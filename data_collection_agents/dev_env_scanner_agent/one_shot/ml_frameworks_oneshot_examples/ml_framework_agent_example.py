from __future__ import annotations

MLFRAMEWORK_MLFRAMEWORKAGENT_EXAMPLE = {
    "MLFrameworkAgent": {
        "input_key_meanings": {
            "code_snippets": "Model training/inference code to infer framework mix and consistency."
        },
        "example_input": {
            "code_snippets": [
                """\
                    import torch
                    import torch.nn as nn
                    from sklearn.metrics import accuracy_score

                    class Net(nn.Module):
                        def __init__(self): ...
                        def forward(self, x): ...

                    yhat = model(X)
                    acc = accuracy_score(y, yhat.argmax(1))
                """
            ]
        },
        "example_output": {
            "metric_id": "ml.framework_maturity",
            "band": 4,
            "rationale": "Torch is clearly primary and used idiomatically; some sklearn interop exists. Shared wrappers/utilities are not shown.",
            "flags": ["interop_with_sklearn", "wrappers_unknown"],
            "gaps": [
                "Inconsistent abstraction → add common training/eval wrappers → standardize APIs across modules (unlocks band 5)."
            ]
        }
    }
}