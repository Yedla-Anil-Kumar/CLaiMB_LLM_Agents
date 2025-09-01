from __future__ import annotations

INFRA_FEATURE_ENGINEERING_EXAMPLE = {
    "FeatureEngineeringAgent": {
        "input_key_meanings": {"code_snippets": "Preprocessing/feature transformation code."},
        "example_input": {
            "code_snippets": [
                """\
                    from sklearn.pipeline import Pipeline
                    from sklearn.preprocessing import StandardScaler, OneHotEncoder
                    from sklearn.compose import ColumnTransformer
                    import joblib

                    num_cols = ['age','income']
                    cat_cols = ['country']

                    ct = ColumnTransformer([
                        ('num', StandardScaler(), num_cols),
                        ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols),
                    ])

                    pipe = Pipeline([('prep', ct), ('model', clf)])
                    pipe.fit(df[num_cols+cat_cols], y)
                    joblib.dump(ct, 'artifacts/prep.joblib')
                    joblib.dump(pipe, 'artifacts/model.joblib')
                """
            ]
        },
        "example_output": {
            "metric_id": "infra.feature_engineering",
            "band": 5,
            "rationale": "Sklearn pipeline + ColumnTransformer with persisted fit transformers; ready for train/serve parity.",
            "flags": ["transformers_persisted", "pipeline_used", "parity_ready"],
            "gaps": [
                "Version the artifacts and log schema/examples → robust promotion workflows (keeps band 5)."
            ]
        }
    }
}