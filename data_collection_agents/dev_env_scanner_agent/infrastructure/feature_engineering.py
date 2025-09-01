from __future__ import annotations
from typing import Any, Dict, List, Optional
from loguru import logger

from dev_env_scanner_agent.base_agent import BaseMicroAgent
from dev_env_scanner_agent.one_shot.registry import get_one_shot
from dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from dev_env_scanner_agent.logging_utils import timed

def _join_snippets(snippets: List[str]) -> str:
    return "\n\n".join([f"--- Snippet {i+1} ---\n{s}" for i, s in enumerate(snippets)])

class FeatureEngineeringAgent(BaseMicroAgent):
    """
    metric_id: infra.feature_engineering
    """

    METRIC_ID = "infra.feature_engineering"
    RUBRIC = (
        "Evaluate FE pipelines (sklearn pipelines/ColumnTransformer, featuretools, tsfresh, pandas pipelines) "
        "for reproducibility, persistence of fitted transformers, and automation/readiness for serving.\n"
        "5: Well-structured pipeline with persistable transformers and parity guarantees.\n"
        "4: Solid pipeline usage; persistence/parity partially evidenced.\n"
        "3: Ad-hoc transforms; reproducibility unclear.\n"
        "2: Manual transforms sprinkled across code; risky for serving parity.\n"
        "1: No feature engineering structure."
    )
    INPUT_MEANINGS = {"code_snippets[]":"Preprocessing/transform code used for features."}

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)
        task_input = {"code_snippets": _join_snippets(code_snippets)}
        system_prompt = (
            "You are a feature engineering analyst. Detect FE patterns and evaluate "
            "persistence of fitted transformers and train/serve parity. Return ONLY JSON."
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