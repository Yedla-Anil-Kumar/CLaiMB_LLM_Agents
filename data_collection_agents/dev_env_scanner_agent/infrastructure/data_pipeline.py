from __future__ import annotations
from typing import Any, Dict, List, Optional
from loguru import logger

from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from data_collection_agents.dev_env_scanner_agent.logging_utils import timed

def _join_snippets(snippets: List[str]) -> str:
    return "\n\n".join([f"--- Snippet {i+1} ---\n{s}" for i, s in enumerate(snippets)])

class DataPipelineAgent(BaseMicroAgent):
    """
    metric_id: infra.data_pipeline
    """

    METRIC_ID = "infra.data_pipeline"
    RUBRIC = (
        "Evaluate DAG/flow config and reliability controls (Airflow/Prefect/Luigi/Argo/Kedro): "
        "scheduling, retries/backoff, SLAs/alerts, validation/quality steps, and observability.\n"
        "5: Well-instrumented pipeline with retries, SLAs, alerts, validation gates, and clear monitoring.\n"
        "4: Good structure with minor gaps (e.g., retries or validation missing).\n"
        "3: Basic DAG without reliability/validation hooks.\n"
        "2: Brittle ad-hoc scripts disguised as pipelines.\n"
        "1: No pipeline evidence."
    )
    INPUT_MEANINGS = {"code_snippets[]":"DAG/flow definitions or orchestration configs."}

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)
        task_input = {"code_snippets": _join_snippets(code_snippets)}
        system_prompt = (
            "You are a data pipeline orchestration analyst. Detect pipelines and review retries, SLAs, alerts, "
            "validation steps, and monitoring hooks. Return ONLY JSON."
        )

        prompt = build_metric_prompt(
            rubric=self.RUBRIC, metric_id=self.METRIC_ID,
            input_key_meanings=self.INPUT_MEANINGS, task_input=task_input,
            example_input=ex['example_input'], example_output=ex['example_output']
        )

        logger.debug(f"[{self.METRIC_ID}] prompt_len={len(prompt)}")
        with timed(f"metric.{self.METRIC_ID}"):
            raw = self._call_llm(prompt, system_prompt)
            out = self._parse_json_response(raw) or {}

        out.setdefault("metric_id", self.METRIC_ID)
        try: 
            out["band"] = max(1, min(5, int(out.get("band", 3))))
        except Exception: 
            out["band"] = 3
        out.setdefault("rationale","No rationale.")
        out.setdefault("flags",[]); out.setdefault("gaps",[])
        logger.info(f"[{self.METRIC_ID}] band={out['band']} rationale={out['rationale']}")
        return out