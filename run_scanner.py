import os
import json
import time
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from agents.snapshot_collectors import collect_snapshot

from agents.prompts import DataManagementPrompts, AnalyticsReadinessPrompts
REGISTRY = {
    "check_schema_consistency": {"depends_on": [], "category": "Development Maturity"},
    "evaluate_data_freshness": {"depends_on": [], "category": "Development Maturity"},
    "evaluate_governance_compliance": {"depends_on": [], "category": "Development Maturity"},
    "evaluate_data_lineage": {"depends_on": [], "category": "Development Maturity"},
    "evaluate_metadata_coverage": {"depends_on": [], "category": "Innovation Pipeline"},
    "evaluate_sensitive_tagging": {"depends_on": [], "category": "Development Maturity"},
    "evaluate_duplication": {"depends_on": [], "category": "Development Maturity"},
    "evaluate_backup_recovery": {"depends_on": [], "category": "Development Maturity"},
    "evaluate_security_config": {"depends_on": [], "category": "Development Maturity"},
    "evaluate_resource_utilization": {"depends_on": [], "category": "Innovation Pipeline"},
    "assess_query_performance": {"depends_on": [], "category": "Innovation Pipeline"},
    # depend on the above (must run later)
    "evaluate_data_quality": {"depends_on": ["check_schema_consistency", "evaluate_data_freshness"], "category": "Development Maturity"},
    "compute_pipeline_success_rate": {"depends_on": ["evaluate_data_lineage"], "category": "Innovation Pipeline"},
    "compute_pipeline_latency_throughput": {"depends_on": ["evaluate_data_lineage"], "category": "Innovation Pipeline"},
    "compute_analytics_adoption": {"depends_on": ["evaluate_metadata_coverage","check_schema_consistency","evaluate_data_freshness"], "category": "Innovation Pipeline"},
}

FALLBACK_JSON_PROMPT_TEMPLATE = (
    "You are a precise evaluator. Given the input JSON after this line, return valid JSON ONLY with keys:\n"
    "  - score: integer between 1 and 5 (1 worst, 5 best)\n"
    "  - rationale: short string explaining the score\n"
    "  - gap: a short list (at most 5) of specific improvement items\n"
    "Respond with a single JSON object and nothing else.\n"
    "Input:\n{input}\n"
)

PROMPT_MAPPING = {
    "check_schema_consistency": (DataManagementPrompts, "get_schema_consistency_prompt"),
    "evaluate_data_freshness": (DataManagementPrompts, "get_data_freshness_prompt"),
    "evaluate_data_quality": (DataManagementPrompts, "get_data_quality_prompt"),
    "evaluate_governance_compliance": (DataManagementPrompts, "get_governance_compliance_prompt"),
    "evaluate_data_lineage": (DataManagementPrompts, "get_data_lineage_prompt"),
    "evaluate_metadata_coverage": (DataManagementPrompts, "get_metadata_coverage_prompt"),
    "evaluate_sensitive_tagging": (DataManagementPrompts, "get_sensitive_tagging_prompt"),
    "evaluate_duplication": (DataManagementPrompts, "get_duplication_prompt"),
    "evaluate_backup_recovery": (DataManagementPrompts, "get_backup_recovery_prompt"),
    "evaluate_security_config": (DataManagementPrompts, "get_security_config_prompt"),
    "compute_pipeline_success_rate": (AnalyticsReadinessPrompts, "get_pipeline_success_rate_prompt"),
    "compute_pipeline_latency_throughput": (AnalyticsReadinessPrompts, "get_pipeline_latency_throughput_prompt"),
    "evaluate_resource_utilization": (AnalyticsReadinessPrompts, "get_resource_utilization_prompt"),
    "assess_query_performance": (AnalyticsReadinessPrompts, "get_query_performance_prompt"),
    "compute_analytics_adoption": (AnalyticsReadinessPrompts, "get_analytics_adoption_prompt"),
}

