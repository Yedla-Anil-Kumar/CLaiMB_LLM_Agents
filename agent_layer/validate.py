# agent_layer/validate.py
from __future__ import annotations
from typing import Any, Dict, Tuple

BAND_NUM_TO_LETTER = {5: "A", 4: "B", 3: "C", 2: "D", 1: "E"}
LETTER_TO_SCORE = {"A": 100, "B": 85, "C": 70, "D": 55, "E": 40}

def clamp_band_num(v: Any) -> int:
    try:
        n = int(v)
    except Exception:
        n = 3
    return max(1, min(5, n))

def to_letter_and_score(num_band: int) -> Tuple[str, int]:
    letter = BAND_NUM_TO_LETTER.get(clamp_band_num(num_band), "C")
    return letter, LETTER_TO_SCORE[letter]

def sanitize_metric(metric_id: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize one metric:
    - Keep legacy Score (1..5) from backbone
    - Add band (A..E) and score_0to100
    - Tidy rationale and gaps
    """
    out = dict(raw or {})
    out["MetricID"] = out.get("MetricID", metric_id)
    # numeric band comes from backbone as band or Score
    num = out.get("band", out.get("Score", 3))
    num = clamp_band_num(num)
    out["Score"] = num  # legacy
    letter, score100 = to_letter_and_score(num)
    out["band"] = letter
    out["score_0to100"] = score100

    # tidy fields
    rationale = str(out.get("rationale", "No rationale."))[:600]
    out["rationale"] = rationale
    gaps = out.get("gaps", [])
    out["gaps"] = [str(g)[:160] for g in gaps][:5]

    # keep flags if present
    if "flags" in out and isinstance(out["flags"], list):
        out["flags"] = [str(f)[:80] for f in out["flags"]][:10]

    return out