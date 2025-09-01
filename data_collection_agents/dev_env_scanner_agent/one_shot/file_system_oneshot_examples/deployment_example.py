from __future__ import annotations

DEPLOYMENT_EXAMPLE = {
    "DeploymentAgent": {
        "input_key_meanings": {
            "file_paths": "Paths with Docker/K8s/Helm/Terraform or deploy scripts."
        },
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
            "metric_id": "repo.deployment_readiness",
            "band": 4,
            "rationale": "Docker/K8s/Helm present with scripts; rollout safety and probes not fully evidenced.",
            "flags": ["readiness_probes_unknown", "rollout_strategy_unspecified"],
            "gaps": [
                "Missing health/readiness probes → add probes and resource requests/limits → improve reliability (unlocks band 5).",
                "Rollout controls unclear → enable rolling/blue-green and canaries → documented rollback plan (supports band 5)."
            ]
        }
    }
}