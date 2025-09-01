from __future__ import annotations
from typing import Any, Dict, List, Optional
from dev_env_scanner_agent.base_agent import BaseMicroAgent
from dev_env_scanner_agent.one_shot.registry import get_one_shot
from dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt

class TestDetectionAgent(BaseMicroAgent):
    """
    Detect test files and testing practices.
    Returns:
      - test_file_count (int)
      - has_tests (bool)
      - has_test_coverage_report (bool)
      - test_frameworks (list[str])
      - test_coverage_estimate (0–1)
      - testing_quality (0–1)
    """
    def evaluate(self, code_snippets: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = ("You are an expert testing analyst. Identify test files, "
                         "frameworks (pytest/unittest/etc.), and estimate coverage. "
                         "Respond ONLY with JSON.")
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
        res = self._parse_json_response(self._call_llm(prompt, system_prompt))
        test_count = int(res.get("test_file_count", 0))
        return {
            "test_file_count": test_count,
            "has_tests": test_count > 0,
            "has_test_coverage_report": bool(res.get("has_test_coverage_report", False)),
            "test_frameworks": res.get("test_frameworks", []),
            "test_coverage_estimate": float(res.get("test_coverage_estimate", 0.0)),
            "testing_quality": float(res.get("testing_quality", 0.0)),
        }