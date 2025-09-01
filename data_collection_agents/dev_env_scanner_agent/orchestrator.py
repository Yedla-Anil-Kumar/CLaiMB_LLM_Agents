from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, List
import os
from typing import Set
from utils.file_utils import list_source_files, list_all_files

from dotenv import load_dotenv

from dev_env_scanner_agent.code_quality.cyclomatic_complexity import CyclomaticComplexityAgent
from dev_env_scanner_agent.code_quality.maintainability_index import MaintainabilityAgent
from dev_env_scanner_agent.code_quality.docstring_coverage import DocstringCoverageAgent
from dev_env_scanner_agent.code_quality.nested_loops import NestedLoopsAgent

from dev_env_scanner_agent.file_system.ci_cd import CICDAgent
from dev_env_scanner_agent.file_system.deployment import DeploymentAgent
from dev_env_scanner_agent.file_system.environment_config import EnvironmentConfigAgent
from dev_env_scanner_agent.file_system.experiment_detection import ExperimentDetectionAgent
from dev_env_scanner_agent.file_system.project_structure import ProjectStructureAgent
from dev_env_scanner_agent.file_system.test_detection import TestDetectionAgent

from dev_env_scanner_agent.infrastructure.parallel_patterns import ParallelPatternsAgent
from dev_env_scanner_agent.infrastructure.data_pipeline import DataPipelineAgent
from dev_env_scanner_agent.infrastructure.feature_engineering import FeatureEngineeringAgent
from dev_env_scanner_agent.infrastructure.model_export import ModelExportAgent
from dev_env_scanner_agent.infrastructure.inference_endpoint import InferenceEndpointAgent
from dev_env_scanner_agent.infrastructure.security_hygiene import SecurityAgent

from dev_env_scanner_agent.ml_framework.data_validation import DataValidationAgent
from dev_env_scanner_agent.ml_framework.experiment_tracking import ExperimentTrackingAgent
from dev_env_scanner_agent.ml_framework.hyperparameter_optimization import HyperparameterOptimizationAgent
from dev_env_scanner_agent.ml_framework.ml_framework_agent import MLFrameworkAgent
from dev_env_scanner_agent.ml_framework.model_evaluation import ModelEvaluationAgent
from dev_env_scanner_agent.ml_framework.model_training import ModelTrainingAgent

#from utils.aimri_mapping import compute_aimri_summary
from dev_env_scanner_agent.base_agent import BaseMicroAgent
load_dotenv()

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def calculate_scores(signals: Dict[str, Any], num_py_files: int) -> Dict[str, float]:
    # ─── Development Maturity ────────────────────────────────────
    avg_cc = float(signals.get("avg_cyclomatic_complexity", 0.0))
    s_cc = clamp01(1 - (min(avg_cc, 30) / 30) ** 1.5)
    s_mi = clamp01(float(signals.get("avg_maintainability_index", 0.0)))
    s_doc = clamp01(float(signals.get("docstring_coverage", 0.0)))
    tc = int(signals.get("test_file_count", 0))
    s_tests = clamp01(0.3 * min(tc, 10) / 10 + 0.7 * (tc / num_py_files if num_py_files else 0))
    s_ci = 1.0 if int(signals.get("ci_workflow_count", 0)) > 0 else 0.0
    s_cd = 1.0 if int(signals.get("deploy_script_count", 0)) > 0 else 0.0
    env_bits = [
        bool(signals.get("has_requirements", False)),
        bool(signals.get("has_pipfile", False)),
        bool(signals.get("has_env_yml", False)),
    ]
    s_env = sum(env_bits) / len(env_bits) if env_bits else 0.0
    s_sec = 0.0 if bool(signals.get("has_secrets", False)) else 1.0

    w = {"mi": 0.25, "doc": 0.15, "cc": 0.10, "tests": 0.20, "ci": 0.08, "cd": 0.08, "env": 0.05, "sec": 0.05}
    raw = (
        w["mi"] * s_mi
        + w["doc"] * s_doc
        + w["cc"] * s_cc
        + w["tests"] * s_tests
        + w["ci"] * s_ci
        + w["cd"] * s_cd
        + w["env"] * s_env
        + w["sec"] * s_sec
    )
    dev = round(raw * 5, 2)

    # Innovation
    s_exp = 1.0 if bool(signals.get("has_experiments", False)) else 0.0
    track = sum(bool(signals.get(f"uses_{t}", False)) for t in ("mlflow", "wandb", "clearml"))
    s_track = clamp01(track / 3 + (0.5 if track else 0))
    s_hyp = 1.0 if (
        bool(signals.get("has_hyperparam_file", False))
        or bool(signals.get("uses_optuna", False))
        or bool(signals.get("uses_ray_tune", False))
    ) else 0.0
    s_val = 1.0 if any(bool(signals.get(f"uses_{v}", False)) for v in ("great_expectations", "evidently", "pandera")) else 0.0
    s_met = 1.0 if bool(signals.get("uses_metrics_library", False)) else 0.0

    iw = {"exp": 0.25, "track": 0.30, "hparams": 0.20, "valid": 0.15, "metrics": 0.10}
    raw2 = (
        iw["exp"] * s_exp
        + iw["track"] * s_track
        + iw["hparams"] * s_hyp
        + iw["valid"] * s_val
        + iw["metrics"] * s_met
    )
    innov = round(raw2 * 5, 2)

    return {"development_maturity": dev, "innovation_pipeline": innov}


