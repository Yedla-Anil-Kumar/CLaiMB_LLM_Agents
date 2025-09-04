# agent_layer/registry.py
from typing import Dict, List

"""
Code Repo Agent registry (DAG + category weights) — BI-Tracker style.

LEVEL0: run in parallel (no deps)
LEVEL1_DEPS: optional downstream metrics
CATEGORIES: 2 buckets with per-metric weights that sum to 1.00
"""

# -----------------------------
# Level 0 (parallel, no deps)
# -----------------------------
LEVEL0: List[str] = [
    # Code quality
    "code.cyclomatic_complexity_band",
    "code.maintainability_band",
    "code.docstring_coverage_band",
    "code.nested_loops_band",

    # Infra (execution/runtime)
    "infra.parallel_patterns",
    "infra.security_hygiene",

    # Serving & pipelines
    "infra.data_pipeline",
    "infra.feature_engineering",

    # ML framework layer
    "ml.framework_maturity",
    "ml.data_validation",
    "ml.experiment_tracking",
    "ml.hpo_practice",
    "ml.training_practice",
    "ml.evaluation_practice",

    # File-system (your earlier concern — included!)
    "fs.tests_practice",
    "fs.env_config_maturity",
    "fs.ci_cd_maturity",
    "fs.deployment_maturity",
    "fs.experiment_org",
    "fs.project_structure",
]

# ----------------------------------------
# Level 1 — (light) sample dependencies
# ----------------------------------------
LEVEL1_DEPS: Dict[str, List[str]] = {
    # Expose/model endpoints often sit on trained/exported models & FE parity
    "infra.inference_endpoint": [
        "ml.training_practice",
        "infra.feature_engineering",
    ],
    # Export maturity benefits from training discipline
    "infra.model_export": [
        "ml.training_practice",
        "ml.experiment_tracking",
    ],
}

# ------------------------------------------------------
# Categories & weights (each metric weights sum to 1.00)
# ------------------------------------------------------
CATEGORIES: Dict[str, Dict] = {
    "development_maturity": {
        "weight": 0.50,
        "metrics": {
            # Code quality
            "code.maintainability_band":       0.14,
            "code.docstring_coverage_band":    0.10,
            "code.cyclomatic_complexity_band": 0.10,
            "code.nested_loops_band":          0.06,

            # Infra hygiene
            "infra.parallel_patterns":         0.06,
            "infra.security_hygiene":          0.10,

            # FS / SDLC signals
            "fs.tests_practice":               0.12,
            "fs.env_config_maturity":          0.06,
            "fs.ci_cd_maturity":               0.10,
            "fs.deployment_maturity":          0.06,
            "fs.project_structure":            0.06,
            # (fs.experiment_org placed under innovation below)
        },
    },

    "innovation_pipeline": {
        "weight": 0.50,
        "metrics": {
            # ML/FE/Pipelines
            "infra.data_pipeline":             0.08,
            "infra.feature_engineering":       0.10,
            "infra.model_export":              0.10,  # level-1
            "infra.inference_endpoint":        0.10,  # level-1

            # ML practice quality
            "ml.framework_maturity":           0.10,
            "ml.data_validation":              0.12,
            "ml.experiment_tracking":          0.12,
            "ml.hpo_practice":                 0.08,
            "ml.training_practice":            0.08,
            "ml.evaluation_practice":          0.07,

            # FS: experiments layout indicates experimentation culture
            "fs.experiment_org":               0.05,
        },
    },
}