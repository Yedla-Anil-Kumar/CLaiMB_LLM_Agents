from __future__ import annotations
from typing import Any, Dict, List, Optional
from loguru import logger

from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from data_collection_agents.dev_env_scanner_agent.logging_utils import timed

def _join_snippets(snippets: List[str]) -> str:
    return "\n\n".join([f"--- Snippet {i+1} ---\n{s}" for i, s in enumerate(snippets)])

class SecurityAgent(BaseMicroAgent):
    """
    metric_id: infra.security_hygiene
    """

    METRIC_ID = "infra.security_hygiene"
    RUBRIC = (
        "Evaluate code for secrets exposure, weak auth/crypto, unsafe validation, and missing security controls.\n"
        "5: No exposures; strong policies and patterns enforced; secrets managed; input validation solid.\n"
        "4: Minor gaps with controls present (e.g., policy doc missing or a rare exception).\n"
        "3: Some issues (weak validation, occasional hardcoded values) without systemic failures.\n"
        "2: Material risks (hardcoded secrets, weak password policy) and limited mitigations.\n"
        "1: Severe exposures or negligence."
    )
    INPUT_MEANINGS = {"code_snippets[]":"Any code possibly containing secrets or security-sensitive paths."}

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)
        task_input = {"code_snippets": _join_snippets(code_snippets)}
        system_prompt = (
            "You are a security hygiene analyst. Look for secret exposure, weak crypto, lax validation, "
            "and unsafe patterns. Return ONLY JSON."
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
        try: out["band"] = max(1, min(5, int(out.get("band", 3))))
        except Exception: out["band"] = 3
        out.setdefault("rationale","No rationale."); out.setdefault("flags",[]); out.setdefault("gaps",[])
        logger.info(f"[{self.METRIC_ID}] band={out['band']} rationale={out['rationale']}")
        return out