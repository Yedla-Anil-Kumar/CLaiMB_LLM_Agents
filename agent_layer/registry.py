# agent_layer/registry.py
from __future__ import annotations

# Category weights (50/50 per the MVP)
CATEGORY_WEIGHTS = {
    "business_integration": 0.5,
    "decision_making": 0.5,
}

# 20 BI metrics: category + dependencies (for simple 2-level DAG)
REGISTRY = {
    # ---- Level 0 (no deps) ------------------------------------
    "usage.dau_mau":                   {"category": "business_integration", "depends_on": []},
    "usage.creators_ratio":            {"category": "business_integration", "depends_on": []},
    "usage.session_depth":             {"category": "business_integration", "depends_on": []},
    "usage.drilldown":                 {"category": "business_integration", "depends_on": []},
    "usage.weekly_active_trend":       {"category": "business_integration", "depends_on": []},
    "usage.retention_4w":              {"category": "business_integration", "depends_on": []},
    "features.cross_links":            {"category": "business_integration", "depends_on": []},
    "features.export_rate":            {"category": "business_integration", "depends_on": []},
    "features.alerts_usage":           {"category": "business_integration", "depends_on": []},
    "democratization.dept_coverage":   {"category": "business_integration", "depends_on": []},

    "reliability.refresh_timeliness":  {"category": "decision_making",      "depends_on": []},
    "reliability.sla_breach_streaks":  {"category": "decision_making",      "depends_on": []},
    "reliability.error_rate_queries":  {"category": "decision_making",      "depends_on": []},
    "governance.coverage":             {"category": "decision_making",      "depends_on": []},
    "governance.pii_coverage":         {"category": "decision_making",      "depends_on": []},
    "governance.lineage_coverage":     {"category": "decision_making",      "depends_on": []},

    "data.source_diversity":           {"category": "business_integration", "depends_on": []},

    # ---- Level 1 (has deps) -----------------------------------
    # Examples from your spec:
    #  self_service ← creators_ratio, dau_mau, governance_coverage
    "democratization.self_service":    {
        "category": "business_integration",
        "depends_on": ["usage.creators_ratio", "usage.dau_mau", "governance.coverage"],
    },
    #  decision_traceability ← lineage_coverage, governance_coverage, cross_links
    "decision.traceability":           {
        "category": "decision_making",
        "depends_on": ["governance.lineage_coverage", "governance.coverage", "features.cross_links"],
    },
    #  cost_efficiency ← refresh_timeliness, error_rate_queries
    "data.cost_efficiency":            {
        "category": "decision_making",
        "depends_on": ["reliability.refresh_timeliness", "reliability.error_rate_queries"],
    },
}