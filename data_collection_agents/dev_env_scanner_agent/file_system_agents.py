# micro_agents/file_system_agents.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from dev_env_scanner_agent.base_agent import BaseMicroAgent
from dev_env_scanner_agent.one_shot.registry import get_one_shot
from dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt


def _join_snippets(snippets: List[str]) -> str:
    parts = []
    for i, s in enumerate(snippets, start=1):
        parts.append(f"--- Snippet {i} ---\n{s}")
    return "\n\n".join(parts)


def _join_paths(paths: List[str]) -> str:
    parts = []
    for i, p in enumerate(paths, start=1):
        parts.append(f"--- File {i} ---\n{p}")
    return "\n\n".join(parts)


class TestDetectionAgent(BaseMicroAgent):
    """
    Micro-agent for detecting test files and testing practices.

    Produces keys compatible with the static pipeline:
      - test_file_count (int)
      - has_tests (bool)
      - has_test_coverage_report (bool)  [best-effort; defaults to False]
    Additional (nice to have):
      - test_frameworks (list[str])
      - test_coverage_estimate (float 0–1)
      - testing_quality (float 0–1)
    """

    def evaluate(
        self,
        code_snippets: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert testing analyst. Identify test files, "
            "frameworks (pytest/unittest/etc.), and estimate coverage. "
            "Respond ONLY with JSON."
        )

        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"test_file_count": <int>, "test_frameworks": ["<string>", "..."], '
            '"test_coverage_estimate": <0-1>, "testing_quality": <0-1>, '
            '"has_test_coverage_report": <true|false>}'
        )

        prompt = build_one_shot_prompt(
            system_preamble=system_prompt,
            response_format_description=response_format,
            task_input={"code_snippets": code_snippets},
            input_key_meanings=ex.get("input_key_meanings", {}),
            example_input=ex["example_input"],
            example_output=ex["example_output"],
        )

        response = self._call_llm(prompt, system_prompt)
        res = self._parse_json_response(response)

        test_count = int(res.get("test_file_count", 0))
        has_cov_report = bool(res.get("has_test_coverage_report", False))

        return {
            "test_file_count": test_count,
            "has_tests": test_count > 0,
            "has_test_coverage_report": has_cov_report,
            "test_frameworks": res.get("test_frameworks", []),
            "test_coverage_estimate": float(res.get("test_coverage_estimate", 0.0)),
            "testing_quality": float(res.get("testing_quality", 0.0)),
        }


