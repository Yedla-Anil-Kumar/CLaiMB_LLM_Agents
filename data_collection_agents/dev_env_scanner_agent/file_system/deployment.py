from __future__ import annotations
from typing import Any, Dict, List, Optional
from dev_env_scanner_agent.base_agent import BaseMicroAgent
from dev_env_scanner_agent.one_shot.registry import get_one_shot
from dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt

class DeploymentAgent(BaseMicroAgent):
    """
    Detect deploy scripts/configs.
    Returns:
      - deploy_script_count, has_deploy_scripts
      - deployment_automation, deployment_quality
      - has_<type> flags (docker/kubernetes/helm/etc.)
    """
    def evaluate(self, file_paths: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = "You are a deployment analyst. Detect deploy scripts/configs. Respond ONLY with JSON."
        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"deployment_files": {"docker": <int>, "kubernetes": <int>, "helm": <int>, "...": <int>}, '
            '"deploy_script_count": <int>, "deployment_automation": <0-1>, "deployment_quality": <0-1>}'
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

        count = int(res.get("deploy_script_count", 0))
        out: Dict[str, Any] = {
            "deploy_script_count": count,
            "has_deploy_scripts": count > 0,
            "deployment_automation": float(res.get("deployment_automation", 0.0)),
            "deployment_quality": float(res.get("deployment_quality", 0.0)),
        }
        for dtype, dcount in (res.get("deployment_files", {}) or {}).items():
            out[f"has_{str(dtype).strip().lower()}"] = bool(dcount)
        return out