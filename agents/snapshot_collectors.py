# """
# Snapshot collectors for the MVP Data Platform Scanner.

# Behavior:
# - Loads config.yaml for file mappings.
# - Looks for a `data/` directory (relative to project root) and tries to load JSON files.
# - Falls back to built-in defaults if file missing or invalid.
# """

# import json
# import yaml
# from pathlib import Path
# from typing import Any, Dict, Optional


# def _load_json_file(path: Path) -> Optional[Any]:
#     if not path.exists():
#         return None
#     try:
#         return json.loads(path.read_text(encoding="utf-8"))
#     except Exception as e:
#         print(f"[snapshot_collectors] Failed to load/parse {path}: {e}")
#         return None


# def _load_config(config_path: Path) -> Dict[str, Any]:
#     try:
#         with config_path.open(encoding="utf-8") as f:
#             return yaml.safe_load(f)
#     except Exception as e:
#         raise RuntimeError(f"[snapshot_collectors] Failed to load config file {config_path}: {e}")


# def _default_snapshot() -> Dict[str, Any]:
#     return {
#         "baseline_schema": {"tables": [{"name": "users", "cols": ["id", "name", "email"]}]},
#         "table_schemas": {"tables": [{"name": "users", "cols": ["id", "name", "email"]}]},
#         "table_metadata": {"tables": [{"name": "users", "last_updated": "2025-08-01T00:00:00Z"}]},
#         "data_quality_report": {"checks": [{"name": "nulls", "pct_null": 0.01}]},
#         "access_logs": {"events": []},
#         "lineage": {"jobs": [{"id": "job1", "upstreams": []}]},
#         "metadata": {"tables": [{"name": "users", "description": "user table"}]},
#         "tagging": {"columns": []},
#         "duplication": {"tables": [{"name": "users", "duplicate_pct": 0.0}]},
#         "backup": {"last_backup": "2025-08-01T01:00:00Z"},
#         "security": {"policies": []},
#         "pipeline_runs": {"runs": [{"id": "r1", "status": "success"}]},
#         "pipeline_metrics": {"latency_ms": [120, 110, 150]},
#         "resource_usage": {"cpu_pct": [10, 20, 15], "mem_mb": [1024, 1500, 1100]},
#         "query_logs": {"queries": [{"sql": "select * from users", "latency_ms": 200}]},
#         "user_activity": {"users": [{"id": 1, "used_dashboard": True}]},
#     }


# def collect_snapshot(data_dir: str = "data/Input", config_file: str = "config/config.yaml") -> Dict[str, Any]:
#     data_path = Path(data_dir)
#     config_path = Path(config_file)
#     config = _load_config(config_path)
#     file_mapping = config.get("default_filenames", {})
#     defaults = _default_snapshot()
#     ctx = {}

#     for key, filename in file_mapping.items():
#         file_path = data_path / filename
#         value = _load_json_file(file_path)
#         if value is not None:
#             ctx[key] = value
#         else:
#             ctx[key] = defaults.get(key)
#             if file_path.exists() and value is None:
#                 print(f"[snapshot_collectors] Using default for '{key}' because {file_path} couldn't be parsed.")

#     return ctx


# if __name__ == "__main__":
#     import pprint

#     print("Collecting snapshot from 'data/Input' (or falling back to defaults)...")
#     snapshot = collect_snapshot()
#     pprint.pprint(snapshot)
"""
Snapshot collectors for the MVP Data Platform Scanner.

Behavior:
- Loads config.yaml for file mappings.
- Looks for a `data/` directory (relative to project root) and tries to load JSON files.
- Falls back to built-in defaults if file missing or invalid.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class DataPlatformAnalyzerSnapshotCollector:
    def __init__(self, data_dir: str = "data/Input", config_file: str = "config/config.yaml"):
        self.data_path = Path(data_dir)
        self.config_path = Path(config_file)
        self.config = self._load_config()
        self.file_mapping = self.config.get("default_filenames", {})
        self.defaults = self._default_snapshot()

    def _load_json_file(self, path: Path) -> Optional[Any]:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[SnapshotCollector] Failed to load/parse {path}: {e}")
            return None

    def _load_config(self) -> Dict[str, Any]:
        try:
            with self.config_path.open(encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"[SnapshotCollector] Failed to load config file {self.config_path}: {e}")

    def _default_snapshot(self) -> Dict[str, Any]:
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

    def collect_snapshot(self) -> Dict[str, Any]:
        ctx = {}
        for key, filename in self.file_mapping.items():
            file_path = self.data_path / filename
            value = self._load_json_file(file_path)
            if value is not None:
                ctx[key] = value
            else:
                ctx[key] = self.defaults.get(key)
                if file_path.exists() and value is None:
                    print(f"[SnapshotCollector] Using default for '{key}' because {file_path} couldn't be parsed.")
        return ctx


if __name__ == "__main__":
    import pprint

    collector = SnapshotCollector()
    print("Collecting snapshot from 'data/Input' (or falling back to defaults)...")
    snapshot = collector.collect_snapshot()
    pprint.pprint(snapshot)
