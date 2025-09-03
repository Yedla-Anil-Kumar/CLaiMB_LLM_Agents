import os
import json
import time
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed


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
    "compute_analytics_adoption": {"depends_on": ["evaluate_metadata_coverage", "evaluate_data_quality"], "category": "Innovation Pipeline"},
}

# Fallback generic prompt (only used if a metric is not in PROMPT_MAPPING)
FALLBACK_JSON_PROMPT_TEMPLATE = (
    "You are a precise evaluator. Given the input JSON after this line, return valid JSON ONLY with keys:\n"
    "  - score: integer between 1 and 5 (1 worst, 5 best)\n"
    "  - rationale: short string explaining the score\n"
    "  - gap: a short list (at most 5) of specific improvement items\n"
    "Respond with a single JSON object and nothing else.\n"
    "Input:\n{input}\n"
)

# ----------------------------------------------------------------------------
# Map each metric name to the prompt builder class and method name in prompts.py
# The builder method must accept a single JSON string argument and return the prompt text.
# ----------------------------------------------------------------------------
PROMPT_MAPPING = {
    # DataManagementPrompts
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
    # AnalyticsReadinessPrompts
    "compute_pipeline_success_rate": (AnalyticsReadinessPrompts, "get_pipeline_success_rate_prompt"),
    "compute_pipeline_latency_throughput": (AnalyticsReadinessPrompts, "get_pipeline_latency_throughput_prompt"),
    "evaluate_resource_utilization": (AnalyticsReadinessPrompts, "get_resource_utilization_prompt"),
    "assess_query_performance": (AnalyticsReadinessPrompts, "get_query_performance_prompt"),
    "compute_analytics_adoption": (AnalyticsReadinessPrompts, "get_analytics_adoption_prompt"),
    # pipeline_runs/metrics mapping already covered above
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

    # -------------------------- Snapshot loader (delegates) -------------------
    def collect_snapshot(self) -> Dict[str, Any]:
        # ensure the collector module path matches your project layout
        from agents.snapshot_collectors import collect_snapshot as external_collect
        return external_collect()

    # -------------------------- Prompt builder -------------------------------
    def _build_prompt_for(self, metric: str, input_obj: Any) -> str:
        """
        Build a prompt string for the metric using your prompt builders.
        The builders expected signature: builder_method(json_string) -> prompt_string
        """
        mapping = PROMPT_MAPPING.get(metric)
        # prepare a compact JSON string for the builder
        task_input_json = json.dumps(input_obj, ensure_ascii=False)

        if mapping:
            builder_class, method_name = mapping
            builder_method = getattr(builder_class, method_name, None)
            if builder_method is None:
                # fallback to generic template
                return FALLBACK_JSON_PROMPT_TEMPLATE.format(input=task_input_json)
            # call the builder — if it's a @staticmethod or function, this will work
            try:
                prompt_text = builder_method(task_input_json)
            except Exception as e:
                # defensive fallback if the builder fails
                print(f"[WARNING] prompt builder {builder_class.__name__}.{method_name} failed: {e}")
                prompt_text = FALLBACK_JSON_PROMPT_TEMPLATE.format(input=task_input_json)
            return prompt_text
        else:
            # fallback generic prompt
            return FALLBACK_JSON_PROMPT_TEMPLATE.format(input=task_input_json)

    # -------------------------- LLM call + validation ------------------------
    def _llm_evaluate(self, prompt: str, metric_name: str) -> Dict[str, Any]:
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
            print(f"DEBUG RAW for metric {metric_name}:\n{raw}\n--- END RAW ---")
            raise

        # Minimal validation + normalization
        score = parsed.get("score")
        try:
            score = int(score)
        except Exception:
            raise ValueError(f"Metric {metric_name} returned invalid score: {score}")

        score = max(1, min(5, score))
        parsed["score"] = score
        parsed["score_0to100"] = round((score - 1) / 4 * 100)

        gap = parsed.get("gap") or []
        if not isinstance(gap, list):
            gap = [str(gap)]
        parsed["gap"] = [str(g)[:200] for g in gap[:5]]
        parsed["rationale"] = str(parsed.get("rationale") or "No rationale provided")[:500]
        return parsed

    # -------------------------- Metric wrappers ------------------------------
    def _metric_input_for(self, metric: str, ctx: Dict[str, Any]) -> Any:
        m = metric
        if m == "check_schema_consistency":
            return {"baseline": ctx.get("baseline_schema"), "actual": ctx.get("table_schemas")}
        if m == "evaluate_data_freshness":
            return ctx.get("table_metadata")
        if m == "evaluate_data_quality":
            return ctx.get("data_quality_report")
        if m == "evaluate_governance_compliance":
            return ctx.get("access_logs")
        if m == "evaluate_data_lineage":
            return ctx.get("lineage")
        if m == "evaluate_metadata_coverage":
            return ctx.get("metadata")
        if m == "evaluate_sensitive_tagging":
            return ctx.get("tagging")
        if m == "evaluate_duplication":
            return ctx.get("duplication")
        if m == "evaluate_backup_recovery":
            return ctx.get("backup")
        if m == "evaluate_security_config":
            return ctx.get("security")
        if m == "evaluate_resource_utilization":
            return ctx.get("resource_usage")
        if m == "assess_query_performance":
            return ctx.get("query_logs")
        if m == "compute_pipeline_success_rate":
            return ctx.get("pipeline_runs")
        if m == "compute_pipeline_latency_throughput":
            return ctx.get("pipeline_metrics")
        if m == "compute_analytics_adoption":
            return ctx.get("user_activity")
        return ctx

    def _call_metric(self, metric: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        input_obj = self._metric_input_for(metric, ctx)
        prompt = self._build_prompt_for(metric, input_obj)
        result = self._llm_evaluate(prompt, metric)
        return result

    # -------------------------- Orchestration -------------------------------
    def run(self) -> Dict[str, Any]:
        ctx = self.collect_snapshot()
        level0 = [m for m, meta in REGISTRY.items() if not meta["depends_on"]]
        level1 = [m for m, meta in REGISTRY.items() if meta["depends_on"]]

        results = {}

        print("Running level0 metrics in parallel:", level0)
        with ThreadPoolExecutor(max_workers=min(8, len(level0) or 1)) as ex:
            futures = {ex.submit(self._call_metric, m, ctx): m for m in level0}
            for fut in as_completed(futures):
                m = futures[fut]
                try:
                    results[m] = fut.result()
                    print(f"Completed {m} -> score {results[m]['score']} (0-100={results[m]['score_0to100']})")
                except Exception as e:
                    print(f"Metric {m} failed: {e}")
                    results[m] = {"error": str(e)}

        print("Running level1 metrics sequentially:", level1)
        for m in level1:
            deps = REGISTRY[m]["depends_on"]
            missing = [d for d in deps if d not in results]
            if missing:
                print(f"Skipping {m} because missing deps: {missing}")
                continue
            try:
                results[m] = self._call_metric(m, {**ctx, "_prev_results": results})
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

    # -------------------------- Aggregation -------------------------------
    def _aggregate(self, results: Dict[str, Any]) -> Dict[str, Any]:
        category_scores = {}
        counts = {}
        for m, meta in REGISTRY.items():
            cat = meta.get("category", "uncategorized")
            r = results.get(m)
            if not r or "score_0to100" not in r:
                continue
            category_scores.setdefault(cat, 0)
            counts.setdefault(cat, 0)
            category_scores[cat] += r["score_0to100"]
            counts[cat] += 1

        for cat in list(category_scores.keys()):
            category_scores[cat] = round(category_scores[cat] / counts[cat]) if counts[cat] else None

        weights = {"Development Maturity": 0.6, "Innovation Pipeline": 0.4}
        overall = 0.0
        total_weight = 0.0
        for cat, score in category_scores.items():
            w = weights.get(cat, 0.0)
            if score is None:
                continue
            overall += score * w
            total_weight += w

        overall_normalized = round(overall / total_weight) if total_weight else None
        return {"per_category": category_scores, "overall_score_0to100": overall_normalized}


if __name__ == "__main__":
    scanner = MVPDataPlatformScanner()
    artifact = scanner.run()
    print(json.dumps({"summary": artifact["aggregates"]}, indent=2))
