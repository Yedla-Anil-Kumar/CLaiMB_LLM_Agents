# agent_layer/orchestrator.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# path bootstrap
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_layer.registry import LEVEL0, LEVEL1_DEPS, CATEGORIES  # noqa: E402
from agent_layer.router import route, route_many                 # noqa: E402
from langchain_core.runnables import RunnableParallel           # noqa: E402


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _now_id(prefix: str = "code-repo") -> str:
    return f"{prefix}-{now_utc_iso()}"


def _clamp_band(v: Any) -> float:
    try:
        x = int(v)
        if x < 1:
            x = 1
        if x > 5:
            x = 5
        return float(x)
    except Exception:
        return 3.0


def _aggregate(metrics: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    cat_scores: Dict[str, float] = {}
    overall = 0.0
    tot_w = 0.0
    for cat, spec in CATEGORIES.items():
        cat_w = float(spec.get("weight", 0.5))
        met_w: Dict[str, float] = spec.get("metrics", {})
        s = sum(met_w.values()) or 1.0
        score = 0.0
        for mid, w in met_w.items():
            band = _clamp_band(metrics.get(mid, {}).get("band", 3))
            score += (w / s) * band
        score = round(score, 2)
        cat_scores[cat] = score
        overall += cat_w * score
        tot_w += cat_w
    cat_scores["overall_score"] = round(overall / tot_w, 2) if tot_w else 0.0
    return cat_scores


class CodeRepoOrchestrator:
    """
    Class-based orchestrator for the code-repo agent:
      - L0 parallel fanout (RunnableParallel)
      - L1 metrics (respecting declared deps presence)
      - aggregate category and overall
      - optional artifact writing
    """

    def __init__(self, *, prefix: str = "code-repo") -> None:
        self.prefix = prefix

    def run(self, snapshot: Dict[str, Any], out_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Snapshot must contain:
          - code_snippets: list[str]
          - file_paths:    list[str]
        """
        load_dotenv()

        # Level 0
        l0_runnables = route_many(LEVEL0)
        parallel = RunnableParallel(**l0_runnables)
        l0_out: Dict[str, Dict[str, Any]] = parallel.invoke(snapshot)

        # Level 1
        l1_out: Dict[str, Dict[str, Any]] = {}
        for mid, deps in LEVEL1_DEPS.items():
            # deps are computed by L0; we could validate/log if missing
            _ = [d for d in deps if d not in l0_out]
            l1_out[mid] = route(mid).invoke(snapshot)

        metrics: Dict[str, Dict[str, Any]] = {**l0_out, **l1_out}
        aggregates = _aggregate(metrics)

        result = {
            "run_id": _now_id(self.prefix),
            "metrics": metrics,
            "aggregates": aggregates,
        }

        if out_dir is not None:
            out_dir = Path(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            artifact = out_dir / f"{result['run_id']}.json"
            artifact.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            result["artifact_path"] = str(artifact)

        return result


# === Backwards-compatible functional API ===
def run(snapshot: Dict[str, Any], out_dir: Optional[Path] = None) -> Dict[str, Any]:
    orch = CodeRepoOrchestrator()
    return orch.run(snapshot, out_dir=out_dir)
