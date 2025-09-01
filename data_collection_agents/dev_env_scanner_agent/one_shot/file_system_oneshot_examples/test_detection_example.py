from __future__ import annotations

TEST_DETECTION_EXAMPLE = {
    "TestDetectionAgent": {
        "input_key_meanings": {
            "code_snippets": "Representative test files or files importing test frameworks."
        },
        "example_input": {
            "code_snippets": [
                """\
                # tests/test_api.py
                import pytest
                from app import create_app

                @pytest.fixture
                def client():
                    app = create_app()
                    return app.test_client()

                def test_health(client):
                    rv = client.get('/health')
                    assert rv.status_code == 200
                """
            ]
        },
        "example_output": {
            "metric_id": "repo.tests_presence",
            "band": 4,
            "rationale": "Pytest detected with fixtures and basic health checks; breadth of test types and coverage reporting is unclear.",
            "flags": ["coverage_report_unknown", "limited_test_types"],
            "gaps": [
                "Coverage signal missing → integrate coverage tool and publish threshold in CI → require ≥70% line coverage (unlocks band 5).",
                "Narrow test scope → add integration and negative-path tests → expand beyond smoke tests (supports band 5)."
            ]
        }
    }
}