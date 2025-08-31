# Data_Collection_Agents/dev_env_scanner/one_shot/registry.py
from __future__ import annotations
from typing import Any, Dict

# Import the family-specific example maps created earlier
from dev_env_scanner_agent.one_shot.code_quality_examples import CODE_QUALITY_EXAMPLES
from dev_env_scanner_agent.one_shot.file_system_examples import FILE_SYSTEM_EXAMPLES
from dev_env_scanner_agent.one_shot.infrastructure_examples import INFRASTRUCTURE_EXAMPLES
from dev_env_scanner_agent.one_shot.ml_framework_examples import ML_FRAMEWORK_EXAMPLES

# Merge into a single registry keyed by agent class name
_ONE_SHOT_REGISTRY: Dict[str, Dict[str, Any]] = {}
_ONE_SHOT_REGISTRY.update(CODE_QUALITY_EXAMPLES)
_ONE_SHOT_REGISTRY.update(FILE_SYSTEM_EXAMPLES)
_ONE_SHOT_REGISTRY.update(INFRASTRUCTURE_EXAMPLES)
_ONE_SHOT_REGISTRY.update(ML_FRAMEWORK_EXAMPLES)

def get_one_shot(agent_name: str) -> Dict[str, Any]:
    """
    Return {"input_key_meanings", "example_input", "example_output"} for an agent.
    Raises KeyError if not found (so call sites fail fast).
    """
    ex = _ONE_SHOT_REGISTRY.get(agent_name)
    if not ex:
        raise KeyError(f"No one-shot examples registered for {agent_name}")
    return ex