# agent_layer/tool_loader.py
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List
from dotenv import load_dotenv

load_dotenv()
# Ensure repo root on sys.path (so we can import the backbone without init-file gymnastics)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_collection_agents.bi_tracker_agent.llm_engine import BIUsageLLM # noqa: E402

# ---- Singleton LLM wrapper (reuses your JSON-contract scorers) ----
_llm = BIUsageLLM(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.0")),
)

def _clamp_band(v: Any) -> int:
    try:
        return max(1, min(5, int(v)))
    except Exception:
        return 3

def _sanitize(out: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
    out = dict(out or {})
    out["metric_id"] = metric_id
    out["band"] = _clamp_band(out.get("band", out.get("score", 3)))
    out.setdefault("rationale", "Strong signal; limited by missing detail.")
    out.setdefault("gaps", [])
    out.setdefault("flags", [])

    # Keep things tidy
    out["rationale"] = str(out["rationale"])[:600]
    gaps = out.get("gaps", [])
    out["gaps"] = [str(g)[:280] for g in gaps][:6]
    flags = out.get("flags", [])
    out["flags"] = [str(f)[:80] for f in flags][:10]

    # For backward-compat consumers that read 'score'
    out["score"] = out["band"]
    return out

# Map metric_id -> callable(snapshot)-> JSON (delegates to your BIUsageLLM)
def load_tool(metric_id: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def _score(_mid: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        s = snapshot or {}
        if _mid == "usage.dau_mau":
            return _sanitize(_llm.score_dau_mau(s.get("activity_events", []), s.get("today_utc", "")), _mid)
        if _mid == "usage.creators_ratio":
            return _sanitize(_llm.score_active_creators(s.get("usage_logs", [])), _mid)
        if _mid == "usage.session_depth":
            return _sanitize(_llm.score_session_depth(s.get("session_logs", [])), _mid)
        if _mid == "usage.drilldown":
            return _sanitize(_llm.score_drilldown(s.get("interaction_logs", [])), _mid)
        if _mid == "usage.weekly_active_trend":
            return _sanitize(_llm.score_weekly_active_trend(s.get("activity_events", []), s.get("today_utc", "")), _mid)
        if _mid == "usage.retention_4w":
            return _sanitize(_llm.score_retention_4w(s.get("activity_events", []), s.get("today_utc", "")), _mid)

        if _mid == "features.cross_links":
            return _sanitize(_llm.score_cross_links(s.get("dashboard_link_data", [])), _mid)
        if _mid == "features.export_rate":
            return _sanitize(_llm.score_export_rate(s.get("activity_events", [])), _mid)
        if _mid == "features.alerts_usage":
            return _sanitize(_llm.score_alerts_usage(s.get("activity_events", [])), _mid)

        if _mid == "democratization.dept_coverage":
            return _sanitize(_llm.score_dept_coverage(s.get("user_roles", []), s.get("user_directory", [])), _mid)
        if _mid == "democratization.self_service":
            return _sanitize(_llm.score_self_service_adoption(s.get("user_roles", [])), _mid)

        if _mid == "reliability.refresh_timeliness":
            return _sanitize(_llm.score_refresh_timeliness(s.get("dashboard_metadata", []), s.get("today_utc", "")), _mid)
        if _mid == "reliability.sla_breach_streaks":
            return _sanitize(_llm.score_sla_breach_streaks(s.get("dashboard_metadata", []), s.get("today_utc", "")), _mid)
        if _mid == "reliability.error_rate_queries":
            return _sanitize(_llm.score_error_rate_queries(s.get("activity_events", [])), _mid)

        if _mid == "governance.coverage":
            return _sanitize(_llm.score_governance_coverage(s.get("governance_data", [])), _mid)
        if _mid == "governance.pii_coverage":
            return _sanitize(_llm.score_pii_coverage(s.get("governance_data", [])), _mid)
        if _mid == "governance.lineage_coverage":
            return _sanitize(_llm.score_lineage_coverage(s.get("governance_data", [])), _mid)

        if _mid == "data.source_diversity":
            return _sanitize(_llm.score_source_diversity(s.get("source_catalog", [])), _mid)
        if _mid == "data.cost_efficiency":
            return _sanitize(_llm.score_cost_efficiency(
                s.get("source_catalog", []),
                s.get("activity_events", []),
                s.get("dashboard_metadata", []),
            ), _mid)

        # Unknown metric id
        return _sanitize({"band": 3, "rationale": "Unknown metric_id."}, _mid)

    return lambda snapshot: _score(metric_id, snapshot)