# agent_layer/tool_loader_enterprise.py
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Callable, Dict

# Ensure repo root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import your backbone LLM (support common casings/module names)

from data_collection_agents.enterprise_systems_agent.llm_engine import EnterpriseLLM #noqa:E402


from agent_layer.validate import sanitize_metric #noqa:E402

# Singleton LLM
_llm = EnterpriseLLM(model="gpt-4o-mini", temperature=0.0)

def _get_evidence(snapshot: Dict[str, Any], key: str) -> Dict[str, Any]:
    """
    Pull a compact evidence blob for the given input key from snapshot.
    Each key matches EnterpriseInputs fields in your backbone.
    """
    return dict(snapshot.get(key, {}))

def load_tool(fn_id: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns a callable(context) that computes the metric.
    The context is a dict: {"snapshot": <blob>, "results": <dict of prior results>}
    (We only use "snapshot" for MVP. "results" is available if you want to enrich L1/L2 prompts later.)
    """

    def compute(ctx: Dict[str, Any]) -> Dict[str, Any]:
        snap = ctx.get("snapshot", {})
        # Map function id -> backbone wrapper + evidence key
        if fn_id == "compute_process_automation_coverage":
            raw = _llm.grade_process_automation_coverage(_get_evidence(snap, "process_automation_coverage"))
            return sanitize_metric("process.automation.coverage", raw)

        if fn_id == "compute_workflow_sla_adherence":
            raw = _llm.grade_workflow_sla_adherence(_get_evidence(snap, "workflow_sla_adherence"))
            return sanitize_metric("workflow.sla_adherence", raw)

        if fn_id == "compute_lead_to_oppty_cycle_time":
            raw = _llm.grade_sales_lead_to_oppty_cycle_time(_get_evidence(snap, "lead_to_oppty_cycle_time"))
            return sanitize_metric("sales.lead_to_oppty_cycle_time", raw)

        if fn_id == "compute_case_resolution_time":
            raw = _llm.grade_itsm_case_resolution_time(_get_evidence(snap, "case_resolution_time_sn"))
            return sanitize_metric("itsm.case_resolution_time", raw)

        if fn_id == "compute_incident_reopen_rate":
            raw = _llm.grade_itsm_incident_reopen_rate(_get_evidence(snap, "incident_reopen_rate_sn"))
            return sanitize_metric("itsm.incident_reopen_rate", raw)

        if fn_id == "compute_hr_onboarding_cycle_time":
            raw = _llm.grade_hr_onboarding_cycle_time(_get_evidence(snap, "hr_onboarding_cycle_time"))
            return sanitize_metric("hr.onboarding_cycle_time", raw)

        if fn_id == "compute_procure_to_pay_cycle":
            raw = _llm.grade_sap_procure_to_pay_cycle(_get_evidence(snap, "procure_to_pay_cycle_time"))
            return sanitize_metric("sap.procure_to_pay_cycle", raw)

        if fn_id == "compute_q2c_throughput":
            raw = _llm.grade_q2c_throughput(_get_evidence(snap, "q2c_throughput"))
            return sanitize_metric("q2c.throughput", raw)

        if fn_id == "compute_backlog_aging":
            raw = _llm.grade_backlog_aging(_get_evidence(snap, "backlog_aging"))
            return sanitize_metric("backlog.aging", raw)

        if fn_id == "compute_rpa_success_rate":
            raw = _llm.grade_rpa_success_rate(_get_evidence(snap, "rpa_success_rate"))
            return sanitize_metric("rpa.success_rate", raw)

        # Integration & Data Health
        if fn_id == "compute_data_sync_latency":
            raw = _llm.grade_integration_data_sync_latency(_get_evidence(snap, "data_sync_latency"))
            return sanitize_metric("integration.data_sync_latency", raw)

        if fn_id == "compute_api_reliability":
            raw = _llm.grade_api_reliability(_get_evidence(snap, "api_reliability"))
            return sanitize_metric("api.reliability", raw)

        if fn_id == "compute_integration_topology_health":
            raw = _llm.grade_integration_topology_health(_get_evidence(snap, "integration_topology_health"))
            return sanitize_metric("integration.topology_health", raw)

        if fn_id == "compute_duplicate_record_rate":
            raw = _llm.grade_mdm_duplicate_rate(_get_evidence(snap, "duplicate_record_rate"))
            return sanitize_metric("mdm.duplicate_rate", raw)

        if fn_id == "compute_dq_exceptions_rate":
            raw = _llm.grade_dq_exceptions_rate(_get_evidence(snap, "dq_exceptions_rate"))
            return sanitize_metric("dq.exceptions_rate", raw)

        # AI
        if fn_id == "compute_ai_penetration":
            raw = _llm.grade_ai_penetration(_get_evidence(snap, "ai_integration_penetration"))
            return sanitize_metric("ai.penetration", raw)

        if fn_id == "compute_ai_outcome_uplift":
            raw = _llm.grade_ai_outcome_uplift(_get_evidence(snap, "ai_outcome_uplift"))
            return sanitize_metric("ai.outcome_uplift", raw)

        if fn_id == "compute_ai_governance_coverage":
            raw = _llm.grade_ai_governance_coverage(_get_evidence(snap, "ai_governance_coverage"))
            return sanitize_metric("ai.governance_coverage", raw)

        # Platform Risk
        if fn_id == "compute_platform_customization_debt":
            raw = _llm.grade_platform_customization_debt(_get_evidence(snap, "customization_debt_index"))
            return sanitize_metric("platform.customization_debt", raw)

        if fn_id == "compute_change_failure_rate":
            raw = _llm.grade_change_failure_rate(_get_evidence(snap, "change_failure_rate"))
            return sanitize_metric("change.failure_rate", raw)

        # Unknown
        return sanitize_metric(fn_id, {"Score": 3, "rationale": "Unknown metric id.", "gaps": []})

    return compute