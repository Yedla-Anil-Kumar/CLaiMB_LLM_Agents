# agent_layer/registry.py
from typing import List, Dict

"""
BI Tracker registry (DAG + category weights), cloud-infra style.

- LEVEL0: metrics with no dependencies (run in parallel)
- LEVEL1_DEPS: metrics that depend on Level-0 results
- CATEGORIES: category-level weights and per-metric weights (sum to 1 within category)

Top-level categories use a simple 50/50 split as requested:
  - business_integration: 0.50
  - decision_making:      0.50
"""

# -----------------------------
# Level 0 (parallel, no deps)
# -----------------------------
LEVEL0: List[str] = [
    # Usage & Adoption
    "usage.dau_mau",
    "usage.creators_ratio",
    "usage.session_depth",
    "usage.drilldown",
    "usage.weekly_active_trend",
    "usage.retention_4w",

    # Features
    "features.cross_links",
    "features.export_rate",
    "features.alerts_usage",

    # Governance
    "governance.coverage",
    "governance.pii_coverage",
    "governance.lineage_coverage",

    # Reliability
    "reliability.refresh_timeliness",
    "reliability.sla_breach_streaks",
    "reliability.error_rate_queries",

    # Data breadth
    "data.source_diversity",

    # Democratization (independent)
    "democratization.dept_coverage",
]

# ----------------------------------------
# Level 1 (depends on one or more Level 0)
# ----------------------------------------
LEVEL1_DEPS: Dict[str, List[str]] = {
    # Self-service depends on core adoption signals
    "democratization.self_service": [
        "usage.creators_ratio",
        "usage.dau_mau",
        "governance.coverage",
    ],

    # Decision traceability depends on governance and cross-linking
    "decision.traceability": [
        "governance.lineage_coverage",
        "governance.coverage",
        "features.cross_links",
    ],

    # Cost efficiency depends on freshness & error rate (proxy for wasted runs / unreliable views)
    "data.cost_efficiency": [
        "reliability.refresh_timeliness",
        "reliability.error_rate_queries",
    ],
}

# ------------------------------------------------------
# Categories & weights (each metric weights sum to 1.00)
# ------------------------------------------------------
CATEGORIES: Dict[str, Dict] = {
    "business_integration": {
        "weight": 0.50,
        "metrics": {
            # Core adoption / stickiness
            "usage.dau_mau":               0.14,
            "usage.creators_ratio":        0.12,
            "usage.session_depth":         0.08,
            "usage.drilldown":             0.06,

            # Feature usage
            "features.cross_links":        0.08,
            "features.alerts_usage":       0.06,
            "features.export_rate":        0.06,

            # Breadth / coverage
            "data.source_diversity":       0.08,
            "democratization.self_service":0.12,  # Level-1

            # Growth signals
            "usage.weekly_active_trend":   0.10,
            "usage.retention_4w":          0.06,

            # Democratization spread
            "democratization.dept_coverage": 0.04,
        },
    },

    "decision_making": {
        "weight": 0.50,
        "metrics": {
            # Freshness & reliability
            "reliability.refresh_timeliness": 0.22,
            "reliability.sla_breach_streaks": 0.14,
            "reliability.error_rate_queries": 0.16,

            # Governance
            "governance.coverage":        0.16,
            "governance.pii_coverage":    0.10,
            "governance.lineage_coverage":0.10,

            # Traceability (Level-1)
            "decision.traceability":      0.08,

            # Efficiency (Level-1)
            "data.cost_efficiency":       0.04,
        },
    },
}