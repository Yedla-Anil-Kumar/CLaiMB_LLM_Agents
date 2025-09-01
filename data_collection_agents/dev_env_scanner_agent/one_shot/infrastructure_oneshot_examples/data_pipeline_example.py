from __future__ import annotations

INFRA_DATA_PIPELINE_EXAMPLE = {
    "DataPipelineAgent": {
        "input_key_meanings": {"code_snippets": "DAGs/flows/workflows for data pipelines."},
        "example_input": {
            "code_snippets": [
                """\
                    from airflow import DAG
                    from airflow.operators.python import PythonOperator
                    from datetime import datetime, timedelta

                    def extract_fn(): ...
                    def transform_fn(): ...
                    def validate_fn(): ...
                    def load_fn(): ...

                    default_args = {"retries": 3, "retry_delay": timedelta(minutes=5), "sla": timedelta(minutes=60)}
                    with DAG('etl_orders', start_date=datetime(2025,1,1), schedule='@daily', catchup=False, default_args=default_args) as dag:
                        extract = PythonOperator(task_id='extract', python_callable=extract_fn)
                        transform = PythonOperator(task_id='transform', python_callable=transform_fn)
                        validate = PythonOperator(task_id='validate', python_callable=validate_fn)
                        load = PythonOperator(task_id='load', python_callable=load_fn)
                        extract >> transform >> validate >> load
                """
            ]
        },
        "example_output": {
            "metric_id": "infra.data_pipeline",
            "band": 5,
            "rationale": "Daily Airflow DAG with retries, SLA, and a validation gate before load; scheduling and chaining are clear.",
            "flags": ["retries_configured", "sla_defined", "validation_gate_present"],
            "gaps": [
                "Add on-failure alerts to on-call channel → faster incident response (maintains band 5)."
            ]
        }
    }
}