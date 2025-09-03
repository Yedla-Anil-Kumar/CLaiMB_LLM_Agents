# agent_layer/tool_loader_mlops.py
from __future__ import annotations
import os, sys
from pathlib import Path
from typing import Any, Callable, Dict
from dotenv import load_dotenv

load_dotenv()

# ensure repo root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_collection_agents.ml_ops_agent.llm_engine import MLOpsLLM  # noqa: E402
from agent_layer.registry_mlops import BAND_TO_SCORE  # noqa: E402

_llm = MLOpsLLM(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.0")),
)

NUM_TO_LETTER = {5: "A", 4: "B", 3: "C", 2: "D", 1: "E"}

def _sanitize(out: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
    out = dict(out or {})
    band_num = int(out.get("band", 3))
    band_num = max(1, min(5, band_num))
    band_letter = NUM_TO_LETTER[band_num]
    score = BAND_TO_SCORE[band_letter]

    out["metric_id"] = metric_id
    out["band"] = band_letter               # mentor wants A..E
    out["score_0to100"] = score
    out.setdefault("rationale", "No rationale.")
    out.setdefault("gaps", [])
    out.setdefault("flags", [])
    # trim noisy fields
    out["rationale"] = str(out["rationale"])[:600]
    out["gaps"] = [str(g)[:280] for g in out.get("gaps", [])][:6]
    out["flags"] = [str(f)[:80] for f in out.get("flags", [])][:10]
    return out

def load_tool(metric_id: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def _run(snapshot: Dict[str, Any]) -> Dict[str, Any]:
        s = snapshot or {}

        # ----- MLflow -----
        if metric_id == "mlflow.experiment_completeness_band":
            return _sanitize(_llm.grade_mlflow_experiment_completeness({"evidence": s.get("mlflow_experiment_completeness", {})}), metric_id)
        if metric_id == "mlflow.lineage_coverage_band":
            return _sanitize(_llm.grade_mlflow_lineage_coverage({"evidence": s.get("mlflow_lineage_coverage", {})}), metric_id)
        if metric_id == "mlflow.experiment_velocity_band":
            return _sanitize(_llm.grade_mlflow_experiment_velocity({"evidence": s.get("mlflow_best_run_trend", {})}), metric_id)
        if metric_id == "mlflow.registry_hygiene_band":
            return _sanitize(_llm.grade_mlflow_registry_governance({"evidence": s.get("mlflow_registry_hygiene", {})}), metric_id)
        if metric_id == "mlflow.validation_artifacts_band":
            return _sanitize(_llm.grade_mlflow_validation_artifacts({"evidence": s.get("mlflow_validation_artifacts", {})}), metric_id)
        if metric_id == "mlflow.reproducibility_band":
            return _sanitize(_llm.grade_mlflow_reproducibility({"evidence": s.get("mlflow_reproducibility", {})}), metric_id)

        # ----- AML -----
        if metric_id == "aml.jobs_flow_band":
            return _sanitize(_llm.grade_aml_jobs_flow({"evidence": s.get("aml_jobs_flow", {})}), metric_id)
        if metric_id == "aml.monitoring_coverage_band":
            return _sanitize(_llm.grade_aml_monitoring_coverage({"evidence": s.get("aml_monitoring_coverage", {})}), metric_id)
        if metric_id == "aml.registry_governance_band":
            return _sanitize(_llm.grade_aml_registry_governance({"evidence": s.get("aml_registry_governance", {})}), metric_id)
        if metric_id == "aml.cost_correlation_band":
            return _sanitize(_llm.grade_aml_cost_correlation({"evidence": s.get("aml_cost_correlation", {})}), metric_id)
        if metric_id == "aml.endpoint_slo_band":
            ev = {"declared_slo": s.get("declared_slo", {}), **(s.get("aml_endpoint_slo", {}) or {})}
            return _sanitize(_llm.grade_aml_endpoint_slo({"evidence": ev}), metric_id)

        # ----- SageMaker -----
        if metric_id == "sm.pipeline_flow_band":
            return _sanitize(_llm.grade_sm_pipeline_flow({"evidence": s.get("sm_pipeline_stats", {})}), metric_id)
        if metric_id == "sm.experiments_lineage_band":
            return _sanitize(_llm.grade_sm_experiments_lineage({"evidence": s.get("sm_experiments_lineage", {})}), metric_id)
        if metric_id == "sm.clarify_coverage_band":
            return _sanitize(_llm.grade_sm_clarify_coverage({"evidence": s.get("sm_clarify_coverage", {})}), metric_id)
        if metric_id == "sm.cost_efficiency_band":
            return _sanitize(_llm.grade_sm_cost_efficiency({"evidence": s.get("sm_cost_efficiency", {})}), metric_id)
        if metric_id == "sm.endpoint_slo_scaling_band":
            return _sanitize(_llm.grade_sm_endpoint_slo_scaling({"evidence": s.get("sm_endpoint_slo_scaling", {})}), metric_id)

        # ----- CI/CD -----
        if metric_id == "cicd.deploy_frequency_band":
            return _sanitize(_llm.grade_cicd_deploy_frequency({"evidence": s.get("cicd_deploy_frequency", {})}), metric_id)
        if metric_id == "cicd.lead_time_band":
            return _sanitize(_llm.grade_cicd_lead_time({"evidence": s.get("cicd_lead_time", {})}), metric_id)
        if metric_id == "cicd.change_failure_rate_band":
            return _sanitize(_llm.grade_cicd_change_failure_rate({"evidence": s.get("cicd_change_failure_rate", {})}), metric_id)
        if metric_id == "cicd.policy_gates_band":
            payload = s.get("cicd_policy_gates", {}) or {
                "required_checks": s.get("policy_required_checks", []),
                "workflow_yaml": "",
                "logs_snippets": [],
            }
            return _sanitize(_llm.check_cicd_policy_gates(payload), metric_id)

        return {"metric_id": metric_id, "band": "C", "score_0to100": 70, "rationale": "Unknown metric."}
    return _run