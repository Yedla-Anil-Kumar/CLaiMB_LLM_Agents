import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from .prompts import DataManagementPrompts, AnalyticsReadinessPrompts

class DataManagementMetrics:

    def __init__(self, api_key: str = None):
        load_dotenv()
        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise ValueError("Missing OPENAI_API_KEY in .env file")
        self.client = OpenAI(api_key=self.key)

    def _load_json(self, path: str) -> str:
        """Helper: read JSON file and return raw JSON string."""
        with open(path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f), ensure_ascii=False)

    def _ask_openai(self, prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """Helper: call OpenAI chat model and return parsed JSON response."""
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a structured evaluator. Always return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        
        raw = response.choices[0].message.content.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print("DEBUG RAW:", raw)
            raise e

    # === Evaluators ===

    def check_schema_consistency(self, baseline_schema_json: str, table_schemas_json: str) -> Dict[str, Any]:
        task_input = {
            "baseline_schema": json.loads(baseline_schema_json),
            "actual_schema": json.loads(table_schemas_json),
        }
        task_input_json = json.dumps(task_input, ensure_ascii=False)
        prompt = DataManagementPrompts.get_schema_consistency_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_data_freshness(self, table_metadata_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(table_metadata_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_data_freshness_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_data_quality(self, data_quality_report_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(data_quality_report_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_data_quality_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_governance_compliance(self, access_logs_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(access_logs_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_governance_compliance_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_data_lineage(self, lineage_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(lineage_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_data_lineage_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_metadata_coverage(self, metadata_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(metadata_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_metadata_coverage_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_sensitive_tagging(self, tagging_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(tagging_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_sensitive_tagging_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_duplication(self, duplication_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(duplication_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_duplication_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_backup_recovery(self, backup_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(backup_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_backup_recovery_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_security_config(self, security_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(security_json), ensure_ascii=False)
        prompt = DataManagementPrompts.get_security_config_prompt(task_input_json)
        return self._ask_openai(prompt)


class AnalyticsReadinessMetrics:

    def __init__(self, api_key: str = None):
        load_dotenv()
        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise ValueError("Missing OPENAI_API_KEY in .env file")
        self.client = OpenAI(api_key=self.key)

    # === Internal Helpers ===
    def _load_json(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f), ensure_ascii=False)

    def _ask_openai(self, prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an advanced Analytics Readiness evaluator. Always return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        
        raw = response.choices[0].message.content.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print("DEBUG RAW:", raw)
            raise e

    # === Evaluators ===

    def compute_pipeline_success_rate(self, pipeline_runs_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(pipeline_runs_json), ensure_ascii=False)
        prompt = AnalyticsReadinessPrompts.get_pipeline_success_rate_prompt(task_input_json)
        return self._ask_openai(prompt)

    def compute_pipeline_latency_throughput(self, pipeline_metrics_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(pipeline_metrics_json), ensure_ascii=False)
        prompt = AnalyticsReadinessPrompts.get_pipeline_latency_throughput_prompt(task_input_json)
        return self._ask_openai(prompt)

    def evaluate_resource_utilization(self, resource_usage_json: str) -> Dict[str, Any]:
        task_input = {
            "resource_usage": json.loads(resource_usage_json),
        }
        task_input_json = json.dumps(task_input, ensure_ascii=False)
        prompt = AnalyticsReadinessPrompts.get_resource_utilization_prompt(task_input_json)
        return self._ask_openai(prompt)

    def assess_query_performance(self, query_logs_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(query_logs_json), ensure_ascii=False)
        prompt = AnalyticsReadinessPrompts.get_query_performance_prompt(task_input_json)
        return self._ask_openai(prompt)

    def compute_analytics_adoption(self, user_activity_json: str) -> Dict[str, Any]:
        task_input_json = json.dumps(json.loads(user_activity_json), ensure_ascii=False)
        prompt = AnalyticsReadinessPrompts.get_analytics_adoption_prompt(task_input_json)
        return self._ask_openai(prompt)
