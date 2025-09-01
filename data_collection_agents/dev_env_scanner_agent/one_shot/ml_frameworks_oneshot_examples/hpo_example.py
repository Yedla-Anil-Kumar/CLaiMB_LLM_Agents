from __future__ import annotations

MLFRAMEWORK_HYPERPARAMETEROPTIMIZATIONAGENT_EXAMPLE = {
    "HyperparameterOptimizationAgent": {
        "input_key_meanings": {"code_snippets": "Search/optimization code or HPO configs (YAML/JSON)."},
        "example_input": {
            "code_snippets": [
                """\
                    import optuna
                    def objective(trial):
                        lr = trial.suggest_float('lr', 1e-5, 1e-2, log=True)
                        ...
                    study = optuna.create_study(direction='minimize')
                    study.optimize(objective, n_trials=50)
                    # seeds/artifacts persistence not shown
                """
            ]
        },
        "example_output": {
            "metric_id": "ml.hpo_practice",
            "band": 4,
            "rationale": "Optuna-based search is sensible; seeds and trial artifact persistence are partly missing.",
            "flags": ["seed_missing", "trial_artifacts_missing"],
            "gaps": [
                "No fixed seeds → set global/random seeds per trial → comparable results (unlocks band 5).",
                "Artifacts sparse → log per-trial metrics/plots → enable auditability (supports band 5).",
                "Best params not persisted → store config + checkpoint → easy promotion (supports band 5)."
            ]
        }
    }
}