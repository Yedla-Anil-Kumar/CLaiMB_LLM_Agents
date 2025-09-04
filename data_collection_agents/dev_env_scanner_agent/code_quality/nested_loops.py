# micro_agents/code_quality_agents.py
from typing import Any, Dict, List, Optional
from loguru import logger
from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from data_collection_agents.dev_env_scanner_agent.logging_utils import timed

def _join_snippets(snippets: List[str]) -> str:
    parts = []
    for i, s in enumerate(snippets, start=1):
        parts.append(f"--- Snippet {i} ---\n{s}")
    return "\n\n".join(parts)

class NestedLoopsAgent(BaseMicroAgent):
    METRIC_ID = "code.nested_loops_band"
    RUBRIC = (
        "Consider existence + depth + hotspots + alternatives.\n"
        "Band 5: no problematic nesting (depth ≤2) or refactored hotspots;\n"
        "Band 4: some nesting (depth ≤3) with mitigations and tests;\n"
        "Band 3: notable nesting (depth 3–4) with partial mitigations;\n"
        "Band 2: frequent deep nesting (depth ≥4) and limited tests;\n"
        "Band 1: widespread deep nesting causing performance/complexity risks."
    )
    INPUT_MEANINGS = {"code_snippets[]":"Source snippets where loops and nesting depth can be inferred."}

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
        try: out["band"] = max(1, min(5, int(out.get("band", 3))))
        except Exception: out["band"] = 3
        out.setdefault("rationale","No rationale."); out.setdefault("flags",[]); out.setdefault("gaps",[])
        logger.info(f"[{self.METRIC_ID}] band={out['band']} rationale={out['rationale']}")
        if out["flags"]: logger.info(f"[{self.METRIC_ID}] flags={out['flags']}")
        if out["gaps"]: logger.info(f"[{self.METRIC_ID}] gaps={out['gaps']}")
        return out