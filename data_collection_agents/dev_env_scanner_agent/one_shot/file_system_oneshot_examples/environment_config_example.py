from __future__ import annotations

ENV_CONFIG_EXAMPLE = {
    "EnvironmentConfigAgent": {
        "input_key_meanings": {
            "file_paths": "Repo file paths; include dependency and env files if present."
        },
        "example_input": {
            "file_paths": [
                "pyproject.toml",
                "requirements.txt",
                "environment.yml",
                "src/app/main.py",
                "setup.py"
            ]
        },
        "example_output": {
            "metric_id": "repo.env_config_hygiene",
            "band": 4,
            "rationale": "Multiple dependency descriptors found; presence is strong but single source of truth and locking are unclear.",
            "flags": ["multiple_dep_files", "lockfile_missing"],
            "gaps": [
                "Dual descriptors (pyproject + requirements) → choose one canonical source → document toolchain (unlocks band 5).",
                "No lockfile → add `uv.lock`/`poetry.lock`/`pip-tools` hashes → ensure reproducible builds (supports band 5)."
            ]
        }
    }
}