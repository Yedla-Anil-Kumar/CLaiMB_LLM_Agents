from __future__ import annotations
from typing import Any, Dict, List, Optional
from dev_env_scanner_agent.base_agent import BaseMicroAgent
from dev_env_scanner_agent.one_shot.registry import get_one_shot
from dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt

class EnvironmentConfigAgent(BaseMicroAgent):
    """
    Detect dependency/environment files.
    Returns canonical flags:
      - has_requirements, has_pipfile, has_env_yml, has_pyproject_toml, has_setup_py
    """
    _CANONICAL_KEYS = {
        "requirements.txt": "has_requirements",
        "requirements": "has_requirements",
        "pipfile": "has_pipfile",
        "environment.yml": "has_env_yml",
        "environment.yaml": "has_env_yml",
        "conda.yml": "has_env_yml",
        "pyproject.toml": "has_pyproject_toml",
        "setup.py": "has_setup_py",
    }

    def evaluate(self, file_paths: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = ("You are a dependency management analyst. Identify dependency/"
                         "environment files. Respond ONLY with JSON.")
        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"dependency_files": {"requirements.txt": <true|false>, "...": <true|false>}, '
            '"dependency_management_quality": <0-1>, "environment_consistency": <0-1>, '
            '"best_practices": ["<string>", "..."]}'
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

        raw = res.get("dependency_files", {}) or {}
        out: Dict[str, Any] = {v: False for v in self._CANONICAL_KEYS.values()}
        for key, present in raw.items():
            canon = self._CANONICAL_KEYS.get(str(key).strip().lower())
            if canon:
                out[canon] = bool(present)
        out.setdefault("has_requirements", False)
        out.setdefault("has_pipfile", False)
        out.setdefault("has_env_yml", False)
        out["dependency_management_quality"] = float(res.get("dependency_management_quality", 0.0))
        out["environment_consistency"] = float(res.get("environment_consistency", 0.0))
        out["dependency_best_practices"] = res.get("best_practices", [])
        return out