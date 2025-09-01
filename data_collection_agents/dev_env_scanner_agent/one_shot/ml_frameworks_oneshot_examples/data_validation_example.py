from __future__ import annotations

MLFRAMEWORK_DATAVALIDATIONAGENT_EXAMPLE = {
    "DataValidationAgent": {
        "input_key_meanings": {"code_snippets": "Pipelines validating data schemas/distributions/drift."},
        "example_input": {
            "code_snippets": [
                """\
                    from great_expectations.dataset import PandasDataset

                    ds = PandasDataset(df)
                    ds.expect_column_values_to_not_be_null('user_id')
                    ds.expect_column_values_to_be_between('amount', min_value=0)
                    _ = ds.validate()  # CI gating not wired here
                """
            ]
        },
        "example_output": {
            "metric_id": "ml.data_validation",
            "band": 4,
            "rationale": "Schema and range checks are present; CI enforcement and drift monitoring are not explicit.",
            "flags": ["ci_enforcement_unknown", "drift_monitoring_missing"],
            "gaps": [
                "Validation not gated → wire into CI and block on critical failures → prevent bad data (unlocks band 5).",
                "No drift checks → add distribution monitors post-deploy → early anomaly detection (supports band 5)."
            ]
        }
    }
}