# ---- Budget caps (env-overridable) ----

MAX_FILES_PER_REPO = int(os.getenv("MA_MAX_FILES_PER_REPO", "50"))
MAX_SNIPPET_BYTES = int(os.getenv("MA_MAX_SNIPPET_BYTES", "3000"))
MAX_PATHS_PER_AGENT = int(os.getenv("MA_MAX_PATHS_PER_AGENT", "400"))


class MicroAgentOrchestrator:
    """
    Orchestrates all micro-agents and aggregates per-file LLM evaluations
    into the same signal schema your dev_platform_agent uses.

    IMPORTANT:
    - Calls the LLM for each file individually (per your requirement).
    - Aggregates booleans with OR, counts by summation, and averages
      maintainability/docstring/complexity across files.
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.1):
        self.model = model
        self.temperature = temperature

        # Initialize micro-agents
        self.agents_code = [
            CyclomaticComplexityAgent(model, temperature),
            MaintainabilityAgent(model, temperature),
            DocstringCoverageAgent(model, temperature),
            NestedLoopsAgent(model, temperature),
        ]
        self.agents_ml = [
            MLFrameworkAgent(model, temperature),
            ExperimentTrackingAgent(model, temperature),
            HyperparameterOptimizationAgent(model, temperature),
            DataValidationAgent(model, temperature),
            ModelTrainingAgent(model, temperature),
            ModelEvaluationAgent(model, temperature),
        ]
        self.agents_infra = [
            ParallelPatternsAgent(model, temperature),
            InferenceEndpointAgent(model, temperature),
            ModelExportAgent(model, temperature),
            DataPipelineAgent(model, temperature),
            FeatureEngineeringAgent(model, temperature),
            SecurityAgent(model, temperature),
        ]
        self.agents_fs = [
            TestDetectionAgent(model, temperature),
            EnvironmentConfigAgent(model, temperature),
            CICDAgent(model, temperature),
            DeploymentAgent(model, temperature),
            ExperimentDetectionAgent(model, temperature),
            ProjectStructureAgent(model, temperature),
        ]

    # ---------- public API ----------

    def _collect_raw_outputs(self, snippets: List[str], agents: List[BaseMicroAgent]) -> List[Dict[str, Any]]:
        """Run all given agents on each snippet, return flat list of raw JSON outputs."""
        results = []
        for snippet in snippets:
            for agent in agents:
                res = agent.evaluate([snippet])
                results.append(res)
        return results

    # def analyze_repo(self, repo_path: str) -> Dict[str, Any]:
    #     root = Path(repo_path)

    #     # Per-file contents (source .py only) → sample + trim
    #     all_source = self._get_source_files(repo_path)
    #     picked = self._pick_representative_files(all_source)
    #     source_texts = self._read_files_snippets(picked)

    #     # All file paths (for FS-style agents) → trim per agent later
    #     all_paths = self._get_all_paths(repo_path)

    #     # Aggregate signals across per-file LLM calls
    #     signals: Dict[str, Any] = self._aggregate_code_signals(source_texts)
    #     tests_signals = self.agents_fs[0].evaluate(source_texts)
    #     signals.update(tests_signals)
    #     signals.update(self._aggregate_ml_signals(source_texts))
    #     signals.update(self._aggregate_infra_signals(source_texts))
    #     signals.update(self._aggregate_fs_signals(all_paths))

    #     # Compute scores
    #     scores = self._calculate_scores(signals, len(picked))
    #     aimri = compute_aimri_summary(signals)

    #     return {
    #         "agent": "micro_agent_orchestrator",
    #         "repo": root.name,
    #         # "signals": signals,  # keep commented if you don't want raw signals returned
    #         "scores": scores,
    #         "micro_agent_results": {
    #             "source_files_analyzed": len(picked),
    #             "total_files_analyzed": len(all_source),
    #         },
    #         "aimri_summary": aimri,
    #     }

    def analyze_repo(self, repo_path: str) -> Dict[str, Any]:
        """
        Run all agents, consolidate repeated metric_id entries into a single
        per-metric object, and return a bi_tracker-style JSON:
        {
          "agent": "micro_agent_orchestrator",
          "metric_breakdown": { "<metric_id>": {...}, ... }
        }
        """
        all_source = self._get_source_files(repo_path)
        picked = self._pick_representative_files(all_source)
        source_texts = self._read_files_snippets(picked)
        all_paths = self._get_all_paths(repo_path)

        # Gather raw LLM outputs (many duplicates across files)
        outputs: List[Dict[str, Any]] = []
        outputs.extend(self._collect_raw_outputs(source_texts, self.agents_code))
        outputs.extend(self._collect_raw_outputs(source_texts, self.agents_ml))
        outputs.extend(self._collect_raw_outputs(source_texts, self.agents_infra))
        outputs.extend(self._collect_fs_outputs(all_paths, source_texts))  # FS agents

        # Consolidate to single entry per metric_id
        metric_breakdown = self._consolidate_metrics(outputs)

        return {
            "agent": "micro_agent_orchestrator",
            "metric_breakdown": metric_breakdown,
        }

    # ---------- helpers for raw -> consolidated ----------

    def _collect_raw_outputs(self, snippets: List[str], agents: List[BaseMicroAgent]) -> List[Dict[str, Any]]:
        """Run all given agents on each snippet, return flat list of raw JSON outputs."""
        results: List[Dict[str, Any]] = []
        for snippet in snippets:
            for agent in agents:
                res = agent.evaluate([snippet])
                if isinstance(res, dict):
                    results.append(res)
                elif isinstance(res, list):
                    # Some agents might (rarely) return a list of metrics
                    results.extend([r for r in res if isinstance(r, dict)])
        return results

    def _collect_fs_outputs(self, all_paths: List[str], source_texts: List[str]) -> List[Dict[str, Any]]:
        outputs: List[Dict[str, Any]] = []
        # Tests is based on source snippets
        outputs.append(self.agents_fs[0].evaluate(source_texts))     # TestDetectionAgent
        # The rest are path-based
        outputs.append(self.agents_fs[1].evaluate(all_paths))         # EnvironmentConfigAgent
        outputs.append(self.agents_fs[2].evaluate(all_paths))         # CICDAgent
        outputs.append(self.agents_fs[3].evaluate(all_paths))         # DeploymentAgent
        outputs.append(self.agents_fs[4].evaluate(all_paths))         # ExperimentDetectionAgent
        outputs.append(self.agents_fs[5].evaluate(all_paths))         # ProjectStructureAgent
        # Flatten if any agent returned a list
        flat: List[Dict[str, Any]] = []
        for r in outputs:
            if isinstance(r, dict):
                flat.append(r)
            elif isinstance(r, list):
                flat.extend([x for x in r if isinstance(x, dict)])
        return flat

    def _consolidate_metrics(self, outputs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Many agents run per file, so the same metric_id can appear multiple times.
        We collapse to ONE entry per metric_id using conservative rules:
          - Keep the lowest (worst) band observed.
          - Union unique flags/gaps.
          - Prefer a non-empty rationale; if multiple, keep the longest text.
          - Add `score` mirroring `band` to match your bi_tracker shape.
        """
        consolidated: Dict[str, Dict[str, Any]] = {}

        for obj in outputs:
            if not isinstance(obj, dict):
                continue
            metric_id = obj.get("metric_id")
            if not metric_id:
                # Skip anything that doesn't identify the metric
                continue

            band = obj.get("band", 3)
            try:
                band = max(1, min(5, int(band)))
            except Exception:
                band = 3

            rationale = obj.get("rationale", "")
            flags_in: List[str] = obj.get("flags", []) or []
            gaps_in: List[str] = obj.get("gaps", []) or []

            if metric_id not in consolidated:
                consolidated[metric_id] = {
                    "metric_id": metric_id,
                    "band": band,
                    "rationale": rationale or "",
                    "flags": list(dict.fromkeys([str(f) for f in flags_in])),
                    "gaps": list(dict.fromkeys([str(g) for g in gaps_in])),
                    "score": band,  # mirror band -> score
                }
                continue

            # Merge into existing
            cur = consolidated[metric_id]
            # Keep the worst band (lowest number)
            cur["band"] = min(cur.get("band", band), band)
            # Prefer the longest non-empty rationale
            old_rat = cur.get("rationale", "")
            if rationale and (len(rationale) > len(old_rat)):
                cur["rationale"] = rationale
            # Union flags/gaps preserving order & uniqueness
            def _merge_list(dst: List[str], src: List[str]) -> List[str]:
                seen: Set[str] = set(map(str, dst))
                for x in src:
                    s = str(x)
                    if s not in seen:
                        dst.append(s)
                        seen.add(s)
                return dst
            cur["flags"] = _merge_list(cur.get("flags", []), flags_in)
            cur["gaps"] = _merge_list(cur.get("gaps", []), gaps_in)
            # Keep score in sync with band
            cur["score"] = cur["band"]

        return consolidated

    # ---------- file helpers ----------

    def _get_source_files(self, repo_path: str) -> List[Path]:
        return list(list_source_files(repo_path))

    def _get_all_paths(self, repo_path: str) -> List[str]:
        return list(list_all_files(repo_path))

    def _pick_representative_files(self, paths: List[Path]) -> List[Path]:
        """Prefer src/* and ML/serving/pipeline names, then cap to budget."""
        keywords = (
            "/src/",
            "train",
            "eval",
            "serve",
            "api",
            "pipeline",
            "dag",
            "flow",
            "inference",
        )
        pri = [p for p in paths if any(k in str(p).lower() for k in keywords)]
        # Deduplicate, preserve order
        seen = set()
        dedup: List[Path] = []
        for p in pri + paths:
            if p not in seen:
                seen.add(p)
                dedup.append(p)
        return dedup[:MAX_FILES_PER_REPO]

    @staticmethod
    def _read_files_snippets(paths: Iterable[Path]) -> List[str]:
        """Return head+tail snippets to keep token usage bounded per call."""
        out: List[str] = []
        half = max(1, MAX_SNIPPET_BYTES // 2)
        for p in paths:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            if len(text) <= MAX_SNIPPET_BYTES:
                out.append(text)
            else:
                head = text[:half]
                tail = text[-half:]
                out.append(head + "\n# ...\n" + tail)
        return out

    # ---------- aggregation per category ----------

    def _band_to_score(b: int) -> float:
        # Simple linear map: 1->0.2, 2->0.4, 3->0.6, 4->0.8, 5->1.0
        return max(1, min(5, int(b))) / 5.0

    def _aggregate_code_signals(self, code_snippets: List[str]) -> Dict[str, Any]:
        accum = {
            "avg_maintainability_index": 0.0,  # use band proxy
            "docstring_coverage": 0.0,         # use band proxy
            "avg_cyclomatic_complexity": 0.0,  # derive a proxy complexity from band
            "nested_loop_files": 0,
        }
        n = max(1, len(code_snippets))
        for snippet in code_snippets:
            b_cc = self.agents_code[0].evaluate([snippet])  # complexity band
            b_mi = self.agents_code[1].evaluate([snippet])  # maintainability band
            b_ds = self.agents_code[2].evaluate([snippet])  # docstring band
            b_nl = self.agents_code[3].evaluate([snippet])  # nested loops band

            # map bands to the legacy normalized signals you score on
            accum["avg_maintainability_index"] += max(1, min(5, int(b_mi.get("band", 3)))) / 5.0
            accum["docstring_coverage"]        += max(1, min(5, int(b_ds.get("band", 3)))) / 5.0

            # for complexity your formula expects a small "avg complexity" number (lower is better)
            # pick representative midpoints for each band threshold in your rubric:
            # 5: ≤5, 4: ≤7, 3: ≤10, 2: ≤12, 1: >12
            band_to_complexity_mid = {5: 4.5, 4: 6.0, 3: 9.0, 2: 11.0, 1: 14.0}
            accum["avg_cyclomatic_complexity"] += band_to_complexity_mid.get(int(b_cc.get("band", 3)), 9.0)

            # nested loops "file had problematic nesting?" — use flags or band
            flags = [str(f).lower() for f in b_nl.get("flags", [])]
            has_nested_flag = any("nested" in f or "depth" in f for f in flags)
            # be conservative: count as nested if band ≤3 OR flags indicate nesting
            if int(b_nl.get("band", 3)) <= 3 or has_nested_flag:
                accum["nested_loop_files"] += 1

        # averages
        accum["avg_maintainability_index"] /= n
        accum["docstring_coverage"]        /= n
        accum["avg_cyclomatic_complexity"] /= n
        return accum

    def _aggregate_ml_signals(self, code_snippets: List[str]) -> Dict[str, Any]:
        """
        Sums counts and ORs booleans for ML-related signals, per file.
        """
        out: Dict[str, Any] = {
            "framework_torch": 0,
            "framework_tensorflow": 0,
            "framework_sklearn": 0,
            "framework_keras": 0,
            "framework_xgboost": 0,
            "framework_lightgbm": 0,
            "uses_mlflow": False,
            "uses_wandb": False,
            "uses_clearml": False,
            "has_hyperparam_file": False,
            "uses_optuna": False,
            "uses_ray_tune": False,
            "train_script_count": 0,
            "has_entrypoint_training": False,
            "eval_script_count": 0,
            "uses_metrics_library": False,
            "uses_great_expectations": False,
            "uses_evidently": False,
            "uses_pandera": False,
        }

        for snippet in code_snippets:
            out = self._sum_dict(out, self.agents_ml[0].evaluate([snippet]))
            out = self._or_bools(out, self.agents_ml[1].evaluate([snippet]))
            out = self._or_bools(out, self.agents_ml[2].evaluate([snippet]))
            out = self._or_bools(out, self.agents_ml[3].evaluate([snippet]))

            tr = self.agents_ml[4].evaluate([snippet])
            out["train_script_count"] += int(tr.get("train_script_count", 0))
            out["has_entrypoint_training"] = out["has_entrypoint_training"] or bool(
                tr.get("has_entrypoint_training", False)
            )

            ev = self.agents_ml[5].evaluate([snippet])
            out["eval_script_count"] += int(ev.get("eval_script_count", 0))
            out["uses_metrics_library"] = out["uses_metrics_library"] or bool(
                ev.get("uses_metrics_library", False)
            )

        return out

    def _aggregate_infra_signals(self, code_snippets: List[str]) -> Dict[str, Any]:
        """
        OR booleans and set flags for infra-related signals, per file.
        """
        out: Dict[str, Any] = {
            "uses_threading": False,
            "uses_multiprocessing": False,
            "uses_concurrent": False,
            "uses_fastapi": False,
            "uses_flask": False,
            "uses_streamlit": False,
            "exports_torch_model": False,
            "exports_sklearn_model": False,
            "has_airflow": False,
            "has_prefect": False,
            "has_luigi": False,
            "has_argo": False,
            "has_kedro": False,
            "uses_sklearn_preprocessing": False,
            "uses_featuretools": False,
            "uses_tsfresh": False,
            "has_secrets": False,
        }

        for snippet in code_snippets:
            out = self._or_bools(out, self.agents_infra[0].evaluate([snippet]))
            out = self._or_bools(out, self.agents_infra[1].evaluate([snippet]))
            out = self._or_bools(out, self.agents_infra[2].evaluate([snippet]))
            out = self._or_bools(out, self.agents_infra[3].evaluate([snippet]))
            out = self._or_bools(out, self.agents_infra[4].evaluate([snippet]))
            out = self._or_bools(out, self.agents_infra[5].evaluate([snippet]))

        return out

    def _aggregate_fs_signals(self, all_paths: List[str]) -> Dict[str, Any]:
        """
        Trim path lists per agent to avoid huge prompts and then call once each.
        NOTE: Test detection is handled from source snippets in analyze_repo()
              to avoid empty-input inference; we do NOT call TestDetectionAgent here.
        """
        out: Dict[str, Any] = {
            # (intentionally no test_* keys to avoid clobbering earlier results)
            "has_requirements": False,
            "has_pipfile": False,
            "has_env_yml": False,
            "ci_workflow_count": 0,
            "has_ci": False,
            "deploy_script_count": 0,
            "has_deploy_scripts": False,
            "experiment_folder_count": 0,
            "has_experiments": False,
        }

        # Helper to limit paths
        def cap(lst: List[str]) -> List[str]:
            return lst[:MAX_PATHS_PER_AGENT]

        # Env config
        env_paths = [
            p
            for p in all_paths
            if any(
                name in p.lower()
                for name in (
                    "requirements",
                    "pipfile",
                    "environment.yml",
                    "environment.yaml",
                    "pyproject.toml",
                    "setup.py",
                )
            )
        ]
        out.update(self.agents_fs[1].evaluate(cap(env_paths or all_paths)))

        # CI/CD
        ci_paths = [
            p
            for p in all_paths
            if any(
                tag in p.lower()
                for tag in (
                    ".github/workflows",
                    ".gitlab-ci",
                    "jenkins",
                    ".circleci",
                    "azure-pipelines",
                    "workflow",
                )
            )
        ]
        out.update(self.agents_fs[2].evaluate(cap(ci_paths or all_paths)))

        # Deploy
        dep_paths = [
            p
            for p in all_paths
            if any(
                tag in p.lower()
                for tag in (
                    "deploy",
                    "release",
                    "docker",
                    "docker-compose",
                    "k8s",
                    "kubernetes",
                    "helm",
                    "chart",
                    "deployment.yaml",
                    "service.yaml",
                )
            )
        ]
        out.update(self.agents_fs[3].evaluate(cap(dep_paths or all_paths)))

        # Experiments
        exp_paths = [
            p
            for p in all_paths
            if any(tag in p.lower() for tag in ("experiment", "/exp/", "experiments"))
        ]
        out.update(self.agents_fs[4].evaluate(cap(exp_paths or all_paths)))

        # Project structure (sample paths)
        out.update(self.agents_fs[5].evaluate(cap(all_paths)))

        return out

    # ---------- generic merging helpers ----------

    @staticmethod
    def _or_bools(base: Dict[str, Any], add: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(base)
        for k, v in add.items():
            if isinstance(v, bool) and k in out and isinstance(out[k], bool):
                out[k] = out[k] or v
        return out

    @staticmethod
    def _sum_dict(base: Dict[str, Any], add: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(base)
        for k, v in add.items():
            if (
                isinstance(v, (int, float))
                and k in out
                and isinstance(out[k], (int, float))
            ):
                out[k] = out[k] + v
        return out

    # ---------- scoring ----------

    @staticmethod
    def _calculate_scores(
        signals: Dict[str, Any], num_py_files: int
    ) -> Dict[str, float]:
        return calculate_scores(signals, num_py_files)