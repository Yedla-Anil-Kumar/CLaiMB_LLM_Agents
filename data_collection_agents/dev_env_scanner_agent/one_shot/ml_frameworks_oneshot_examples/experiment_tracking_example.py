from __future__ import annotations

MLFRAMEWORK_EXPERIMENTTRACKINGAGENT_EXAMPLE = {
    "ExperimentTrackingAgent": {
        "input_key_meanings": {"code_snippets": "Code that logs params/metrics/artifacts/signatures."},
        "example_input": {
            "code_snippets": [
                """\
                    import mlflow
                    with mlflow.start_run():
                        mlflow.log_param("lr", 1e-3)
                        mlflow.log_metric("loss", 0.23, step=10)
                        # model, signature logging not shown
                """
            ]
        },
        "example_output": {
            "metric_id": "ml.experiment_tracking",
            "band": 4,
            "rationale": "Parameters and metrics are consistently logged; artifact/signature and lineage are not fully evidenced.",
            "flags": ["artifacts_incomplete", "signature_missing", "lineage_unknown"],
            "gaps": [
                "Artifacts incomplete → persist model binaries and eval reports each run → ≥90% runs complete (unlocks band 5).",
                "Signature missing → log model signature & input example → reproducible serving (supports band 5).",
                "Lineage unclear → record dataset version/hash → traceable experiments (supports band 5)."
            ]
        }
    }
}