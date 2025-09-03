# agent_layer/registry_mlops.py
from typing import Dict, List

# -------- Level 0 (no deps; run in parallel) --------
LEVEL0: List[str] = [
    # MLflow
    "mlflow.experiment_completeness_band",
    "mlflow.lineage_coverage_band",
    "mlflow.experiment_velocity_band",
    "mlflow.registry_hygiene_band",
    "mlflow.validation_artifacts_band",
    "mlflow.reproducibility_band",

    # AML
    "aml.jobs_flow_band",
    "aml.monitoring_coverage_band",
    "aml.registry_governance_band",
    "aml.cost_correlation_band",

    # SageMaker
    "sm.pipeline_flow_band",
    "sm.experiments_lineage_band",
    "sm.clarify_coverage_band",

    # CI/CD
    "cicd.deploy_frequency_band",
    "cicd.lead_time_band",
    "cicd.change_failure_rate_band",
    "cicd.policy_gates_band",
]

# -------- Level 1 (depends on Level 0) ---------------
LEVEL1_DEPS: Dict[str, List[str]] = {
    # SLO depends on jobs flow + monitoring
    "aml.endpoint_slo_band": [
        "aml.jobs_flow_band",
        "aml.monitoring_coverage_band",
    ],
    # SM endpoint SLO/scaling depends on pipeline flow + monitoring
    "sm.endpoint_slo_scaling_band": [
        "sm.pipeline_flow_band",
        "aml.monitoring_coverage_band",  # cross-platform monitor proxy
    ],
    # Cost efficiency depends on cost correlation + pipeline flow
    "sm.cost_efficiency_band": [
        "aml.cost_correlation_band",
        "sm.pipeline_flow_band",
    ],
}

# -------- Categories & weights -----------------------
# Mentor asks: Data Management 0.6, Analytics Readiness 0.4
CATEGORIES = {
    "data_management": {
        "weight": 0.60,
        "metrics": {
            # Experimentation hygiene / lineage / registry / validation
            "mlflow.experiment_completeness_band": 0.10,
            "mlflow.lineage_coverage_band":        0.10,
            "mlflow.registry_hygiene_band":        0.10,
            "mlflow.validation_artifacts_band":    0.10,
            "mlflow.reproducibility_band":         0.05,

            # Platform governance / monitoring / cost attribution
            "aml.registry_governance_band":        0.06,
            "aml.monitoring_coverage_band":        0.06,
            "aml.cost_correlation_band":           0.07,

            # CI/CD guardrails (process hygiene influences DM readiness)
            "cicd.policy_gates_band":              0.06,
            "cicd.change_failure_rate_band":       0.05,
            "cicd.lead_time_band":                 0.05,
        },
    },
    "analytics_readiness": {
        "weight": 0.40,
        "metrics": {
            # Throughput/velocity & pipeline flow
            "mlflow.experiment_velocity_band":     0.08,
            "sm.pipeline_flow_band":               0.08,

            # Endpoints SLO/scale (composite)
            "aml.endpoint_slo_band":               0.10,
            "sm.endpoint_slo_scaling_band":        0.08,

            # Explainability / bias & cost efficiency
            "sm.experiments_lineage_band":         0.06,
            "sm.clarify_coverage_band":            0.06,
            "sm.cost_efficiency_band":             0.06,

            # Deployment cadence (capacity to deliver insights)
            "cicd.deploy_frequency_band":          0.08,
        },
    },
}

# Optional: A..E → score_0to100
BAND_TO_SCORE = {"A": 100, "B": 85, "C": 70, "D": 55, "E": 40}