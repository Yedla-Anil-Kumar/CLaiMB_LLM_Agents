# agent_layer/registry_enterprise.py
from __future__ import annotations
from typing import Dict, List

"""
Enterprise Systems Agent — DAG registry + category mapping.

Nodes = metric wrapper function ids (compute_*).
Edges = depends_on (parents must finish before child runs).

Category weights:
  - data_management:       0.60
  - analytics_readiness:   0.40
"""

# -----------------------------
# DAG (depends_on adjacency)
# -----------------------------
REGISTRY: Dict[str, Dict[str, List[str]]] = {
    # ----- Level 0: base signals (no deps, run in parallel) -----
    "compute_process_automation_coverage": {"depends_on": []},
    "compute_workflow_sla_adherence": {"depends_on": []},
    "compute_lead_to_oppty_cycle_time": {"depends_on": []},
    "compute_case_resolution_time": {"depends_on": []},
    "compute_incident_reopen_rate": {"depends_on": []},
    "compute_hr_onboarding_cycle_time": {"depends_on": []},
    "compute_procure_to_pay_cycle": {"depends_on": []},
    "compute_q2c_throughput": {"depends_on": []},
    "compute_backlog_aging": {"depends_on": []},
    "compute_rpa_success_rate": {"depends_on": []},

    "compute_data_sync_latency": {"depends_on": []},
    "compute_api_reliability": {"depends_on": []},
    "compute_duplicate_record_rate": {"depends_on": []},
    "compute_dq_exceptions_rate": {"depends_on": []},

    "compute_ai_penetration": {"depends_on": []},

    "compute_platform_customization_debt": {"depends_on": []},
    "compute_change_failure_rate": {"depends_on": []},

    # ----- Level 1: derived from L0 -----
    "compute_integration_topology_health": {
        "depends_on": [
            "compute_api_reliability",
            "compute_data_sync_latency",
            "compute_duplicate_record_rate",
            "compute_dq_exceptions_rate",
        ]
    },
    "compute_ai_governance_coverage": {
        "depends_on": [
            "compute_integration_topology_health"
        ]
    },

    # ----- Level 2: derived from L0 + L1 -----
    "compute_ai_outcome_uplift": {
        "depends_on": [
            # L0 process KPIs
            "compute_case_resolution_time",
            "compute_q2c_throughput",
            "compute_procure_to_pay_cycle",
            "compute_lead_to_oppty_cycle_time",
            "compute_incident_reopen_rate",
            # L0 adoption
            "compute_ai_penetration",
            # L1
            "compute_integration_topology_health",
            "compute_ai_governance_coverage",
        ]
    },
}

# ---------------------------------
# Categories & top-level weighting
# ---------------------------------
CATEGORY_WEIGHTS = {
    "data_management": 0.60,
    "analytics_readiness": 0.40,
}

CATEGORIES = {
    "data_management": [
        # Integration & Data Health
        "compute_data_sync_latency",
        "compute_api_reliability",
        "compute_integration_topology_health",
        "compute_duplicate_record_rate",
        "compute_dq_exceptions_rate",
        # Platform Health / Risk
        "compute_platform_customization_debt",
        "compute_change_failure_rate",
    ],
    "analytics_readiness": [
        # Process & Workflow (10)
        "compute_process_automation_coverage",
        "compute_workflow_sla_adherence",
        "compute_lead_to_oppty_cycle_time",
        "compute_case_resolution_time",
        "compute_incident_reopen_rate",
        "compute_hr_onboarding_cycle_time",
        "compute_procure_to_pay_cycle",
        "compute_q2c_throughput",
        "compute_backlog_aging",
        "compute_rpa_success_rate",
        # AI Integration & Outcomes (3)
        "compute_ai_penetration",
        "compute_ai_outcome_uplift",
        "compute_ai_governance_coverage",
    ],
}