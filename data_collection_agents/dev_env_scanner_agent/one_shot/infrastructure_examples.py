# Data_Collection_Agents/dev_env_scanner/one_shot/infrastructure_examples.py
from __future__ import annotations

INFRASTRUCTURE_EXAMPLES = {
    "ParallelPatternsAgent": {
        "input_key_meanings": {"code_snippets": "Snippets that might use threading/multiprocessing/concurrent.futures."},
        "example_input": {
            "code_snippets": [
                """\
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch(url):
    resp = session.get(url, timeout=5)
    return resp.status_code

with ThreadPoolExecutor(max_workers=16) as ex:
    futures = [ex.submit(fetch, u) for u in urls]
    results = [f.result() for f in as_completed(futures)]
"""
            ]
        },
        "example_output": {
            "parallel_tools": {"concurrent.futures": True, "threading": False, "multiprocessing": False},
            "parallel_patterns": ["thread-pool fan-out/fan-in"],
            "scalability_analysis": "Network-bound; threads scale well to dozens; watch connection pooling.",
            "optimization_opportunities": ["Share a single HTTP session", "Bound queue to avoid over-submission"]
        }
    },

    "InferenceEndpointAgent": {
        "input_key_meanings": {"code_snippets": "Web service code implementing inference endpoints."},
        "example_input": {
            "code_snippets": [
                """\
from fastapi import FastAPI
import joblib
app = FastAPI()
model = joblib.load('model.joblib')

@app.post('/predict')
def predict(payload: dict):
    x = vectorize(payload['features'])
    y = model.predict([x])[0]
    return {'prediction': float(y)}
"""
            ]
        },
        "example_output": {
            "inference_frameworks": {"fastapi": True, "flask": False, "streamlit": False},
            "serving_patterns": ["synchronous HTTP prediction", "on-start model load"],
            "deployment_quality": 0.76,
            "scalability_considerations": ["Cold start acceptable; add health/readiness probes; add pydantic schemas"]
        }
    },

    "ModelExportAgent": {
        "input_key_meanings": {"code_snippets": "Snippets that save models to disk or external stores."},
        "example_input": {
            "code_snippets": [
                """\
import joblib
from sklearn.linear_model import LogisticRegression

clf = LogisticRegression().fit(X, y)
joblib.dump(clf, 'artifacts/model.joblib')
"""
            ]
        },
        "example_output": {
            "export_patterns": {"joblib.dump": True, "torch.save": False, "onnx": False},
            "model_formats": ["joblib"],
            "export_quality": 0.7,
            "deployment_readiness": "Versioned path exists; add schema & model card"
        }
    },

    "DataPipelineAgent": {
        "input_key_meanings": {"code_snippets": "DAGs/flows/workflows for data movement or feature pipelines."},
        "example_input": {
            "code_snippets": [
                """\
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG('etl_orders', start_date=datetime(2024,1,1), schedule='@daily', catchup=False) as dag:
    extract = PythonOperator(task_id='extract', python_callable=extract_fn)
    transform = PythonOperator(task_id='transform', python_callable=transform_fn)
    load = PythonOperator(task_id='load', python_callable=load_fn)
    extract >> transform >> load
"""
            ]
        },
        "example_output": {
            "pipeline_tools": {"airflow": True, "prefect": False, "luigi": False, "argo": False, "kedro": False},
            "pipeline_patterns": ["ETL DAG", "daily schedule", "task chaining"],
            "pipeline_quality": 0.74,
            "orchestration_approach": "Centralized scheduler; add retries & SLAs"
        }
    },

    "FeatureEngineeringAgent": {
        "input_key_meanings": {"code_snippets": "Preprocessing/feature transformation code."},
        "example_input": {
            "code_snippets": [
                """\
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

ct = ColumnTransformer([
    ('num', StandardScaler(), ['age','income']),
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['country'])
])
Xtr = ct.fit_transform(df)
"""
            ]
        },
        "example_output": {
            "feature_tools": {"sklearn.preprocessing": True, "featuretools": False, "tsfresh": False},
            "feature_patterns": ["column-wise transforms", "one-hot encoding"],
            "feature_quality": 0.78,
            "automation_level": "Pipeline-ready; persist transformer for inference parity"
        }
    },

    "SecurityAgent": {
        "input_key_meanings": {"code_snippets": "Any code possibly containing secrets or weak validation."},
        "example_input": {
            "code_snippets": [
                """\
SENTRY_DSN = "https://key:secret@sentry.io/12345"  # hardcoded!
def login(user, pwd):
    if len(pwd) < 6:
        return False
    return True
"""
            ]
        },
        "example_output": {
            "security_issues": ["Hardcoded credential-like string (SENTRY_DSN)", "Weak password policy"],
            "secret_exposure": "Likely",
            "security_score": 0.35,
            "recommendations": ["Move secrets to env/secret manager", "Enforce strong password policy + rate limiting"]
        }
    },
}