class MVPDataPlatformScanner:
    def __init__(self, api_key: str = None, out_dir: str = "runs_mvp_scanner"):
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment or .env file")
        self.client = OpenAI(api_key=self.api_key)
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _build_prompt_for(self, metric: str, input_obj: Any) -> str:
        mapping = PROMPT_MAPPING.get(metric)
        task_input_json = json.dumps(input_obj, ensure_ascii=False)

        if mapping:
            builder_class, method_name = mapping
            builder_method = getattr(builder_class, method_name, None)
            if builder_method is None:
                return FALLBACK_JSON_PROMPT_TEMPLATE.format(input=task_input_json)
            try:
                prompt_text = builder_method(task_input_json)
            except Exception as e:
                print(f"[WARNING] prompt builder {builder_class.__name__}.{method_name} failed: {e}")
                prompt_text = FALLBACK_JSON_PROMPT_TEMPLATE.format(input=task_input_json)
            return prompt_text
        else:
            return FALLBACK_JSON_PROMPT_TEMPLATE.format(input=task_input_json)

    def _llm_evaluate(self, prompt: str, metric_name: str) -> Dict[str, Any]:
        # DEBUG: print the exact input sent to the LLM for this metric
        #print(f"[LLM INPUT] metric={metric_name} -- prompt start: \n {prompt} \n --- END PROMPT ---")

        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a structured evaluator. Always return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        raw = resp.choices[0].message.content.strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            print(f"DEBUG RAW for metric {metric_name}: \n {raw} \n --- END RAW ---")
            raise

        score = parsed.get("score")
        try:
            score = int(score)
        except Exception:
            raise ValueError(f"Metric {metric_name} returned invalid score: {score}")

        score = max(1, min(5, score))
        parsed["score"] = score

        gap = parsed.get("gap") or []
        if not isinstance(gap, list):
            gap = [str(gap)]
        parsed["gap"] = [str(g)[:200] for g in gap[:5]]
        parsed["rationale"] = str(parsed.get("rationale") or "No rationale provided")[:500]
        return parsed

    def _metric_input_for(self, metric: str, ctx: Dict[str, Any]) -> Any:
        """
        Build the input object for a metric.

        Behavior:
        - Construct the "base" input exactly as before (using the original snapshot keys).
        - If the caller provided `_prev_results` in `ctx` (a dict mapping metric->result), and the
          current metric declares dependencies in REGISTRY, then include those dependency outputs
          alongside the original input under the key `dependency_results`.

        This ensures dependent metrics receive both the original data they expect AND the JSON
        outputs produced by the metrics they depend on.
        """
        m = metric
        # base input (same as before)
        if m == "check_schema_consistency":
            base = {"baseline": ctx.get("baseline_schema"), "actual": ctx.get("table_schemas")}
        elif m == "evaluate_data_freshness":
            base = ctx.get("table_metadata")
        elif m == "evaluate_data_quality":
            base = ctx.get("data_quality_report")
        elif m == "evaluate_governance_compliance":
            base = ctx.get("access_logs")
        elif m == "evaluate_data_lineage":
            base = ctx.get("lineage")
        elif m == "evaluate_metadata_coverage":
            base = ctx.get("metadata")
        elif m == "evaluate_sensitive_tagging":
            base = ctx.get("tagging")
        elif m == "evaluate_duplication":
            base = ctx.get("duplication")
        elif m == "evaluate_backup_recovery":
            base = ctx.get("backup")
        elif m == "evaluate_security_config":
            base = ctx.get("security")
        elif m == "evaluate_resource_utilization":
            base = ctx.get("resource_usage")
        elif m == "assess_query_performance":
            base = ctx.get("query_logs")
        elif m == "compute_pipeline_success_rate":
            base = ctx.get("pipeline_runs")
        elif m == "compute_pipeline_latency_throughput":
            base = ctx.get("pipeline_metrics")
        elif m == "compute_analytics_adoption":
            base = ctx.get("user_activity")
        else:
            base = ctx

        dep_results = {}
        all_prev = ctx.get("_prev_results") or {}
        declared_deps = REGISTRY.get(m, {}).get("depends_on", [])
        for d in declared_deps:
            if d in all_prev:
                dep_results[d] = all_prev[d]

        if dep_results:
            if isinstance(base, dict):
                result = dict(base)
                if "dependency_results" in result:
                    result.setdefault("_dependency_results", {})
                    result["_dependency_results"].update(dep_results)
                else:
                    result["dependency_results"] = dep_results
                return result
            else:
                return {"input": base, "dependency_results": dep_results}

        return base

    def _call_metric(self, metric: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        input_obj = self._metric_input_for(metric, ctx)
        prompt = self._build_prompt_for(metric, input_obj)
        result = self._llm_evaluate(prompt, metric)
        return result

    def run(self) -> Dict[str, Any]:
        """
        Orchestrate metric execution.

        - Run all level0 (no-dependency) metrics in parallel.
        - Then run all dependent metrics (level1+) in parallel **but** pass each metric only the
          outputs produced by its declared dependencies (not the whole results map). This ensures
          each metric receives a compact `_prev_results` object containing just the dependency
          outputs it needs.
        """
        ctx = collect_snapshot()
        level0 = [m for m, meta in REGISTRY.items() if not meta["depends_on"]]
        level1 = [m for m, meta in REGISTRY.items() if meta["depends_on"]]

        results = {}

        # --- Run level0 in parallel ---
        print("Running level0 metrics in parallel:", level0)
        with ThreadPoolExecutor(max_workers=min(8, len(level0) or 1)) as ex:
            futures = {ex.submit(self._call_metric, m, ctx): m for m in level0}
            for fut in as_completed(futures):
                m = futures[fut]
                try:
                    results[m] = fut.result()
                    print(f"Completed {m} -> score {results[m]['score']}")
                except Exception as e:
                    print(f"Metric {m} failed: {e}")
                    results[m] = {"error": str(e)}

        # --- Prepare and run level1 in parallel, giving each metric only its dependency outputs ---
        print("Running level1 metrics in parallel (each receives only its dependencies' outputs):", level1)
        with ThreadPoolExecutor(max_workers=min(8, len(level1) or 1)) as ex:
            futures = {}
            for m in level1:
                deps = REGISTRY[m]["depends_on"]
                # only keep dependency outputs that completed successfully
                available_deps = [d for d in deps if d in results and "score" in results.get(d, {})]
                missing = [d for d in deps if d not in results]
                if missing:
                    print(f"Skipping {m} because missing deps: {missing}")
                    continue

                # build a compact _prev_results that contains only the dependency outputs
                prev_results_subset = {d: results[d] for d in available_deps}

                # include the metric's own existing result if present (rare), so the metric can use
                # prior output as part of its context. This follows your request "run on its own
                # output along with the outputs generated by its level 0 dependency".
                if m in results:
                    prev_results_subset[m] = results[m]

                per_metric_ctx = {**ctx, "_prev_results": prev_results_subset}

                futures[ex.submit(self._call_metric, m, per_metric_ctx)] = m

            for fut in as_completed(futures):
                m = futures[fut]
                try:
                    results[m] = fut.result()
                    print(f"Completed {m} -> score {results[m]['score']}")
                except Exception as e:
                    print(f"Metric {m} failed: {e}")
                    results[m] = {"error": str(e)}

        aggregates = self._aggregate(results)

        artifact = {
            "registry": REGISTRY,
            "context_keys": list(ctx.keys()),
            "results": results,
            "aggregates": aggregates,
        }

        fname = self.out_dir / f"run_{int(time.time())}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(artifact, f, ensure_ascii=False, indent=2)

        print(f"Run persisted to {fname}")
        return artifact

    def _aggregate(self, results: Dict[str, Any]) -> Dict[str, Any]:
        category_sums: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        for m, meta in REGISTRY.items():
            cat = meta.get("category", "uncategorized")
            r = results.get(m)
            if not r or "score" not in r:
                continue
            category_sums.setdefault(cat, 0.0)
            counts.setdefault(cat, 0)
            category_sums[cat] += float(r["score"])
            counts[cat] += 1

        category_avgs: Dict[str, float] = {}
        for cat in list(category_sums.keys()):
            if counts.get(cat):
                category_avgs[cat] = round(category_sums[cat] / counts[cat], 2)
            else:
                category_avgs[cat] = None

        weights = {"Development Maturity": 0.6, "Innovation Pipeline": 0.4}
        overall = 0.0
        total_weight = 0.0
        for cat, avg in category_avgs.items():
            if avg is None:
                continue
            w = weights.get(cat, 0.0)
            overall += avg * w
            total_weight += w

        overall_normalized = round(overall / total_weight, 2) if total_weight else None
        return {"per_category_1to5": category_avgs, "overall_score_1to5": overall_normalized}


if __name__ == "__main__":
    scanner = MVPDataPlatformScanner()
    artifact = scanner.run()
    print(json.dumps({"summary": artifact["aggregates"]}, indent=2))
