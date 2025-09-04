from __future__ import annotations
from typing import Any, Dict, List, Optional

# Reuse your existing MicroAgents (all expose METRIC_ID + evaluate)
from data_collection_agents.dev_env_scanner_agent.code_quality.cyclomatic_complexity import CyclomaticComplexityAgent
from data_collection_agents.dev_env_scanner_agent.code_quality.maintainability_index import MaintainabilityAgent
from data_collection_agents.dev_env_scanner_agent.code_quality.docstring_coverage import DocstringCoverageAgent
from data_collection_agents.dev_env_scanner_agent.code_quality.nested_loops import NestedLoopsAgent

from data_collection_agents.dev_env_scanner_agent.infrastructure.parallel_patterns import ParallelPatternsAgent
from data_collection_agents.dev_env_scanner_agent.infrastructure.data_pipeline import DataPipelineAgent
from data_collection_agents.dev_env_scanner_agent.infrastructure.feature_engineering import FeatureEngineeringAgent
from data_collection_agents.dev_env_scanner_agent.infrastructure.model_export import ModelExportAgent
from data_collection_agents.dev_env_scanner_agent.infrastructure.inference_endpoint import InferenceEndpointAgent
from data_collection_agents.dev_env_scanner_agent.infrastructure.security_hygiene import SecurityAgent

from data_collection_agents.dev_env_scanner_agent.ml_framework.data_validation import DataValidationAgent
from data_collection_agents.dev_env_scanner_agent.ml_framework.experiment_tracking import ExperimentTrackingAgent
from data_collection_agents.dev_env_scanner_agent.ml_framework.hyperparameter_optimization import HyperparameterOptimizationAgent
from data_collection_agents.dev_env_scanner_agent.ml_framework.ml_framework_agent import MLFrameworkAgent
from data_collection_agents.dev_env_scanner_agent.ml_framework.model_evaluation import ModelEvaluationAgent
from data_collection_agents.dev_env_scanner_agent.ml_framework.model_training import ModelTrainingAgent

from data_collection_agents.dev_env_scanner_agent.file_system.ci_cd import CICDAgent
from data_collection_agents.dev_env_scanner_agent.file_system.deployment import DeploymentAgent
from data_collection_agents.dev_env_scanner_agent.file_system.environment_config import EnvironmentConfigAgent
from data_collection_agents.dev_env_scanner_agent.file_system.experiment_detection import ExperimentDetectionAgent
from data_collection_agents.dev_env_scanner_agent.file_system.project_structure import ProjectStructureAgent
from data_collection_agents.dev_env_scanner_agent.file_system.test_detection import TestDetectionAgent

def _mk(model: str, temp: float, cls):
    return cls(model=model, temperature=temp)

def build_agents(model: str, temperature: float) -> Dict[str, Any]:
    return {
        # code
        "code.cyclomatic_complexity_band": _mk(model, temperature, CyclomaticComplexityAgent),
        "code.maintainability_band":       _mk(model, temperature, MaintainabilityAgent),
        "code.docstring_coverage_band":    _mk(model, temperature, DocstringCoverageAgent),
        "code.nested_loops_band":          _mk(model, temperature, NestedLoopsAgent),

        # infra
        "infra.parallel_patterns":         _mk(model, temperature, ParallelPatternsAgent),
        "infra.data_pipeline":             _mk(model, temperature, DataPipelineAgent),
        "infra.feature_engineering":       _mk(model, temperature, FeatureEngineeringAgent),
        "infra.security_hygiene":          _mk(model, temperature, SecurityAgent),
        "infra.inference_endpoint":        _mk(model, temperature, InferenceEndpointAgent),
        "infra.model_export":              _mk(model, temperature, ModelExportAgent),

        # ml
        "ml.framework_maturity":           _mk(model, temperature, MLFrameworkAgent),
        "ml.experiment_tracking":          _mk(model, temperature, ExperimentTrackingAgent),
        "ml.hpo_practice":                 _mk(model, temperature, HyperparameterOptimizationAgent),
        "ml.data_validation":              _mk(model, temperature, DataValidationAgent),
        "ml.training_practice":            _mk(model, temperature, ModelTrainingAgent),
        "ml.evaluation_practice":          _mk(model, temperature, ModelEvaluationAgent),

        "fs.ci_cd":            CICDAgent(model, temperature),
        "fs.deployment":       DeploymentAgent(model, temperature),
        "fs.environment":      EnvironmentConfigAgent(model, temperature),
        "fs.experiment_detect":ExperimentDetectionAgent(model, temperature),
        "fs.project_structure":ProjectStructureAgent(model, temperature),
        "fs.test_detection":   TestDetectionAgent(model, temperature),
    }

# tiny per-metric input filters (still use your provided code_snippets; no snapshots)
SLICE_RULES: Dict[str, Dict[str, Any]] = {
    "code.cyclomatic_complexity_band": {"k": 8, "filters": None},
    "code.maintainability_band":       {"k": 8, "filters": None},
    "code.docstring_coverage_band":    {"k": 8, "filters": None},
    "code.nested_loops_band":          {"k": 8, "filters": ("for ", "while ", "range(", "itertools")},

    "infra.parallel_patterns":         {"k": 6, "filters": ("thread", "multiprocess", "concurrent", "async def", "await", "ray")},
    "infra.data_pipeline":             {"k": 6, "filters": ("airflow", "prefect", "luigi", "argo", "kedro", "dag(")},
    "infra.feature_engineering":       {"k": 6, "filters": ("pipeline(", "columntransformer(", "featuretools", "tsfresh", "transform")},
    "infra.security_hygiene":          {"k": 8, "filters": ("secret", "token", "private_key", "password", "auth", "jwt", "hashlib", "crypt")},
    "infra.inference_endpoint":        {"k": 6, "filters": ("fastapi", "@app.", "flask", "@route", "grpc", "pydantic")},
    "infra.model_export":              {"k": 6, "filters": ("torch.save", "joblib", "pickle", "onnx", "SavedModel", "export")},

    "ml.framework_maturity":           {"k": 6, "filters": ("import torch", "tensorflow", "sklearn", "keras", "xgboost", "lightgbm")},
    "ml.experiment_tracking":          {"k": 6, "filters": ("mlflow", "wandb", "clearml", "log_metric", "log_artifact")},
    "ml.hpo_practice":                 {"k": 6, "filters": ("optuna", "ray.tune", "study", "grid", "random", "bayes")},
    "ml.data_validation":              {"k": 6, "filters": ("great_expectations", "evidently", "pandera", "validate", "schema")},
    "ml.training_practice":            {"k": 6, "filters": ("if __name__ == '__main__'", "train(", "Trainer(", "checkpoint", "seed")},
    "ml.evaluation_practice":          {"k": 6, "filters": ("roc_auc", "f1_", "precision", "recall", "calibration", "fairness")},

    "fs.ci_cd":            {"k": 0, "filters": None},  # file_paths only
    "fs.deployment":       {"k": 0, "filters": None},
    "fs.environment":      {"k": 0, "filters": None},
    "fs.experiment_detect":{"k": 0, "filters": None},
    "fs.project_structure":{"k": 0, "filters": None},
    "fs.test_detection":   {"k": 8, "filters": ("test", "pytest", "unittest")},
}

def slice_snippets(snips: List[str], k: int, filters: Optional[tuple[str, ...]]) -> List[str]:
    if not snips:
        return []
    if filters:
        filtered = [s for s in snips if any(f in s.lower() for f in filters)]
        if filtered:
            snips = filtered
    return snips[:k]