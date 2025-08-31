# micro_agents/code_quality_agents.py
from typing import Any, Dict, List, Optional

from dev_env_scanner_agent.base_agent import BaseMicroAgent
from dev_env_scanner_agent.one_shot.registry import get_one_shot
from dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt


def _join_snippets(snippets: List[str]) -> str:
    parts = []
    for i, s in enumerate(snippets, start=1):
        parts.append(f"--- Snippet {i} ---\n{s}")
    return "\n\n".join(parts)


class CyclomaticComplexityAgent(BaseMicroAgent):
    """
    Micro-agent for estimating cyclomatic complexity using the LLM.

    Output keys map to the static pipeline:
      - avg_cyclomatic_complexity (float)
      - complexity_distribution (dict)
      - complexity_recommendations (list[str])
    """

    def evaluate(
        self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a strict code-quality analyst. Estimate cyclomatic "
            "complexity from code. Respond ONLY with JSON."
        )

        # One-shot examples (externalized)
        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"avg_complexity": <number>, '
            '"complexity_distribution": {"low": <int>, "medium": <int>, "high": <int>, "very_high": <int>}, '
            '"recommendations": ["<string>", "..."]}'
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
        result = self._parse_json_response(response)

        return {
            "avg_cyclomatic_complexity": float(result.get("avg_complexity", 0.0)),
            "complexity_distribution": result.get("complexity_distribution", {}),
            "complexity_recommendations": result.get("recommendations", []),
        }


class MaintainabilityAgent(BaseMicroAgent):
    """
    Micro-agent for maintainability/readability/design. Matches existing fields:
      - avg_maintainability_index (0–1)
    Adds:
      - readability_score (0–1)
      - design_quality  (0–1)
      - maintainability_suggestions (list[str])
    """

    def evaluate(
        self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert maintainability reviewer. Score readability, "
            "design, and overall maintainability on 0–1. Respond ONLY with JSON."
        )

        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"maintainability_score": <0-1>, "readability_score": <0-1>, '
            '"design_quality": <0-1>, "improvement_suggestions": ["<string>", "..."]}'
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
        result = self._parse_json_response(response)

        return {
            "avg_maintainability_index": float(
                result.get("maintainability_score", 0.0)
            ),
            "readability_score": float(result.get("readability_score", 0.0)),
            "design_quality": float(result.get("design_quality", 0.0)),
            "maintainability_suggestions": result.get("improvement_suggestions", []),
        }


class DocstringCoverageAgent(BaseMicroAgent):
    """
    Micro-agent for docstring presence/quality. Matches existing field:
      - docstring_coverage (0–1)
    Adds:
      - docstring_quality (0–1)
      - missing_documentation (list[str])
      - documentation_suggestions (list[str])
    """

    def evaluate(
        self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a documentation analyst. Estimate docstring coverage and "
            "quality. Respond ONLY with JSON."
        )

        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"docstring_coverage": <0-1>, "docstring_quality": <0-1>, '
            '"missing_documentation": ["<symbol>", "..."], '
            '"quality_improvements": ["<string>", "..."]}'
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
        result = self._parse_json_response(response)

        return {
            "docstring_coverage": float(result.get("docstring_coverage", 0.0)),
            "docstring_quality": float(result.get("docstring_quality", 0.0)),
            "missing_documentation": result.get("missing_documentation", []),
            "documentation_suggestions": result.get("quality_improvements", []),
        }


class NestedLoopsAgent(BaseMicroAgent):
    """
    Micro-agent for nested loops. Matches the static field:
      - nested_loop_files (int)  — aggregated by orchestrator
    Adds:
      - max_nesting_depth (int)
      - performance_concerns (list[str])
      - loop_optimization_suggestions (list[str])

    NOTE: Orchestrator should call this per file (one snippet per call) and
    then count files with nested loops when aggregating.
    """

    def evaluate(
        self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a loop-complexity analyst. Detect nested loops and "
            "report depth/risks. Respond ONLY with JSON."
        )

        ex = get_one_shot(self.__class__.__name__)
        response_format = (
            '{"has_nested_loops": <true|false>, "max_nesting_depth": <int>, '
            '"performance_concerns": ["<string>", "..."], '
            '"optimization_suggestions": ["<string>", "..."]}'
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
        result = self._parse_json_response(response)

        has_nested = bool(result.get("has_nested_loops", False))
        return {
            "has_nested_loops": has_nested,
            "max_nesting_depth": int(result.get("max_nesting_depth", 0)),
            "performance_concerns": result.get("performance_concerns", []),
            "loop_optimization_suggestions": result.get("optimization_suggestions", []),
        }