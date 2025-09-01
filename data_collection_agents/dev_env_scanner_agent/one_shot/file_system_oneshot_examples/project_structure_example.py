from __future__ import annotations

PROJECT_STRUCTURE_EXAMPLE = {
    "ProjectStructureAgent": {
        "input_key_meanings": {
            "file_paths": "Sample of repo tree to infer layout and documentation signals."
        },
        "example_input": {
            "file_paths": [
                "README.md",
                "docs/architecture.md",
                "src/app/__init__.py",
                "src/app/api.py",
                "tests/test_api.py"
            ]
        },
        "example_output": {
            "metric_id": "repo.project_structure",
            "band": 4,
            "rationale": "Clear src/ layout with docs and tests; ownership and ADRs are not consistently present.",
            "flags": ["owner_docs_missing", "adrs_absent"],
            "gaps": [
                "Missing OWNERS/CODEOWNERS → add code ownership map → speed up reviews (unlocks band 5).",
                "Architecture decisions not tracked → add ADRs in docs/ → create change history (supports band 5)."
            ]
        }
    }
}