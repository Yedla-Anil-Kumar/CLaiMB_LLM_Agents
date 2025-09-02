# agent_layer/orchestrator.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Add repo root to path so imports work when running as a module
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_layer.registry import LEVEL0, LEVEL1_DEPS, CATEGORIES # noqa: E402
from agent_layer.tool_loader import load_tool # noqa: E402
from langchain_core.runnables import RunnableLambda, RunnableParallel # noqa: E402


def _now_id(prefix: str = "bi-tracker") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{prefix}-{ts}"


def _clamp_band(v: Any) -> float:
    try:
        x = int(v)
        if x < 1: x = 1
        if x > 5: x = 5
        return float(x)
    except Exception:
        return 3.0


def _aggregate(metrics: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    cat_scores: Dict[str, float] = {}
    overall = 0.0
    tot_cat_w = 0.0

    for cat, spec in CATEGORIES.items():
        cat_w = float(spec.get("weight", 0.5))
        met_weights: Dict[str, float] = spec.get("metrics", {})
        s = sum(met_weights.values()) or 1.0
        score = 0.0
        for m_id, w in met_weights.items():
            band = _clamp_band(metrics.get(m_id, {}).get("band", 3))
            score += (w / s) * band
        cat_scores[cat] = round(score, 2)
        overall += cat_w * score
        tot_cat_w += cat_w

    overall_score = round(overall / tot_cat_w, 2) if tot_cat_w else 0.0
    return {**cat_scores, "overall_score": overall_score}


def run(snapshot: Dict[str, Any], out_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Deterministic execution:
      - Level 0 (parallel)
      - Level 1 (sequential, honoring dependencies)
      - Aggregation by categories (50/50)

    If out_dir is provided, writes ./<out_dir>/<run_id>.json
    """
    load_dotenv()  # ensure .env is loaded for the backbone

    # --- Level 0 in parallel ---
    l0_tools = {mid: RunnableLambda(lambda s, _m=mid: load_tool(_m)(s)) for mid in LEVEL0}
    parallel = RunnableParallel(**l0_tools)
    l0_out: Dict[str, Dict[str, Any]] = parallel.invoke(snapshot)

    # --- Level 1 (single wave; deps are for ordering only here) ---
    l1_out: Dict[str, Dict[str, Any]] = {}
    for mid, deps in LEVEL1_DEPS.items():
        # (Optional) verify deps were executed; we don't feed their outputs into prompts yet.
        _ = [d for d in deps if d not in l0_out]  # could log if needed
        l1_out[mid] = load_tool(mid)(snapshot)

    # --- Merge & aggregate ---
    metrics: Dict[str, Dict[str, Any]] = {**l0_out, **l1_out}
    aggregates = _aggregate(metrics)

    result = {
        "run_id": _now_id(),
        "metrics": metrics,
        "aggregates": aggregates,
    }

    # --- Persistence (optional) ---
    artifact_path: Optional[str] = None
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        artifact = out_dir / f"{result['run_id']}.json"
        artifact.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        artifact_path = str(artifact)
        result["artifact_path"] = artifact_path

    return result