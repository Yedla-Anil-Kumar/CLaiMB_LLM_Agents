from __future__ import annotations
from typing import Any, Dict, List

def clamp_band(x: Any, default: int = 3) -> int:
    try:
        return max(1, min(5, int(x)))
    except Exception:
        return default

def normalize(obj: Dict[str, Any], metric_id_fallback: str) -> Dict[str, Any]:
    out = dict(obj or {})
    out.setdefault("metric_id", metric_id_fallback)
    out["band"] = clamp_band(out.get("band", 3))
    out["score"] = out["band"]
    out["rationale"] = str(out.get("rationale", "")).strip() or "No rationale."
    out["flags"] = [str(x) for x in (out.get("flags", []) or [])][:10]
    out["gaps"]  = [str(x) for x in (out.get("gaps", []) or [])][:5]
    return out

def consolidate(outputs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for obj in outputs:
        if not isinstance(obj, dict):
            continue
        metric_id = obj.get("metric_id")
        if not metric_id:
            continue
        band = clamp_band(obj.get("band", 3))
        rationale = str(obj.get("rationale", "")).strip()
        flags = [str(x) for x in (obj.get("flags", []) or [])]
        gaps  = [str(x) for x in (obj.get("gaps", []) or [])]

        if metric_id not in merged:
            merged[metric_id] = {
                "metric_id": metric_id,
                "band": band,
                "score": band,
                "rationale": rationale,
                "flags": list(dict.fromkeys(flags)),
                "gaps":  list(dict.fromkeys(gaps)),
            }
            continue

        cur = merged[metric_id]
        cur["band"] = min(cur["band"], band)
        cur["score"] = cur["band"]
        if len(rationale) > len(cur.get("rationale", "")):
            cur["rationale"] = rationale
        # union lists preserving order
        for key, newvals in (("flags", flags), ("gaps", gaps)):
            seen = set(cur[key])
            for v in newvals:
                if v not in seen:
                    cur[key].append(v); seen.add(v)
    return merged