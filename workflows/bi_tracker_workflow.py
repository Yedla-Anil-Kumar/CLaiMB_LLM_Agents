# workflows/bi_tracker_workflow.py
from __future__ import annotations
from typing import Any, Dict
from pathlib import Path

from agent_layer.orchestrator import run as run_agent

def collect_snapshot() -> Dict[str, Any]:
    """Tiny, realistic sample snapshot. Replace with your real loader if desired."""
    return {
        "today_utc": "2025-09-02",
        # Activity & interaction
        "activity_events": [
            {"ts": "2025-09-01T10:00:00Z", "user_id": "u1", "action": "view"},
            {"ts": "2025-09-01T11:30:00Z", "user_id": "u2", "action": "export"},
            {"ts": "2025-08-25T09:00:00Z", "user_id": "u3", "action": "view"},
            {"ts": "2025-08-15T09:00:00Z", "user_id": "u1", "action": "error"},
        ],
        "interaction_logs": [
            {"ts": "2025-09-01T10:01:00Z", "user": "u1", "action": "drill"},
            {"ts": "2025-09-01T10:05:00Z", "user": "u2", "action": "click"},
        ],
        "session_logs": [
            {"user": "u1", "duration": 310, "pages": 4, "repeats_per_week": 2},
            {"user": "u2", "duration": 190, "pages": 3},
        ],
        "usage_logs": [
            {"user": "u1", "role": "creator"},
            {"user": "u2", "role": "viewer"},
            {"user": "u3", "role": "viewer"},
        ],
        "user_roles": [
            {"id": "u1", "role": "creator"},
            {"id": "u2", "role": "viewer"},
            {"id": "u3", "role": "viewer"},
        ],
        "user_directory": [
            {"user_id": "u1", "department": "Finance"},
            {"user_id": "u2", "department": "Sales"},
            {"user_id": "u3", "department": "Ops"},
        ],
        # Governance & dashboards
        "governance_data": [
            {"id": "d1", "certified": True, "owner": "bi_ops", "metadata": ["description", "refresh_rate", "lineage"]},
            {"id": "d2", "certified": False, "owner": None, "metadata": []},
        ],
        "dashboard_metadata": [
            {"id": "d1", "last_refresh": "2025-09-01", "sla": "daily", "priority": "high"},
            {"id": "d2", "last_refresh": "2025-08-26", "sla": "weekly", "priority": "low"},
        ],
        "dashboard_link_data": [
            {"id": "d1", "links": ["d2"], "link_usage": 12},
            {"id": "d2", "links": [], "link_usage": 1},
        ],
        # Sources & decisions
        "source_catalog": ["Snowflake", "Postgres", "Salesforce"],
        "decision_logs": [
            {"id": "dec1", "linked_dash": "d1", "evidence": "screenshot", "date": "2025-08-28"},
            {"id": "dec2", "linked_dash": None, "evidence": None, "date": "2025-08-20"},
        ],
    }

def run_workflow() -> Dict[str, Any]:
    snapshot = collect_snapshot()
    result = run_agent(snapshot, out_dir=Path("runs_bi_mvp"))
    return result