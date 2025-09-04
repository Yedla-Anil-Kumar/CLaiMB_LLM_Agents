from __future__ import annotations
from typing import Dict, Tuple, Any, List
from .registry import CATEGORIES

def compute_category_and_overall(metric_breakdown: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, float], float]:
    cat_scores: Dict[str, float] = {}
    for cat, metric_ids in CATEGORIES.items():
        vals: List[float] = [metric_breakdown[m]["score"] for m in metric_ids if m in metric_breakdown]
        cat_scores[cat] = round(sum(vals) / max(1, len(vals)), 2)
    overall = round(0.5 * cat_scores.get("development_maturity", 0.0) + 0.5 * cat_scores.get("innovation_pipeline", 0.0), 2)
    return cat_scores, overall