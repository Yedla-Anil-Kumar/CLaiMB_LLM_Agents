# Data_Collection_Agents/dev_env_scanner/one_shot/file_system_examples.py
from __future__ import annotations

FILE_SYSTEM_EXAMPLES = {
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
            "test_file_count": 6,
            "test_frameworks": ["pytest"],
            "test_coverage_estimate": 0.58,
            "testing_quality": 0.64,
            "has_test_coverage_report": True
        }
    },

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
            "dependency_files": {
                "requirements.txt": True,
                "environment.yml": True,
                "pyproject.toml": True,
                "setup.py": True
            },
            "dependency_management_quality": 0.8,
            "environment_consistency": 0.75,
            "best_practices": ["Pin indirect deps via lock or hashes", "Single source of truth for versions"]
        }
    },

    "CICDAgent": {
        "input_key_meanings": {"file_paths": "Paths including CI configs under .github/, .gitlab-ci.yml, Jenkinsfile, etc."},
        "example_input": {
            "file_paths": [
                ".github/workflows/ci.yml",
                ".github/workflows/deploy.yml",
                "Jenkinsfile",
                "src/app/main.py"
            ]
        },
        "example_output": {
            "ci_files": {"github_actions": 2, "jenkins": 1},
            "ci_workflow_count": 3,
            "ci_quality": 0.78,
            "deployment_automation": 0.7
        }
    },

    "DeploymentAgent": {
        "input_key_meanings": {"file_paths": "Paths with Docker/K8s/Helm/Terraform or deploy scripts."},
        "example_input": {
            "file_paths": [
                "Dockerfile",
                "docker-compose.yml",
                "k8s/deployment.yaml",
                "k8s/service.yaml",
                "infra/helm/Chart.yaml",
                "scripts/deploy.sh"
            ]
        },
        "example_output": {
            "deployment_files": {"docker": 2, "kubernetes": 2, "helm": 1, "bash": 1},
            "deploy_script_count": 3,
            "deployment_automation": 0.8,
            "deployment_quality": 0.76
        }
    },

    "ExperimentDetectionAgent": {
        "input_key_meanings": {"file_paths": "Folders like experiments/, mlruns/, notebooks/experiments/"},
        "example_input": {"file_paths": ["experiments/exp_2025_08_21/config.yaml", "mlruns/0/meta.yaml"]},
        "example_output": {
            "experiment_dirs": ["experiments", "mlruns"],
            "experiment_folder_count": 2,
            "experiment_management": 0.7,
            "reproducibility_analysis": ["Runs tracked with MLflow, configs committed"]
        }
    },

    "ProjectStructureAgent": {
        "input_key_meanings": {"file_paths": "Sample of repo tree to infer layout and documentation signals."},
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
            "structure_quality": 0.74,
            "organization_patterns": ["src/ layout", "docs/ present", "tests/ present"],
            "documentation_quality": 0.7,
            "best_practices_adherence": 0.72
        }
    },
}