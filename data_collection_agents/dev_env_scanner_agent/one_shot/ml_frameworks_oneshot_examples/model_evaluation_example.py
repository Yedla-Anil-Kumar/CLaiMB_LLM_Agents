from __future__ import annotations

MLFRAMEWORK_MODELEVALUATIONAGENT_EXAMPLE = {
    "ModelEvaluationAgent": {
        "input_key_meanings": {"code_snippets": "Evaluation scripts and metrics usage."},
        "example_input": {
            "code_snippets": [
                """\
                    from sklearn.metrics import f1_score, roc_auc_score

                    def evaluate(y_true, y_prob):
                        return {"f1": f1_score(y_true, y_prob>0.5), "auc": roc_auc_score(y_true, y_prob)}
                    # calibration/fairness analysis not shown
                """
            ]
        },
        "example_output": {
            "metric_id": "ml.evaluation_practice",
            "band": 4,
            "rationale": "Standard metrics used consistently; calibration and fairness analyses are not evidenced.",
            "flags": ["calibration_unknown", "fairness_analysis_missing"],
            "gaps": [
                "No calibration → add reliability plots/calibrators → better thresholding (unlocks band 5).",
                "Fairness not reported → include bias metrics by segment → complete evaluation (supports band 5)."
            ]
        }
    }
}