class EnvironmentConfigAgent(BaseMicroAgent):
    """
    Micro-agent for detecting environment/dependency configuration files.

    Normalizes common file types to canonical keys used by your pipeline:
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

    def evaluate(
        self,
        file_paths: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a dependency management analyst. Identify dependency/"
            "environment files. Respond ONLY with JSON."
        )

        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"dependency_files": {"requirements.txt": <true|false>, "...": <true|false>}, '
            '"dependency_management_quality": <0-1>, '
            '"environment_consistency": <0-1>, '
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

        response = self._call_llm(prompt, system_prompt)
        res = self._parse_json_response(response)

        raw = res.get("dependency_files", {}) or {}
        out: Dict[str, Any] = {}
        for canon in self._CANONICAL_KEYS.values():
            out[canon] = False

        for key, present in raw.items():
            k = str(key).strip().lower()
            canon = self._CANONICAL_KEYS.get(k)
            if canon:
                out[canon] = bool(present)

        out.setdefault("has_requirements", False)
        out.setdefault("has_pipfile", False)
        out.setdefault("has_env_yml", False)

        out["dependency_management_quality"] = float(
            res.get("dependency_management_quality", 0.0)
        )
        out["environment_consistency"] = float(
            res.get("environment_consistency", 0.0)
        )
        out["dependency_best_practices"] = res.get("best_practices", [])
        return out


class CICDAgent(BaseMicroAgent):
    """
    Micro-agent for CI/CD configuration detection.

    Produces keys compatible with static pipeline:
      - ci_workflow_count (int)
      - has_ci (bool)
      - has_github_actions / has_gitlab_ci / has_jenkins (optional booleans)
    """

    def evaluate(
        self,
        file_paths: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a CI/CD analyst. Detect CI systems and workflows. "
            "Respond ONLY with JSON."
        )

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

        response = self._call_llm(prompt, system_prompt)
        res = self._parse_json_response(response)

        ci_files = res.get("ci_files", {}) or {}
        has_github = ci_files.get("github_actions", 0) > 0 or ci_files.get(
            "github", 0
        ) > 0
        has_gitlab = ci_files.get("gitlab_ci", 0) > 0 or ci_files.get(
            "gitlab", 0
        ) > 0
        has_jenkins = ci_files.get("jenkins", 0) > 0

        count = int(res.get("ci_workflow_count", 0))
        out = {
            "ci_workflow_count": count,
            "has_ci": count > 0 or has_github or has_gitlab or has_jenkins,
            "ci_quality": float(res.get("ci_quality", 0.0)),
            "deployment_automation": float(res.get("deployment_automation", 0.0)),
            "has_github_actions": bool(has_github),
            "has_gitlab_ci": bool(has_gitlab),
            "has_jenkins": bool(has_jenkins),
        }
        return out


class DeploymentAgent(BaseMicroAgent):
    """
    Micro-agent for deployment scripts/config detection.

    Produces keys compatible with static pipeline:
      - deploy_script_count (int)
      - has_deploy_scripts (bool)
    """

    def evaluate(
        self,
        file_paths: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a deployment analyst. Detect deploy scripts/configs. "
            "Respond ONLY with JSON."
        )

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

        response = self._call_llm(prompt, system_prompt)
        res = self._parse_json_response(response)

        count = int(res.get("deploy_script_count", 0))
        out = {
            "deploy_script_count": count,
            "has_deploy_scripts": count > 0,
            "deployment_automation": float(res.get("deployment_automation", 0.0)),
            "deployment_quality": float(res.get("deployment_quality", 0.0)),
        }

        deployment_files = res.get("deployment_files", {}) or {}
        for dtype, dcount in deployment_files.items():
            key = f"has_{str(dtype).strip().lower()}"
            out[key] = bool(dcount)

        return out


class ExperimentDetectionAgent(BaseMicroAgent):
    """
    Micro-agent for experiment directories and files.

    Produces:
      - experiment_folder_count (int)
      - has_experiments (bool)
    """

    def evaluate(
        self,
        file_paths: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are an experiment management analyst. Detect experiment dirs. "
            "Respond ONLY with JSON."
        )

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

        response = self._call_llm(prompt, system_prompt)
        res = self._parse_json_response(response)

        count = int(res.get("experiment_folder_count", 0))
        return {
            "experiment_folder_count": count,
            "has_experiments": count > 0,
            "experiment_dirs": res.get("experiment_dirs", []),
            "experiment_management": float(res.get("experiment_management", 0.0)),
            "reproducibility_analysis": res.get("reproducibility_analysis", []),
        }


class ProjectStructureAgent(BaseMicroAgent):
    """
    Micro-agent for overall project structure/organization.
    (Optional signal; not required by your current scoring.)
    """

    def evaluate(
        self,
        file_paths: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a project structure analyst. Assess organization and docs. "
            "Respond ONLY with JSON."
        )

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

        response = self._call_llm(prompt, system_prompt)
        res = self._parse_json_response(response)

        return {
            "structure_quality": float(res.get("structure_quality", 0.0)),
            "organization_patterns": res.get("organization_patterns", []),
            "documentation_quality": float(res.get("documentation_quality", 0.0)),
            "best_practices_adherence": float(
                res.get("best_practices_adherence", 0.0)
            ),
        }