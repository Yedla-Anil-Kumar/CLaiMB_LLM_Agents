from __future__ import annotations

INFRA_MODEL_EXPORT_EXAMPLE = {
    "ModelExportAgent": {
        "input_key_meanings": {"code_snippets": "Snippets that save models to disk or registries."},
        "example_input": {
            "code_snippets": [
                """\
                    import joblib, json, time, hashlib
                    model_path = f"artifacts/model_{int(time.time())}.joblib"
                    joblib.dump(model, model_path)
                    metadata = {
                        "framework": "sklearn",
                        "version": "1.2.0",
                        "signature": {"inputs": ["f1","f2","f3"], "outputs": ["y_hat"]},
                    }
                    with open(model_path + '.meta.json', 'w') as f:
                        json.dump(metadata, f)
                    with open(model_path, 'rb') as f:
                        sha256 = hashlib.sha256(f.read()).hexdigest()
                """
            ]
        },
        "example_output": {
            "metric_id": "infra.model_export",
            "band": 5,
            "rationale": "Model persisted with versioned path, metadata, signature, and integrity hash.",
            "flags": ["versioned_path", "metadata_present", "signature_present", "integrity_hash"],
            "gaps": [
                "Publish a model card (intended use/limits) in artifacts → audit-ready exports (keeps band 5)."
            ]
        }
    }
}