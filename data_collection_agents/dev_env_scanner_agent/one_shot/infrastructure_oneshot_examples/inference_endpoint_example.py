from __future__ import annotations

INFRA_INFERENCE_ENDPOINT_EXAMPLE = {
    "InferenceEndpointAgent": {
        "input_key_meanings": {"code_snippets": "Web service code implementing inference endpoints."},
        "example_input": {
            "code_snippets": [
                """\
                    from fastapi import FastAPI
                    from pydantic import BaseModel
                    import joblib

                    class PredictIn(BaseModel):
                        features: list[float]

                    app = FastAPI()
                    model = joblib.load('artifacts/model.joblib')

                    @app.get('/healthz')
                    def health(): return {'ok': True}

                    @app.post('/predict')
                    def predict(payload: PredictIn):
                        y = model.predict([payload.features])[0]
                        return {'prediction': float(y), 'version': '1.0.3'}
                """
            ]
        },
        "example_output": {
            "metric_id": "infra.inference_endpoint",
            "band": 5,
            "rationale": "FastAPI with Pydantic schemas and health endpoint; model is versioned in response; synchronous path is acceptable.",
            "flags": ["schema_validation_present", "health_probe_present", "response_versioned"],
            "gaps": [
                "Log model signature/schema in registry → enable strict serving parity (maintains band 5)."
            ]
        }
    }
}