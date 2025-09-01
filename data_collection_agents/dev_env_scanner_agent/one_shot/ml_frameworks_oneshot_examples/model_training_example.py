from __future__ import annotations

MLFRAMEWORK_MODELTRAININGAGENT_EXAMPLE = {
    "ModelTrainingAgent": {
        "input_key_meanings": {"code_snippets": "Entrypoint scripts/classes that kick off training."},
        "example_input": {
            "code_snippets": [
                """\
                    if __name__ == "__main__":
                        cfg = load_cfg('configs/train.yaml')
                        trainer = Trainer(cfg)
                        trainer.fit()  # checkpoints/resume not shown
                """
            ]
        },
        "example_output": {
            "metric_id": "ml.training_practice",
            "band": 4,
            "rationale": "Config-driven training with a clear entrypoint; reproducibility hooks and failure recovery are not shown.",
            "flags": ["reproducibility_unknown", "resume_checkpoints_missing"],
            "gaps": [
                "Seed & environment capture missing → record seeds and package versions → reproducible runs (unlocks band 5).",
                "Resume on failure not guaranteed → checkpointing & auto-resume → resilient training (supports band 5)."
            ]
        }
    }
}