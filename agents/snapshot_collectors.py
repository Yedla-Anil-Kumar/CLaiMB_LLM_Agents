# snapshot_collectors.py
"""
Snapshot collectors for the MVP Data Platform Scanner.

Behavior:
- Look for a `data/` directory (relative to the project root) and try to load
  specific JSON files for each snapshot key.
- If a file doesn't exist or can't be parsed, fall back to built-in defaults.
- Expose `collect_snapshot()` which returns the full context dictionary used by
  the scanner.

Usage:
- from snapshot_collectors import collect_snapshot
- ctx = collect_snapshot()
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


# Mapping of snapshot keys -> expected filename in data/
_DEFAULT_FILENAMES = {
    "baseline_schema": "baseline_table.json",
    "table_schemas": "real_table.json",
    "table_metadata": "table_metadata.json",
    "data_quality_report": "quality_input_3.json",
    "access_logs": "governance_input_4.json",
    "lineage": "lineage_input_5.json",
    "metadata": "metadata_input_6.json",
    "tagging": "sensetive_tagging_input_7.json",           # original filename has a typo: 'sensetive'
    "duplication": "duplication_input_8.json",
    "backup": "backup_input_9.json",
    "security": "security_input_10.json",
    "pipeline_runs": "pipeline_success_input_b1.json",
    "pipeline_metrics": "pipeline_latency_input_b2.json",
    "resource_usage": "resource_utilization_input_b3.json",
    "query_logs": "query_performance_input_b4.json",
    "user_activity": "analytics_adoption_input_b5.json",
}


def _load_json_file(path: Path) -> Optional[Any]:
    """Return parsed JSON from path or None if missing / invalid."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[snapshot_collectors] Failed to load/parse {path}: {e}")
        return None


def _default_snapshot() -> Dict[str, Any]:
    """Return a compact default snapshot (same shape as used by the scanner)."""
    return {
        "baseline_schema": {"tables": [{"name": "users", "cols": ["id", "name", "email"]}]},
        "table_schemas": {"tables": [{"name": "users", "cols": ["id", "name", "email"]}]},
        "table_metadata": {"tables": [{"name": "users", "last_updated": "2025-08-01T00:00:00Z"}]},
        "data_quality_report": {"checks": [{"name": "nulls", "pct_null": 0.01}]},
        "access_logs": {"events": []},
        "lineage": {"jobs": [{"id": "job1", "upstreams": []}]},
        "metadata": {"tables": [{"name": "users", "description": "user table"}]},
        "tagging": {"columns": []},
        "duplication": {"tables": [{"name": "users", "duplicate_pct": 0.0}]},
        "backup": {"last_backup": "2025-08-01T01:00:00Z"},
        "security": {"policies": []},
        "pipeline_runs": {"runs": [{"id": "r1", "status": "success"}]},
        "pipeline_metrics": {"latency_ms": [120, 110, 150]},
        "resource_usage": {"cpu_pct": [10, 20, 15], "mem_mb": [1024, 1500, 1100]},
        "query_logs": {"queries": [{"sql": "select * from users", "latency_ms": 200}]},
        "user_activity": {"users": [{"id": 1, "used_dashboard": True}]},
    }


def collect_snapshot(data_dir: str = "data/Input") -> Dict[str, Any]:
    data_path = Path(data_dir)
    defaults = _default_snapshot()
    ctx = {}

    for key, filename in _DEFAULT_FILENAMES.items():
        file_path = data_path / filename
        value = _load_json_file(file_path)
        if value is not None:
            ctx[key] = value
        else:
            ctx[key] = defaults.get(key)
            if file_path.exists() and value is None:
                # there was a file but it couldn't be parsed -> warn user
                print(f"[snapshot_collectors] Using default for '{key}' because {file_path} couldn't be parsed.")
            # else file doesn't exist -> silent fallback to default

    return ctx


if __name__ == "__main__":
    import pprint

    print("Collecting snapshot from 'data/Input' (or falling back to defaults)...")
    snapshot = collect_snapshot()
    pprint.pprint(snapshot)
