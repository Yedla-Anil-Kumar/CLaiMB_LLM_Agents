# Data_Collection_Agents/dev_env_scanner/one_shot/ml_framework_examples.py
from __future__ import annotations

ML_FRAMEWORK_EXAMPLES = {
    "MLFrameworkAgent": {
        "input_key_meanings": {"code_snippets": "Model training/inference code to infer framework mix."},
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
            "framework_usage": {"torch": 3, "sklearn": 1},
            "primary_framework": "torch",
            "framework_combinations": [["torch", "sklearn"]],
            "usage_patterns": ["Torch model with sklearn metrics"]
        }
    },

    "ExperimentTrackingAgent": {
        "input_key_meanings": {"code_snippets": "Training code that may log params/metrics with MLflow/W&B/ClearML."},
        "example_input": {
            "code_snippets": [
                """\
import mlflow
with mlflow.start_run():
    mlflow.log_param("lr", 0.001)
    mlflow.log_metric("loss", 0.23, step=10)
"""
            ]
        },
        "example_output": {
            "tracking_tools": {"mlflow": True, "wandb": False, "clearml": False},
            "tracking_patterns": ["context-managed run", "param/metric logging"],
            "best_practices": ["Log model signature and input example"],
            "improvement_suggestions": ["Enable autologging for sklearn/torch"]
        }
    },

    "HyperparameterOptimizationAgent": {
        "input_key_meanings": {"code_snippets": "Search/optimization snippets; YAML/JSON configs also relevant."},
        "example_input": {
            "code_snippets": [
                """\
import optuna
def objective(trial):
    lr = trial.suggest_float('lr', 1e-5, 1e-2, log=True)
    ...
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)
"""
            ]
        },
        "example_output": {
            "optimization_tools": {"optuna": True, "ray tune": False},
            "config_files": True,
            "optimization_strategies": ["Bayesian-like TPE search"],
            "best_practices": ["Persist best params; fix random seed; track trial artifacts"]
        }
    },

    "DataValidationAgent": {
        "input_key_meanings": {"code_snippets": "Pipelines that validate data schemas, distributions or drift."},
        "example_input": {
            "code_snippets": [
                """\
from great_expectations.dataset import PandasDataset

ds = PandasDataset(df)
ds.expect_column_values_to_not_be_null('user_id')
ds.expect_column_values_to_be_between('amount', min_value=0)
result = ds.validate()
"""
            ]
        },
        "example_output": {
            "validation_tools": {"great expectations": True, "evidently": False, "pandera": False},
            "validation_patterns": ["schema + value-range checks"],
            "data_quality_checks": ["null checks", "range checks"],
            "improvement_suggestions": ["Automate validation in CI and fail fast on critical rules"]
        }
    },

    "ModelTrainingAgent": {
        "input_key_meanings": {"code_snippets": "Entrypoint scripts/classes that kick off model training."},
        "example_input": {
            "code_snippets": [
                """\
if __name__ == "__main__":
    cfg = load_cfg('configs/train.yaml')
    trainer = Trainer(cfg)
    trainer.fit()
"""
            ]
        },
        "example_output": {
            "train_script_count": 1,
            "has_entrypoint_training": True,
            "training_patterns": ["YAML-driven config", "orchestrated Trainer"],
            "training_quality": 0.72
        }
    },

    "ModelEvaluationAgent": {
        "input_key_meanings": {"code_snippets": "Evaluation scripts; look for metrics libraries."},
        "example_input": {
            "code_snippets": [
                """\
from sklearn.metrics import f1_score, roc_auc_score
def evaluate(y_true, y_prob):
    return {'f1': f1_score(y_true, y_prob>0.5), 'auc': roc_auc_score(y_true, y_prob)}
"""
            ]
        },
        "example_output": {
            "eval_script_count": 1,
            "uses_metrics_library": True,
            "evaluation_metrics": ["f1", "auc"],
            "evaluation_quality": 0.75
        }
    },
}