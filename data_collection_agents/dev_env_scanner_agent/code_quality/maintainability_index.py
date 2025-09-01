# micro_agents/code_quality_agents.py
from typing import Any, Dict, List, Optional
from loguru import logger
from dev_env_scanner_agent.base_agent import BaseMicroAgent
from dev_env_scanner_agent.one_shot.registry import get_one_shot
from dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from dev_env_scanner_agent.logging_utils import timed

def _join_snippets(snippets: List[str]) -> str:
    parts = []
    for i, s in enumerate(snippets, start=1):
        parts.append(f"--- Snippet {i} ---\n{s}")
    return "\n\n".join(parts)

class MaintainabilityAgent(BaseMicroAgent):
    METRIC_ID = "code.maintainability_band"
    RUBRIC = (
        "Use maintainability/readability/design as joint evidence.\n"
        "Band 5: all ≥0.85 and consistent across files;\n"
        "Band 4: all ≥0.75 or two ≥0.80;\n"
        "Band 3: all ≥0.60 with mixed signals;\n"
        "Band 2: any <0.60 but some strengths present;\n"
        "Band 1: multiple <0.50 or major smells dominate."
    )
    INPUT_MEANINGS = {"code_snippets[]":"Source snippets for maintainability/readability/design signals."}

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)
        task_input = {"code_snippets": code_snippets}
        prompt = build_metric_prompt(
            rubric=self.RUBRIC, metric_id=self.METRIC_ID,
            input_key_meanings=self.INPUT_MEANINGS,
            task_input=task_input,
            example_input=ex["example_input"], example_output=ex["example_output"],
        )
        logger.debug(f"[{self.METRIC_ID}] prompt_len={len(prompt)}")
        with timed(f"metric.{self.METRIC_ID}"):
            with timed("LLM.call"):
                raw = self._call_llm(prompt, system_prompt="")
            out = self._parse_json_response(raw) or {}
        out.setdefault("metric_id", self.METRIC_ID)
        try:
            out["band"] = max(1, min(5, int(out.get("band", 3))))
        except Exception:
            out["band"] = 3
        out.setdefault("rationale","No rationale."); out.setdefault("flags",[]); out.setdefault("gaps",[])
        logger.info(f"[{self.METRIC_ID}] band={out['band']} rationale={out['rationale']}")
        if out["flags"]: logger.info(f"[{self.METRIC_ID}] flags={out['flags']}")
        if out["gaps"]: logger.info(f"[{self.METRIC_ID}] gaps={out['gaps']}")
        return out


