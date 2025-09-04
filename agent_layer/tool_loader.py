# agent_layer/tool_loader.py
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict

from dotenv import load_dotenv
load_dotenv()

# Ensure repo root importable (same pattern as BI tracker)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# === Import your existing micro-agents (unchanged) ===
from data_collection_agents.dev_env_scanner_agent.code_quality.cyclomatic_complexity import CyclomaticComplexityAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.code_quality.maintainability_index import MaintainabilityAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.code_quality.docstring_coverage import DocstringCoverageAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.code_quality.nested_loops import NestedLoopsAgent # noqa: E402

from data_collection_agents.dev_env_scanner_agent.file_system.ci_cd import CICDAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.file_system.deployment import DeploymentAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.file_system.environment_config import EnvironmentConfigAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.file_system.experiment_detection import ExperimentDetectionAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.file_system.project_structure import ProjectStructureAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.file_system.test_detection import TestDetectionAgent # noqa: E402

from data_collection_agents.dev_env_scanner_agent.infrastructure.parallel_patterns import ParallelPatternsAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.infrastructure.data_pipeline import DataPipelineAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.infrastructure.feature_engineering import FeatureEngineeringAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.infrastructure.model_export import ModelExportAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.infrastructure.inference_endpoint import InferenceEndpointAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.infrastructure.security_hygiene import SecurityAgent # noqa: E402

from data_collection_agents.dev_env_scanner_agent.ml_framework.data_validation import DataValidationAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.ml_framework.experiment_tracking import ExperimentTrackingAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.ml_framework.hyperparameter_optimization import HyperparameterOptimizationAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.ml_framework.ml_framework_agent import MLFrameworkAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.ml_framework.model_evaluation import ModelEvaluationAgent # noqa: E402
from data_collection_agents.dev_env_scanner_agent.ml_framework.model_training import ModelTrainingAgent # noqa: E402
 

# ---- shared LLM config (singleton-style instances) ----
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_TEMP  = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))

# code quality
_cc  = CyclomaticComplexityAgent(_MODEL, _TEMP)
_mi  = MaintainabilityAgent(_MODEL, _TEMP)
_doc = DocstringCoverageAgent(_MODEL, _TEMP)
_nl  = NestedLoopsAgent(_MODEL, _TEMP)

# infra
_par = ParallelPatternsAgent(_MODEL, _TEMP)
_dp  = DataPipelineAgent(_MODEL, _TEMP)
_fe  = FeatureEngineeringAgent(_MODEL, _TEMP)
_exp = ModelExportAgent(_MODEL, _TEMP)
_inf = InferenceEndpointAgent(_MODEL, _TEMP)
_sec = SecurityAgent(_MODEL, _TEMP)

# ml
_fw  = MLFrameworkAgent(_MODEL, _TEMP)
_dv  = DataValidationAgent(_MODEL, _TEMP)
_trk = ExperimentTrackingAgent(_MODEL, _TEMP)
_hpo = HyperparameterOptimizationAgent(_MODEL, _TEMP)
_trn = ModelTrainingAgent(_MODEL, _TEMP)
_eval= ModelEvaluationAgent(_MODEL, _TEMP)

# fs detectors (non-LLM-band originally) — we will wrap into band JSON
_tests = TestDetectionAgent(_MODEL, _TEMP)
_env   = EnvironmentConfigAgent(_MODEL, _TEMP)
_ci    = CICDAgent(_MODEL, _TEMP)
_dep   = DeploymentAgent(_MODEL, _TEMP)
_expd  = ExperimentDetectionAgent(_MODEL, _TEMP)
_proj  = ProjectStructureAgent(_MODEL, _TEMP)


# ---- helpers (same spirit as BI tool_loader) ----
def _clamp_band(v: Any) -> int:
    try:
        return max(1, min(5, int(v)))
    except Exception:
        return 3

