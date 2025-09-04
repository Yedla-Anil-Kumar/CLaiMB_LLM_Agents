from __future__ import annotations
from typing import Any, Dict, List, Optional
from loguru import logger

from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from data_collection_agents.dev_env_scanner_agent.logging_utils import timed

def _join_snippets(snippets: List[str]) -> str:
    return "\n\n".join([f"--- Snippet {i+1} ---\n{s}" for i, s in enumerate(snippets)])

class ModelExportAgent(BaseMicroAgent):
    """
    metric_id: infra.model_export
    """

    METRIC_ID = "infra.model_export"
    RUBRIC = (
        "Evaluate model export/serialization (torch.save, joblib, pickle, ONNX, TF SavedModel) "
        "and completeness (versioning, metadata, model card, signatures, artifacts).\n"
        "5: Standardized export with versioned path, signature, metadata/model card, and integrity checks.\n"
        "4: Reliable export with minor metadata/signature gaps.\n"
        "3: Ad-hoc export, minimal metadata.\n"
        "2: Risky methods or missing reproducibility details.\n"
        "1: No evidence of model export."
    )
    INPUT_MEANINGS = {"code_snippets[]":"Snippets showing training completion and persistence/serialization."}

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)
        task_input = {"code_snippets": _join_snippets(code_snippets)}
        system_prompt = (
            "You are a model export/serialization reviewer. Identify persistence methods and check for "
            "versioning, signatures, metadata, and model cards. Return ONLY JSON."
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