# dev_env_scanner_agent/one_shot/prompting.py
import json

UNIVERSAL_PREAMBLE = (
    "You are a Code Repository Assessor. Grade exactly one metric on a 1–5 band:\n"
    "5 = Excellent\n4 = Good\n3 = Fair\n2 = Poor\n1 = Critical\n\n"
    "Rules:\n"
    "- Use ONLY the provided code snippets and context; do NOT invent code.\n"
    "- Consider ALL relevant evidence; if signals conflict, prefer the lower band and explain why.\n"
    "- Rationale: mention 1–2 strongest positives AND the biggest limiter (≤3 sentences).\n"
    "- 'gaps': action phrasing '<why> → <what to change> → <target> (unlocks band X)'.\n"
    "- Return ONLY the JSON per the response format."
)

UNIVERSAL_RESPONSE_FORMAT = (
    '{"metric_id":"<id>","band":<1-5>,"rationale":"<1-3 sentences>",'
    '"flags":[],"gaps":[]}'
)

def build_metric_prompt(*, rubric: str, metric_id: str,
                        input_key_meanings: dict,
                        task_input: dict,
                        example_input: dict,
                        example_output: dict) -> str:
    meanings = "\n".join([f"- {k}: {v}" for k, v in input_key_meanings.items()]) if input_key_meanings else ""
    return (
        f"SYSTEM:\n{UNIVERSAL_PREAMBLE}\n\nRUBRIC:\n{rubric}\n\n"
        f"INPUT KEY MEANINGS:\n{meanings}\n\n"
        f"RESPONSE FORMAT (JSON only):\n{UNIVERSAL_RESPONSE_FORMAT}\n\n"
        f"TASK INPUT (USER EVIDENCE):\n{json.dumps(task_input, indent=2)}\n\n"
        f"EXAMPLE INPUT:\n{json.dumps(example_input, indent=2)}\n\n"
        f"EXAMPLE OUTPUT:\n{json.dumps(example_output, indent=2)}"
    )