from __future__ import annotations
from typing import Any, Dict, List, Optional
from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt

class ExperimentDetectionAgent(BaseMicroAgent):
    """
    Detect experiment directories/files.
    Returns:
      - experiment_folder_count, has_experiments
      - experiment_dirs, experiment_management, reproducibility_analysis
    """
    def evaluate(self, file_paths: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = "You are an experiment management analyst. Detect experiment dirs. Respond ONLY with JSON."
        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"experiment_dirs": ["<dir>", "..."], "experiment_folder_count": <int>, '
            '"experiment_management": <0-1>, "reproducibility_analysis": ["<string>", "..."]}'
        )
        prompt = build_one_shot_prompt(
            system_preamble=system_prompt,
            response_format_description=response_format,
            task_input={"file_paths": file_paths},
            input_key_meanings=ex.get("input_key_meanings", {}),
            example_input=ex["example_input"],
            example_output=ex["example_output"],
        )
        res = self._parse_json_response(self._call_llm(prompt, system_prompt))
        count = int(res.get("experiment_folder_count", 0))
        return {
            "experiment_folder_count": count,
            "has_experiments": count > 0,
            "experiment_dirs": res.get("experiment_dirs", []),
            "experiment_management": float(res.get("experiment_management", 0.0)),
            "reproducibility_analysis": res.get("reproducibility_analysis", []),
        }