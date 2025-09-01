from __future__ import annotations

EXPERIMENT_DETECTION_EXAMPLE = {
    "ExperimentDetectionAgent": {
        "input_key_meanings": {
            "file_paths": "Folders like experiments/, mlruns/, notebooks/experiments/"
        },
        "example_input": {
            "file_paths": [
                "experiments/exp_2025_08_21/config.yaml",
                "mlruns/0/meta.yaml"
            ]
        },
        "example_output": {
            "metric_id": "repo.experiments_management",
            "band": 4,
            "rationale": "MLflow directories and experiment configs exist; artifact/signature logging completeness is unclear.",
            "flags": ["artifact_completeness_unknown", "signature_missing"],
            "gaps": [
                "Artifact set not standardized → persist model binaries + eval reports each run → ≥90% runs complete (unlocks band 5).",
                "Model signature missing → log schema/examples → guarantee reproducible serving (supports band 5)."
            ]
        }
    }
}