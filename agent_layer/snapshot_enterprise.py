# agent_layer/snapshot_enterprise.py
from __future__ import annotations
from typing import Any, Dict
from datetime import datetime, timezone

def collect_snapshot() -> Dict[str, Any]:
    """
    Tiny stub that simulates source payloads.
    Replace with real collectors later; keep fields aligned with EnterpriseInputs.
    """
    now = datetime.now(timezone.utc).isoformat()

    return {
        "meta": {"collected_at": now},

        # --- Process & Workflow ---
        "process_automation_coverage": {"computed": {"coverage_ratio": 0.72, "sf_active_flows": 8, "sn_active_flows": 4,
                                                     "wd_enabled_bps": 3, "sap_bpm_runs_7d": 220,
                                                     "estimated_automated_objects": 18, "estimated_total_objects": 25}},
        "workflow_sla_adherence": {"computed": {"on_time": 910, "total": 1000, "by_system": {"SF":0.92,"SN":0.9}}},
        "lead_to_oppty_cycle_time": {"computed": {"median_hours": 26, "p90_hours": 48, "sample": 400}},
        "case_resolution_time_sn": {"computed": {"median_minutes": 95, "p90_minutes": 180, "n_resolved": 700}},
        "incident_reopen_rate_sn": {"computed": {"rate": 0.085, "reopened": 51, "resolved": 600}},
        "hr_onboarding_cycle_time": {"computed": {"median_hours": 50, "p90_hours": 72, "n_hires": 40}},
        "procure_to_pay_cycle_time": {"computed": {"total_days": 10.5, "approval_days": 1.2, "gr_days": 5.0, "invoice_days": 4.3}},
        "q2c_throughput": {"computed": {"total_hours": 30, "quote_to_so_hours": 10, "so_to_bill_hours": 20}},
        "backlog_aging": {"computed": {"p50_days": 2.2, "p90_days": 5.5, "open_items": 320}},
        "rpa_success_rate": {"computed": {"rate": 0.94, "success": 940, "failed": 60, "by_system": {"SAP":0.93,"SF":0.95}}},

        # --- Integration & Data Health ---
        "data_sync_latency": {"computed": {"median_sec": 75, "p95_sec": 160, "failed_pct": 0.002}},
        "api_reliability": {"computed": {"p95_ms": 320, "error_rate_pct": 0.6, "rps": 110, "slo_p95_ms": 350}},
        "integration_topology_health": {"computed": {"avg_uptime": 99.7, "nodes_healthy": 3, "nodes_total": 3, "critical_errors": 0}},
        "duplicate_record_rate": {"computed": {"rate": 0.055, "duplicate_groups": 44, "total_entities": 800}},
        "dq_exceptions_rate": {"computed": {"rate": 0.032, "failed_checks": 90, "total_checks": 2800, "weighted_severity": 1.2}},

        # --- AI ---
        "ai_integration_penetration": {"computed": {"workflows_with_ai": 45, "workflows_total": 100, "executions_ai_pct": 0.42}},
        "ai_outcome_uplift": {"computed": {"uplift_pct": 0.11, "baseline": 200, "post": 178}},
        "ai_governance_coverage": {"computed": {"coverage": 0.78, "models_with_all_controls": 39, "models_total": 50, "alerts_30d": 2}},

        # --- Platform Risk ---
        "customization_debt_index": {"computed": {"index": 0.42, "sf_apex": 120, "sn_custom_records": 15,
                                                  "sap_transports_30d": 12, "wd_custom_steps": 5}},
        "change_failure_rate": {"computed": {"rate": 0.09, "deploys": 180, "failed_or_rollback": 16}},
    }