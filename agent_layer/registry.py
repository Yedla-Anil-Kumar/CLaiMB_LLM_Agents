# agent_layer/registry.py
# Level 0 (parallel): 
LEVEL0 = [
    "tagging.coverage",
    "compute.utilization",
    "k8s.utilization",
    "db.utilization",
    "storage.efficiency",
    "lb.performance",
    "availability.incidents",
    "cost.commit_coverage",
    "iac.coverage_drift",
    "security.encryption",
    "security.iam_risk",
    "security.public_exposure",
    "security.vuln_patch",
    "cost.allocation_quality",
    "cost.idle_underutilized",
    "scaling.effectiveness",
]

# Level 1 (depends on Level 0)
LEVEL1_DEPS = {
    "cost.allocation_quality": ["tagging.coverage"],
    "cost.idle_underutilized": ["compute.utilization", "k8s.utilization"],
    "scaling.effectiveness": ["compute.utilization"],
}

# Categories and their weightage
CATEGORIES = {
    "cost": {
        "weight": 0.30,
        "metrics": {
            "cost.commit_coverage": 0.35,
            "cost.allocation_quality": 0.35,
            "cost.idle_underutilized": 0.30,
        }
    },
    "efficiency": {
        "weight": 0.30,
        "metrics": {
            "compute.utilization": 0.22,
            "k8s.utilization": 0.22,
            "db.utilization": 0.18,
            "storage.efficiency": 0.18,
            "scaling.effectiveness": 0.20,
        }
    },
    "reliability": {
        "weight": 0.20,
        "metrics": {
            "availability.incidents": 0.60,
            "lb.performance": 0.40,
        }
    },
    "security": {
        "weight": 0.20,
        "metrics": {
            "security.encryption": 0.25,
            "security.iam_risk":   0.25,
            "security.public_exposure": 0.20,
            "security.vuln_patch": 0.20,
            "iac.coverage_drift": 0.10, 
        }
    },
}
