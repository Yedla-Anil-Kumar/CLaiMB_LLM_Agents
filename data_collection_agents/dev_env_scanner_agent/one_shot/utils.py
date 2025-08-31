# Data_Collection_Agents/dev_env_scanner/one_shot/utils.py
from __future__ import annotations
import json
from typing import Any, Dict

def build_one_shot_prompt(
    *,
    system_preamble: str,
    response_format_description: str,
    task_input: Dict[str, Any],
    input_key_meanings: Dict[str, str],
    example_input: Dict[str, Any],
    example_output: Dict[str, Any],
) -> str:
    """
    Consistent one-shot prompt builder:
      - SYSTEM block with instructions/rubric
      - INPUT KEY MEANINGS (field intent)
      - TASK INPUT (user evidence)
      - RESPONSE FORMAT (strict JSON schema the model must return)
      - EXAMPLE INPUT/OUTPUT (true one-shot to reduce variance)
    """
    meanings_lines = "\n".join(f"- {k}: {v}" for k, v in input_key_meanings.items()) if input_key_meanings else ""
    return (
        f"SYSTEM:\n{system_preamble.strip()}\n\n"
        f"INPUT KEY MEANINGS:\n{meanings_lines}\n\n"
        f"TASK INPUT:\n{json.dumps(task_input, indent=2)}\n\n"
        f"RESPONSE FORMAT (JSON only):\n{response_format_description.strip()}\n\n"
        f"EXAMPLE INPUT:\n{json.dumps(example_input, indent=2)}\n\n"
        f"EXAMPLE OUTPUT:\n{json.dumps(example_output, indent=2)}"
    )