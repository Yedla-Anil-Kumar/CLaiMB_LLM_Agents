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

# class CyclomaticComplexityAgent(BaseMicroAgent):
#     """
#     New behavior: returns a single metric JSON with band/rationale/flags/gaps.
#     metric_id: code.cyclomatic_complexity_band
#     """

#     METRIC_ID = "code.cyclomatic_complexity_band"
#     RUBRIC = (
#         "Use avg_complexity and distribution across low/med/high/very_high.\n"
#         "Band 5: avg ≤ 5 and ≤10% functions high/very_high;\n"
#         "Band 4: avg ≤ 7 and ≤20% high/very_high;\n"
#         "Band 3: avg ≤ 10 or 21–35% high/very_high;\n"
#         "Band 2: avg ≤ 12 or 36–50% high/very_high;\n"
#         "Band 1: avg > 12 or widespread very_high complexity or evidence missing."
#     )

#     INPUT_MEANINGS = {
#         "code_snippets[]": "Source snippets to infer cyclomatic complexity distribution.",
#     }

#     def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
      
#         ex = get_one_shot(self.__class__.__name__)
#         task_input = {"code_snippets": _join_snippets(code_snippets)}

#         prompt = build_metric_prompt(
#             rubric=self.RUBRIC,
#             metric_id=self.METRIC_ID,
#             input_key_meanings=self.INPUT_MEANINGS,
#             task_input=task_input,
#             example_input=ex["example_input"],
#             example_output=ex["example_output"],  # should be in the unified JSON shape
#         )

#         logger.debug(f"[{self.METRIC_ID}] prompt_len={len(prompt)}")

#         with timed(f"metric.{self.METRIC_ID}"):
#             with timed("LLM.call"):
#                 raw = self._call_llm(prompt, system_prompt="")
#             out = self._parse_json_response(raw) or {}

#         # Defensive normalization
#         out.setdefault("metric_id", self.METRIC_ID)
#         try:
#             out["band"] = max(1, min(5, int(out.get("band", 3))))
#         except Exception:
#             out["band"] = 3
#         out.setdefault("rationale", "No rationale.")
#         out.setdefault("flags", [])
#         out.setdefault("gaps", [])

#         logger.info(f"[{self.METRIC_ID}] band={out['band']} rationale={out['rationale']}")
#         if out["flags"]:
#             logger.info(f"[{self.METRIC_ID}] flags={out['flags']}")
#         if out["gaps"]:
#             logger.info(f"[{self.METRIC_ID}] gaps={out['gaps']}")

#         return out
    
class CyclomaticComplexityAgent(BaseMicroAgent):
    METRIC_ID = "code.cyclomatic_complexity_band"
    RUBRIC = (
        "Use avg_complexity and distribution across low/med/high/very_high.\n"
        "Band 5: avg ≤ 5 and ≤10% functions high/very_high;\n"
        "Band 4: avg ≤ 7 and ≤20% high/very_high;\n"
        "Band 3: avg ≤ 10 or 21–35% high/very_high;\n"
        "Band 2: avg ≤ 12 or 36–50% high/very_high;\n"
        "Band 1: avg > 12 or widespread very_high complexity or evidence missing."
    )
    INPUT_MEANINGS = {
        "code_snippets[]": "Source snippets to infer cyclomatic complexity distribution.",
    }

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)

        # IMPORTANT: pass a LIST (matches example_input shape)
        task_input = {"code_snippets": code_snippets}

        prompt = build_metric_prompt(
            rubric=self.RUBRIC,
            metric_id=self.METRIC_ID,
            input_key_meanings=self.INPUT_MEANINGS,
            task_input=task_input,
            example_input=ex["example_input"],
            example_output=ex["example_output"],
        )

        logger.debug(f"[{self.METRIC_ID}] prompt_len={len(prompt)}")

        with timed(f"metric.{self.METRIC_ID}"):
            with timed("LLM.call"):
                raw = self._call_llm(prompt, system_prompt="")
            out = self._parse_json_response(raw) or {}

        # Defensive normalization
        out.setdefault("metric_id", self.METRIC_ID)
        try:
            out["band"] = max(1, min(5, int(out.get("band", 3))))
        except Exception:
            out["band"] = 3
        out.setdefault("rationale", "No rationale.")
        out.setdefault("flags", [])
        out.setdefault("gaps", [])

        logger.info(f"[{self.METRIC_ID}] band={out['band']} rationale={out['rationale']}")
        if out["flags"]:
            logger.info(f"[{self.METRIC_ID}] flags={out['flags']}")
        if out["gaps"]:
            logger.info(f"[{self.METRIC_ID}] gaps={out['gaps']}")

        return out