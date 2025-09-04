from __future__ import annotations
from typing import Any, Dict, List, Optional
from data_collection_agents.dev_env_scanner_agent.base_agent import BaseMicroAgent
from data_collection_agents.dev_env_scanner_agent.one_shot.registry import get_one_shot
from data_collection_agents.dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt

class ProjectStructureAgent(BaseMicroAgent):
    """
    Assess organization/documentation signals.
    Optional metric; not required by current scoring.
    """
    def evaluate(self, file_paths: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = "You are a project structure analyst. Assess organization and docs. Respond ONLY with JSON."
        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"structure_quality": <0-1>, "organization_patterns": ["<string>", "..."], '
            '"documentation_quality": <0-1>, "best_practices_adherence": <0-1>}'
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
        return {
            "structure_quality": float(res.get("structure_quality", 0.0)),
            "organization_patterns": res.get("organization_patterns", []),
            "documentation_quality": float(res.get("documentation_quality", 0.0)),
            "best_practices_adherence": float(res.get("best_practices_adherence", 0.0)),
        }