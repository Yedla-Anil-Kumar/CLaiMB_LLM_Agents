from __future__ import annotations

CI_CD_EXAMPLE = {
    "CICDAgent": {
        "input_key_meanings": {
            "file_paths": "Paths including CI configs under .github/, .gitlab-ci.yml, Jenkinsfile, etc."
        },
        "example_input": {
            "file_paths": [
                ".github/workflows/ci.yml",
                ".github/workflows/deploy.yml",
                "Jenkinsfile",
                "src/app/main.py"
            ]
        },
        "example_output": {
            "metric_id": "repo.cicd_presence",
            "band": 4,
            "rationale": "Build and deploy workflows exist across two systems; quality appears good but policy gates are unknown.",
            "flags": ["multi_ci_systems", "policy_gates_unknown"],
            "gaps": [
                "Ambiguous policy enforcement → require tests/linters/scan gates pre-deploy → all gates pass before release (unlocks band 5).",
                "Two CI providers → consolidate or document ownership → reduce drift/flakiness (supports band 5)."
            ]
        }
    }
}