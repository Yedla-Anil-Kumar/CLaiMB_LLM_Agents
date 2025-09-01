from __future__ import annotations
from typing import Any, Dict, List, Optional
from dev_env_scanner_agent.base_agent import BaseMicroAgent
from dev_env_scanner_agent.one_shot.registry import get_one_shot
from dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt

class CICDAgent(BaseMicroAgent):
    """
    Detect CI systems and workflows.
    Returns:
      - ci_workflow_count, has_ci, ci_quality, deployment_automation
      - has_github_actions, has_gitlab_ci, has_jenkins
    """
    def evaluate(self, file_paths: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = "You are a CI/CD analyst. Detect CI systems and workflows. Respond ONLY with JSON."
        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"ci_files": {"github_actions": <int>, "gitlab_ci": <int>, "jenkins": <int>}, '
            '"ci_workflow_count": <int>, "ci_quality": <0-1>, "deployment_automation": <0-1>}'
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

        ci_files = res.get("ci_files", {}) or {}
        has_github = ci_files.get("github_actions", 0) > 0 or ci_files.get("github", 0) > 0
        has_gitlab = ci_files.get("gitlab_ci", 0) > 0 or ci_files.get("gitlab", 0) > 0
        has_jenkins = ci_files.get("jenkins", 0) > 0

        count = int(res.get("ci_workflow_count", 0))
        return {
            "ci_workflow_count": count,
            "has_ci": count > 0 or has_github or has_gitlab or has_jenkins,
            "ci_quality": float(res.get("ci_quality", 0.0)),
            "deployment_automation": float(res.get("deployment_automation", 0.0)),
            "has_github_actions": bool(has_github),
            "has_gitlab_ci": bool(has_gitlab),
            "has_jenkins": bool(has_jenkins),
        }