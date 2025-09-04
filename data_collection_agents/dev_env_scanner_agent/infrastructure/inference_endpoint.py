from __future__ import annotations
from typing import Any, Dict, List, Optional
from loguru import logger

from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from data_collection_agents.dev_env_scanner_agent.logging_utils import timed

def _join_snippets(snippets: List[str]) -> str:
    return "\n\n".join([f"--- Snippet {i+1} ---\n{s}" for i, s in enumerate(snippets)])

class InferenceEndpointAgent(BaseMicroAgent):
    """
    metric_id: infra.inference_endpoint
    """

    METRIC_ID = "infra.inference_endpoint"
    RUBRIC = (
        "Evaluate the quality of model-serving endpoints (FastAPI/Flask/gRPC/etc.): "
        "request/response schema validation, health/readiness probes, error handling, "
        "async/batching where appropriate, model loading strategy, and logging.\n"
        "5: Strong framework usage + schemas + health/readiness + robust error handling + "
        "model signature and versioning.\n"
        "4: Solid endpoint with minor gaps (e.g., health probe or signature missing).\n"
        "3: Works but lacks validation or operational hooks.\n"
        "2: Ad-hoc serving with risks (blocking, no error handling).\n"
        "1: No clear serving endpoints or unsafe patterns."
    )
    INPUT_MEANINGS = {"code_snippets[]":"Service code implementing or wiring prediction endpoints."}

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)
        task_input = {"code_snippets": _join_snippets(code_snippets)}
        system_prompt = (
            "You are an inference service deployment analyst. Detect frameworks exposing ML predictions "
            "and assess schema validation, health/readiness, error handling, batching/async, and signature/versioning. "
            "Return ONLY JSON."
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