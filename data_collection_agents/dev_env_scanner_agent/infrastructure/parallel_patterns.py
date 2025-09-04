from __future__ import annotations
from typing import Any, Dict, List, Optional
from loguru import logger

from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from data_collection_agents.dev_env_scanner_agent.logging_utils import timed

def _join_snippets(snippets: List[str]) -> str:
    return "\n\n".join([f"--- Snippet {i+1} ---\n{s}" for i, s in enumerate(snippets)])

class ParallelPatternsAgent(BaseMicroAgent):
    """
    Returns a single metric JSON with band/rationale/flags/gaps.
    metric_id: infra.parallel_patterns
    """

    METRIC_ID = "infra.parallel_patterns"
    RUBRIC = (
        "Grade explicit concurrency/parallelism patterns (threading/multiprocessing/"
        "concurrent.futures/asyncio/Ray) and operational safety (pooling, back-pressure, "
        "timeouts, graceful shutdown).\n"
        "5: Correct pattern for workload (IO vs CPU) with pooling, bounded queues, timeouts, "
        "graceful shutdown, and metrics.\n"
        "4: Appropriate pattern with minor gaps (e.g., session reuse unclear or no back-pressure).\n"
        "3: Pattern used but important safety pieces missing (unbounded fan-out, no timeouts).\n"
        "2: Misapplied pattern (e.g., threads for heavy CPU) or frequent anti-patterns.\n"
        "1: Dangerous patterns (blocking in event loop, global shared state races) or no evidence."
    )
    INPUT_MEANINGS = {"code_snippets[]": "Python code where concurrency/parallelism might appear."}

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)
        task_input = {"code_snippets": _join_snippets(code_snippets)}
        system_prompt = (
            "You are a parallel computing reviewer. Identify explicit concurrency/parallelism "
            "patterns in Python code (threading, multiprocessing, concurrent.futures, asyncio, Ray). "
            "Check pool sizing, back-pressure, timeouts, shutdown, and whether the choice matches IO/CPU workloads. "
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