def _sanitize(out: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
    out = dict(out or {})
    out["metric_id"] = metric_id
    # accept either 'band' or legacy 'score'
    out["band"] = _clamp_band(out.get("band", out.get("score", 3)))
    out.setdefault("rationale", "Limited evidence; using conservative band.")
    out.setdefault("gaps", [])
    out.setdefault("flags", [])
    out["rationale"] = str(out["rationale"])[:600]
    out["gaps"] = [str(g)[:280] for g in (out.get("gaps") or [])][:6]
    out["flags"] = [str(f)[:120] for f in (out.get("flags") or [])][:10]
    out["score"] = out["band"]
    return out


# ---- deterministic wrappers that adapt inputs from `snapshot` ----
def _code_snaps(snapshot):   return snapshot.get("code_snippets", []) or []
def _file_paths(snapshot):   return snapshot.get("file_paths", []) or []


# ---- FS heuristic -> band mapping (no LLM call here) ----
def _band_tests(res: Dict[str, Any]) -> Dict[str, Any]:
    c = int(res.get("test_file_count", 0))
    cov = float(res.get("test_coverage_estimate", 0.0))
    qual = float(res.get("testing_quality", 0.0))
    has_rep = bool(res.get("has_test_coverage_report", False))

    # simple joint scoring
    score = 1
    if c == 0:
        score = 1
    elif cov >= 0.8 and qual >= 0.8 and has_rep:
        score = 5
    elif cov >= 0.65 and qual >= 0.65:
        score = 4
    elif cov >= 0.45 or qual >= 0.5:
        score = 3
    else:
        score = 2

    return {
        "band": score,
        "rationale": f"tests={c}, est_cov={cov:.2f}, quality={qual:.2f}, coverage_report={has_rep}",
        "flags": [],
        "gaps": ([] if score >= 4 else ["Increase coverage and add coverage report"]),
    }

def _band_env(res: Dict[str, Any]) -> Dict[str, Any]:
    q = float(res.get("dependency_management_quality", 0.0))
    c = float(res.get("environment_consistency", 0.0))
    has_any = any(res.get(k, False) for k in ["has_requirements","has_pipfile","has_env_yml","has_pyproject_toml","has_setup_py"])
    score = 1
    if has_any and q >= 0.85 and c >= 0.85: score = 5
    elif has_any and q >= 0.70 and c >= 0.70: score = 4
    elif has_any and (q >= 0.5 or c >= 0.5): score = 3
    elif has_any: score = 2
    else: score = 1
    return {
        "band": score,
        "rationale": f"dep_quality={q:.2f}, env_consistency={c:.2f}, has_any={has_any}",
        "flags": [],
        "gaps": ([] if score >= 4 else ["Add/normalize dependency files and lock versions"]),
    }

def _band_ci(res: Dict[str, Any]) -> Dict[str, Any]:
    wf = int(res.get("ci_workflow_count", 0))
    q  = float(res.get("ci_quality", 0.0))
    da = float(res.get("deployment_automation", 0.0))
    score = 1
    if wf > 0 and q >= 0.85 and da >= 0.7: score = 5
    elif wf > 0 and q >= 0.7: score = 4
    elif wf > 0: score = 3
    elif any(res.get(f, False) for f in ["has_github_actions","has_gitlab_ci","has_jenkins"]): score = 2
    else: score = 1
    return {
        "band": score,
        "rationale": f"workflows={wf}, quality={q:.2f}, deploy_auto={da:.2f}",
        "flags": [],
        "gaps": ([] if score >= 4 else ["Add CI workflows and enforce checks"]),
    }

def _band_deploy(res: Dict[str, Any]) -> Dict[str, Any]:
    cnt = int(res.get("deploy_script_count", 0))
    qa  = float(res.get("deployment_automation", 0.0))
    qq  = float(res.get("deployment_quality", 0.0))
    score = 1
    if cnt > 0 and qa >= 0.8 and qq >= 0.8: score = 5
    elif cnt > 0 and (qa >= 0.65 or qq >= 0.65): score = 4
    elif cnt > 0: score = 3
    else: score = 1
    return {
        "band": score,
        "rationale": f"deploy_files={cnt}, automation={qa:.2f}, quality={qq:.2f}",
        "flags": [],
        "gaps": ([] if score >= 4 else ["Introduce automated deployment with rollout/rollback"]),
    }

def _band_experiments(res: Dict[str, Any]) -> Dict[str, Any]:
    cnt = int(res.get("experiment_folder_count", 0))
    mg  = float(res.get("experiment_management", 0.0))
    score = 1 if cnt == 0 else (5 if mg >= 0.85 else 4 if mg >= 0.7 else 3 if mg >= 0.5 else 2)
    return {
        "band": score,
        "rationale": f"experiment_dirs={cnt}, management={mg:.2f}",
        "flags": [],
        "gaps": ([] if score >= 4 else ["Standardize experiment directory & reproducibility"]),
    }

def _band_project_structure(res: Dict[str, Any]) -> Dict[str, Any]:
    s  = float(res.get("structure_quality", 0.0))
    d  = float(res.get("documentation_quality", 0.0))
    bp = float(res.get("best_practices_adherence", 0.0))
    score = 5 if min(s, d, bp) >= 0.85 else 4 if min(s, d, bp) >= 0.70 else 3 if min(s, d, bp) >= 0.50 else 2 if max(s, d, bp) > 0 else 1
    return {
        "band": score,
        "rationale": f"struct={s:.2f}, docs={d:.2f}, best_practices={bp:.2f}",
        "flags": [],
        "gaps": ([] if score >= 4 else ["Improve top-level layout and docs (README, CONTRIBUTING)"]),
    }


# ---- loader (metric_id -> callable(snapshot)-> JSON) ----
def load_tool(metric_id: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def _run(_mid: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        cs = _code_snaps(snapshot)
        fp = _file_paths(snapshot)

        # --- Code quality (LLM JSON already) ---
        if _mid == "code.cyclomatic_complexity_band":
            return _sanitize(_cc.evaluate(cs), _mid)
        if _mid == "code.maintainability_band":
            return _sanitize(_mi.evaluate(cs), _mid)
        if _mid == "code.docstring_coverage_band":
            return _sanitize(_doc.evaluate(cs), _mid)
        if _mid == "code.nested_loops_band":
            return _sanitize(_nl.evaluate(cs), _mid)

        # --- Infra (LLM JSON already) ---
        if _mid == "infra.parallel_patterns":
            return _sanitize(_par.evaluate(cs), _mid)
        if _mid == "infra.data_pipeline":
            return _sanitize(_dp.evaluate(cs), _mid)
        if _mid == "infra.feature_engineering":
            return _sanitize(_fe.evaluate(cs), _mid)
        if _mid == "infra.model_export":
            return _sanitize(_exp.evaluate(cs), _mid)
        if _mid == "infra.inference_endpoint":
            return _sanitize(_inf.evaluate(cs), _mid)
        if _mid == "infra.security_hygiene":
            return _sanitize(_sec.evaluate(cs), _mid)

        # --- ML (LLM JSON already) ---
        if _mid == "ml.framework_maturity":
            return _sanitize(_fw.evaluate(cs), _mid)
        if _mid == "ml.data_validation":
            return _sanitize(_dv.evaluate(cs), _mid)
        if _mid == "ml.experiment_tracking":
            return _sanitize(_trk.evaluate(cs), _mid)
        if _mid == "ml.hpo_practice":
            return _sanitize(_hpo.evaluate(cs), _mid)
        if _mid == "ml.training_practice":
            return _sanitize(_trn.evaluate(cs), _mid)
        if _mid == "ml.evaluation_practice":
            return _sanitize(_eval.evaluate(cs), _mid)

        # --- File-system (wrapped into bands deterministically) ---
        if _mid == "fs.tests_practice":
            return _sanitize(_band_tests(_tests.evaluate(cs)), _mid)
        if _mid == "fs.env_config_maturity":
            return _sanitize(_band_env(_env.evaluate(fp)), _mid)
        if _mid == "fs.ci_cd_maturity":
            return _sanitize(_band_ci(_ci.evaluate(fp)), _mid)
        if _mid == "fs.deployment_maturity":
            return _sanitize(_band_deploy(_dep.evaluate(fp)), _mid)
        if _mid == "fs.experiment_org":
            return _sanitize(_band_experiments(_expd.evaluate(fp)), _mid)
        if _mid == "fs.project_structure":
            return _sanitize(_band_project_structure(_proj.evaluate(fp)), _mid)

        # Fallback
        return _sanitize({"band": 3, "rationale": "Unknown metric_id."}, _mid)

    return lambda snapshot: _run(metric_id, snapshot)