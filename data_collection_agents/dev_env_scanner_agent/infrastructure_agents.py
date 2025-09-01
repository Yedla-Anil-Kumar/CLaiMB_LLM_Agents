# # micro_agents/infrastructure_agents.py
# from typing import Any, Dict, List, Optional
# from dev_env_scanner_agent.base_agent import BaseMicroAgent
# from dev_env_scanner_agent.one_shot.registry import get_one_shot
# from dev_env_scanner_agent.one_shot.utils import build_one_shot_prompt


# class ParallelPatternsAgent(BaseMicroAgent):
#     """Micro-agent for detecting parallel processing patterns."""

#     def evaluate(
#         self, code_snippets: List[str], context: Optional[Dict] = None
#     ) -> Dict[str, Any]:
#         system_prompt = (
#             "You are an expert parallel computing analyst. Detect and analyze "
#             "parallel processing patterns in the provided code snippets. "
#             "Respond ONLY with JSON."
#         )

#         ex = get_one_shot(self.__class__.__name__)
#         response_format = (
#             '{"parallel_tools": {"threading": <bool>, "multiprocessing": <bool>, '
#             '"concurrent.futures": <bool>, "...": <bool>}, '
#             '"parallel_patterns": ["<string>", "..."], '
#             '"scalability_analysis": "<string>", '
#             '"optimization_opportunities": ["<string>", "..."]}'
#         )

#         prompt = build_one_shot_prompt(
#             system_preamble=system_prompt,
#             response_format_description=response_format,
#             task_input={"code_snippets": code_snippets},
#             input_key_meanings=ex.get("input_key_meanings", {}),
#             example_input=ex["example_input"],
#             example_output=ex["example_output"],
#         )

#         response = self._call_llm(prompt, system_prompt)
#         result = self._parse_json_response(response)

#         parallel_tools = result.get("parallel_tools", {})
#         return {f"uses_{tool}": usage for tool, usage in parallel_tools.items()}


# class InferenceEndpointAgent(BaseMicroAgent):
#     """Micro-agent for detecting inference endpoint implementations."""

#     def evaluate(
#         self, code_snippets: List[str], context: Optional[Dict] = None
#     ) -> Dict[str, Any]:
#         system_prompt = (
#             "You are an expert ML deployment analyst. Detect and analyze inference "
#             "endpoint implementations. Respond ONLY with JSON."
#         )

#         ex = get_one_shot(self.__class__.__name__)
#         response_format = (
#             '{"inference_frameworks": {"fastapi": <bool>, "flask": <bool>, "streamlit": <bool>}, '
#             '"serving_patterns": ["<string>", "..."], '
#             '"deployment_quality": <0-1>, '
#             '"scalability_considerations": ["<string>", "..."]}'
#         )

#         prompt = build_one_shot_prompt(
#             system_preamble=system_prompt,
#             response_format_description=response_format,
#             task_input={"code_snippets": code_snippets},
#             input_key_meanings=ex.get("input_key_meanings", {}),
#             example_input=ex["example_input"],
#             example_output=ex["example_output"],
#         )

#         response = self._call_llm(prompt, system_prompt)
#         result = self._parse_json_response(response)

#         inference_frameworks = result.get("inference_frameworks", {})
#         return {f"uses_{tool}": usage for tool, usage in inference_frameworks.items()}


# class ModelExportAgent(BaseMicroAgent):
#     """Micro-agent for detecting model export and serialization patterns."""

#     def evaluate(
#         self, code_snippets: List[str], context: Optional[Dict] = None
#     ) -> Dict[str, Any]:
#         system_prompt = (
#             "You are an expert model deployment analyst. Detect and analyze model "
#             "export and serialization patterns. Respond ONLY with JSON."
#         )

#         ex = get_one_shot(self.__class__.__name__)
#         response_format = (
#             '{"export_patterns": {"torch.save": <bool>, "joblib.dump": <bool>, "onnx": <bool>}, '
#             '"model_formats": ["<string>", "..."], '
#             '"export_quality": <0-1>, '
#             '"deployment_readiness": "<string>"}'
#         )

#         prompt = build_one_shot_prompt(
#             system_preamble=system_prompt,
#             response_format_description=response_format,
#             task_input={"code_snippets": code_snippets},
#             input_key_meanings=ex.get("input_key_meanings", {}),
#             example_input=ex["example_input"],
#             example_output=ex["example_output"],
#         )

