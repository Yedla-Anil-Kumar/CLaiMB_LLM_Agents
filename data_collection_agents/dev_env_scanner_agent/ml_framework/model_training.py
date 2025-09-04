from __future__ import annotations
from typing import Any, Dict, List, Optional

from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from data_collection_agents.dev_env_scanner_agent.logging_utils import timed


def _join_snippets(snippets: List[str]) -> str:
    return "\n\n".join(f"--- Snippet {i} ---\n{s}" for i, s in enumerate(snippets, 1))


class ModelTrainingAgent(BaseMicroAgent):
    METRIC_ID = "ml.training_practice"
    RUBRIC = (
        "Evaluate training entrypoints, config-driven design, reproducibility.\n"
        "Band 5: Config-driven, seeds/env captured, resume/checkpoints, failure recovery;\n"
        "Band 4: Clear entrypoint and configs; some reproducibility hooks;\n"
        "Band 3: Entrypoints present but ad-hoc configs; few hooks;\n"
        "Band 2: Script sprawl; no configs or checkpoints;\n"
        "Band 1: No credible training infrastructure."
    )
    INPUT_MEANINGS = {"code_snippets[]": "Entrypoint scripts/classes that kick off training."}

    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ex = get_one_shot(self.__class__.__name__)
        task_input = {"code_snippets": _join_snippets(code_snippets)}
        prompt = build_metric_prompt(
            rubric=self.RUBRIC,
            metric_id=self.METRIC_ID,
            input_key_meanings=self.INPUT_MEANINGS,
            task_input=task_input,
            example_input=ex["example_input"],
            example_output=ex["example_output"],
        )
        with timed(f"metric.{self.METRIC_ID}"):
            raw = self._call_llm(prompt, system_prompt="")
            out = self._parse_json_response(raw) or {}
        out.setdefault("metric_id", self.METRIC_ID)
        try:
            out["band"] = max(1, min(5, int(out.get("band", 3))))
        except Exception:
            out["band"] = 3
        out.setdefault("rationale", "No rationale.")
        out.setdefault("flags", [])
        out.setdefault("gaps", [])
        return out