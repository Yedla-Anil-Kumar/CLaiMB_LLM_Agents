from __future__ import annotations
from typing import Any, Dict, List, Optional

from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.prompting import build_metric_prompt
from data_collection_agents.dev_env_scanner_agent.logging_utils import timed


def _join_snippets(snippets: List[str]) -> str:
    return "\n\n".join(f"--- Snippet {i} ---\n{s}" for i, s in enumerate(snippets, 1))


class ExperimentTrackingAgent(BaseMicroAgent):
    METRIC_ID = "ml.experiment_tracking"
    RUBRIC = (
        "Evaluate tracking of params/metrics/artifacts/signature/lineage.\n"
        "Band 5: Consistent runs with artifacts, signatures, lineage, dashboards;\n"
        "Band 4: Params/metrics logged, artifacts frequent, signature sometimes;\n"
        "Band 3: Basic params/metrics only; artifacts/signature inconsistent;\n"
        "Band 2: Ad-hoc logging with gaps; little structure;\n"
        "Band 1: No credible tracking or evidence missing."
    )
    INPUT_MEANINGS = {"code_snippets[]": "Training code that may log with MLflow/W&B/ClearML."}

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