#         response = self._call_llm(prompt, system_prompt)
#         result = self._parse_json_response(response)

#         export_patterns = result.get("export_patterns", {})
#         return {f"exports_{method}": usage for method, usage in export_patterns.items()}


# class DataPipelineAgent(BaseMicroAgent):
#     """Micro-agent for detecting data pipeline configurations."""

#     def evaluate(
#         self, code_snippets: List[str], context: Optional[Dict] = None
#     ) -> Dict[str, Any]:
#         system_prompt = (
#             "You are an expert data pipeline analyst. Detect and analyze data pipeline "
#             "configurations and tools. Respond ONLY with JSON."
#         )

#         ex = get_one_shot(self.__class__.__name__)
#         response_format = (
#             '{"pipeline_tools": {"airflow": <bool>, "prefect": <bool>, "luigi": <bool>, "argo": <bool>, "kedro": <bool>}, '
#             '"pipeline_patterns": ["<string>", "..."], '
#             '"pipeline_quality": <0-1>, '
#             '"orchestration_approach": "<string>"}'
#         )

#         prompt = build_one_shot_prompt(
#             system_preamble=system_prompt,
#             response_format_description=response_format,
#             task_input={"code_snippets": code_snippets},
#             input_key_meanings=ex.get("input_key_meanings", {}),
#             example_input=ex["example_input"],
#             example_output=ex["example_output"],
#         )

#         response = self._call_llm(prompt, system_prompt)
#         result = self._parse_json_response(response)

#         pipeline_tools = result.get("pipeline_tools", {})
#         return {f"has_{tool}": usage for tool, usage in pipeline_tools.items()}


# class FeatureEngineeringAgent(BaseMicroAgent):
#     """Micro-agent for detecting feature engineering patterns."""

#     def evaluate(
#         self, code_snippets: List[str], context: Optional[Dict] = None
#     ) -> Dict[str, Any]:
#         system_prompt = (
#             "You are an expert feature engineering analyst. Detect and analyze feature "
#             "engineering patterns and tools. Respond ONLY with JSON."
#         )

#         ex = get_one_shot(self.__class__.__name__)
#         response_format = (
#             '{"feature_tools": {"sklearn.preprocessing": <bool>, "featuretools": <bool>, "tsfresh": <bool>}, '
#             '"feature_patterns": ["<string>", "..."], '
#             '"feature_quality": <0-1>, '
#             '"automation_level": "<string>"}'
#         )

#         prompt = build_one_shot_prompt(
#             system_preamble=system_prompt,
#             response_format_description=response_format,
#             task_input={"code_snippets": code_snippets},
#             input_key_meanings=ex.get("input_key_meanings", {}),
#             example_input=ex["example_input"],
#             example_output=ex["example_output"],
#         )

#         response = self._call_llm(prompt, system_prompt)
#         result = self._parse_json_response(response)

#         feature_tools = result.get("feature_tools", {})
#         return {
#             f"uses_{tool.replace('.', '_')}": usage
#             for tool, usage in feature_tools.items()
#         }


# class SecurityAgent(BaseMicroAgent):
#     """Micro-agent for detecting security vulnerabilities and best practices."""

#     def evaluate(
#         self, code_snippets: List[str], context: Optional[Dict] = None
#     ) -> Dict[str, Any]:
#         system_prompt = (
#             "You are an expert security analyst. Detect and analyze security vulnerabilities "
#             "and best practices. Respond ONLY with JSON."
#         )

#         ex = get_one_shot(self.__class__.__name__)
#         response_format = (
#             '{"security_issues": ["<string>", "..."], '
#             '"secret_exposure": "<string>", '
#             '"security_score": <0-1>, '
#             '"recommendations": ["<string>", "..."]}'
#         )

#         prompt = build_one_shot_prompt(
#             system_preamble=system_prompt,
#             response_format_description=response_format,
#             task_input={"code_snippets": code_snippets},
#             input_key_meanings=ex.get("input_key_meanings", {}),
#             example_input=ex["example_input"],
#             example_output=ex["example_output"],
#         )

#         response = self._call_llm(prompt, system_prompt)
#         result = self._parse_json_response(response)

#         return {
#             "has_secrets": len(result.get("security_issues", [])) > 0,
#             "security_score": result.get("security_score", 0.0),
#             "security_issues": result.get("security_issues", []),
#             "security_recommendations": result.get("recommendations", []),
#         }