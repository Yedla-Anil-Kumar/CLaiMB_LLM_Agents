#!/usr/bin/env python3
"""
Deterministic, LangChain-based MVP that:
- builds one repo snapshot (cheap, minimal context),
- runs 16 metric wrappers (your existing METRIC_ID set) through one tiny shared prompt,
- executes in dependency waves (topological) with RunnableParallel,
- validates clamped outputs,
- aggregates category + overall scores,
- persists a single JSON artifact per run in ./runs_code_repo_mvp/<run_id>.json.

How to run:
  pip install langchain langchain-openai python-dotenv
  export OPENAI_API_KEY=sk-...
  python mvp_code_repo_agent.py --repo /path/to/repo
"""

from __future__ import annotations
import argparse
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Iterable, Tuple, Callable, Optional
from dotenv import load_dotenv

# --- LangChain (single shared contract) ---
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnableParallel
from langchain.prompts import PromptTemplate

# ---- import your concrete micro-agents for snapshot mining (NOT used to score) ----
# these are used to cheaply infer snapshot slices; scoring is by the shared prompt
from data_collection_agents.dev_env_scanner_agent.file_system.ci_cd import CICDAgent
from data_collection_agents.dev_env_scanner_agent.file_system.deployment import DeploymentAgent
from data_collection_agents.dev_env_scanner_agent.file_system.environment_config import EnvironmentConfigAgent
from data_collection_agents.dev_env_scanner_agent.file_system.experiment_detection import ExperimentDetectionAgent
from data_collection_agents.dev_env_scanner_agent.file_system.project_structure import ProjectStructureAgent
from data_collection_agents.dev_env_scanner_agent.file_system.test_detection import TestDetectionAgent

from data_collection_agents.dev_env_scanner_agent.utils.file_utils import list_source_files, list_all_files

# ---------------------------
# 0) Single tiny LLM contract
# ---------------------------
STRICT_JSON_PROMPT = PromptTemplate.from_template(
    """You are evaluating one metric about a code repository snapshot.
Return ONLY strict JSON, no prose, with this exact shape:
{{"score": <int 1..5>, "rationale": "<one concise paragraph>", "gaps": ["<max 5>"]}}

Metric name: {metric_name}
Rubric (apply exactly): {rubric}

You will be given a minimal context slice relevant to this metric.
Use only the provided evidence; if insufficient to judge, give score 1 with a clear rationale.

Context:
{context}

Remember: JSON only. Keys: score, rationale, gaps.
"""
)

def call_llm_once(model: ChatOpenAI, metric_name: str, rubric: str, context: str) -> Dict[str, Any]:
    raw = model.invoke(STRICT_JSON_PROMPT.format(
        metric_name=metric_name, rubric=rubric, context=context
    )).content or ""
    # robust parse
    try:
        if "```json" in raw:
            s = raw.find("```json") + 7
            e = raw.find("```", s)
            raw = raw[s:e].strip()
        elif "```" in raw:
            s = raw.find("```") + 3
            e = raw.find("```", s)
            raw = raw[s:e].strip()
        obj = json.loads(raw)
    except Exception:
        # fallback: best-effort braces
        try:
            s = raw.find("{"); e = raw.rfind("}")
            obj = json.loads(raw[s:e+1]) if s != -1 and e != -1 and e > s else {}
        except Exception:
            obj = {}

    # clamp & tidy
    score = obj.get("score", 3)
    try:
        score = max(1, min(5, int(score)))
    except Exception:
        score = 3
    out = {
        "score": score,
        "score_0to100": score * 20,
        "rationale": str(obj.get("rationale", "No rationale."))[:1200].strip(),
        "gaps": list(map(str, obj.get("gaps", [])[:5])),
    }
    return out

# ---------------------------------------
# 1) Snapshot mining (minimal, cheap jog)
# ---------------------------------------
MAX_FILES = int(os.getenv("MVP_MAX_FILES", "40"))
MAX_SNIPPET_BYTES = int(os.getenv("MVP_MAX_SNIPPET_BYTES", "2400"))

def _head_tail(text: str, cap: int) -> str:
    if len(text) <= cap: return text
    half = cap // 2
    return text[:half] + "\n# ...\n" + text[-half:]

def read_snippets(paths: Iterable[Path]) -> List[str]:
    out: List[str] = []
    for p in paths:
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            txt = ""
        out.append(_head_tail(txt, MAX_SNIPPET_BYTES))
    return out

def collect_snapshot(repo_path: str) -> Dict[str, Any]:
    """One pass to gather the small slices all metric wrappers need."""
    src_paths = list(list_source_files(repo_path))
    src_paths = src_paths[:MAX_FILES]
    source_snippets = read_snippets(src_paths)

    all_paths = list(list_all_files(repo_path))

    # Use your existing detectors once each to set cheap signals in snapshot
    tests = TestDetectionAgent().evaluate(source_snippets)
    env   = EnvironmentConfigAgent().evaluate(all_paths[:400])
    ci    = CICDAgent().evaluate(all_paths[:400])
    dep   = DeploymentAgent().evaluate(all_paths[:400])
    exp   = ExperimentDetectionAgent().evaluate(all_paths[:400])
    proj  = ProjectStructureAgent().evaluate(all_paths[:400])

    return {
        "meta": {
            "repo_name": Path(repo_path).name,
            "file_count": len(all_paths),
            "py_files_sampled": len(src_paths),
        },
        "code_snippets": source_snippets,  # wrappers slice this further
        "fs_signals": {**tests, **env, **ci, **dep, **exp, **proj},
    }

# ---------------------------------------------------------
# 2) Wrappers (1 per metric) — each calls the SAME prompt
# ---------------------------------------------------------
# map: metric_name -> (rubric, slice_fn(snapshot)->context_str)
def _join(snips: List[str]) -> str:
    return "\n\n".join(f"--- Snippet {i+1} ---\n{s}" for i, s in enumerate(snips))

def _slice_first_k(snapshot: Dict[str, Any], k: int, keyword_filters: Optional[Tuple[str, ...]] = None) -> str:
    snips = snapshot["code_snippets"]
    if keyword_filters:
        filt = [s for s in snips if any(kw in s.lower() for kw in keyword_filters)]
        if filt:
            snips = filt
    return _join(snips[:k]) if snips else "NO_CODE_AVAILABLE"

WRAPPERS: Dict[str, Tuple[str, Callable[[Dict[str, Any]], str]]] = {
    # --------- CODE QUALITY ---------
    "code.cyclomatic_complexity_band": (
        "Use avg_complexity and distribution across low/med/high/very_high. "
        "5: avg≤5 & ≤10% high; 4: avg≤7 & ≤20%; 3: avg≤10 or 21–35%; 2: avg≤12 or 36–50%; 1: >12 or poor evidence.",
        lambda s: _slice_first_k(s, 8)
    ),
    "code.maintainability_band": (
        "Maintainability/readability/design jointly. "
        "5: all≥0.85 & consistent; 4: all≥0.75 or two≥0.80; 3: all≥0.60 mixed; 2: any<0.60; 1: smells dominate.",
        lambda s: _slice_first_k(s, 8)
    ),
    "code.docstring_coverage_band": (
        "Docstring coverage + quality. 5: cov≥0.90 & qual≥0.85; 4: cov≥0.80 & qual≥0.75; 3: cov≥0.65 & qual≥0.60; "
        "2: cov≥0.45 or qual≥0.45; 1: below or big gaps.",
        lambda s: _slice_first_k(s, 8)
    ),
    "code.nested_loops_band": (
        "Existence+depth+hotspots+alternatives. 5: no problems (depth≤2) or refactored; 4: some (≤3) with mitigations; "
        "3: notable (3–4) partial mitigations; 2: frequent deep (≥4); 1: widespread deep with perf risks.",
        lambda s: _slice_first_k(s, 8, ("for ", "while ", "range(", "itertools"))
    ),

    # --------- INFRA ---------
    "infra.parallel_patterns": (
        "Concurrency patterns correctness & safety (threading/multiprocessing/concurrent/asyncio/Ray). "
        "5: correct+pooling+timeouts+bounded queues+graceful; 4: minor gaps; 3: missing key safety; 2: misapplied; 1: dangerous/none.",
        lambda s: _slice_first_k(s, 6, ("thread", "multiprocess", "concurrent", "async def", "await", "ray"))
    ),
    "infra.inference_endpoint": (
        "Serving endpoints quality (FastAPI/Flask/gRPC): schemas, health/readiness, errors, async/batching, model load, logging.",
        lambda s: _slice_first_k(s, 6, ("fastapi", "@app.", "flask", "@route", "grpc", "pydantic"))
    ),
    "infra.model_export": (
        "Export/serialization completeness (versioning, signature, metadata/card). "
        "5: standardized export + signature + metadata; 4: reliable minor gaps; 3: ad-hoc; 2: risky; 1: no evidence.",
        lambda s: _slice_first_k(s, 6, ("torch.save", "joblib", "pickle", "onnx", "save", "export"))
    ),
    "infra.data_pipeline": (
        "DAG/flow reliability (schedules, retries/backoff, SLAs/alerts, validation, observability). "
        "5: full hooks; 4: good w/ minor gaps; 3: basic DAG; 2: brittle scripts; 1: none.",
        lambda s: _slice_first_k(s, 6, ("airflow", "prefect", "luigi", "argo", "kedro", "DAG("))
    ),
    "infra.feature_engineering": (
        "FE pipelines reproducibility/persistence/parity (sklearn pipelines, ColumnTransformer, featuretools, tsfresh).",
        lambda s: _slice_first_k(s, 6, ("Pipeline(", "ColumnTransformer(", "featuretools", "tsfresh", "transform"))
    ),
    "infra.security_hygiene": (
        "Secrets exposure, weak auth/crypto, unsafe validation, missing controls.",
        lambda s: _slice_first_k(s, 8, ("SECRET", "TOKEN", "PRIVATE_KEY", "password", "auth", "jwt", "hashlib", "crypt"))
    ),

    # --------- ML ---------
    "ml.data_validation": (
        "Schema/value/drift checks and CI gating.",
        lambda s: _slice_first_k(s, 6, ("great_expectations", "evidently", "pandera", "validate", "schema"))
    ),
    "ml.experiment_tracking": (
        "Params/metrics/artifacts/signature/lineage tracking quality.",
        lambda s: _slice_first_k(s, 6, ("mlflow", "wandb", "clearml", "log_metric", "log_artifact"))
    ),
    "ml.hpo_practice": (
        "HPO structure/rigor (strategy, seeds, persistence).",
        lambda s: _slice_first_k(s, 6, ("optuna", "ray.tune", "study", "search", "grid", "random"))
    ),
    "ml.framework_maturity": (
        "Clarity/consistency of framework usage (imports/idioms/interop).",
        lambda s: _slice_first_k(s, 6, ("import torch", "tensorflow", "sklearn", "keras", "xgboost", "lightgbm"))
    ),
    "ml.evaluation_practice": (
        "Evaluation breadth, calibration, fairness, reporting.",
        lambda s: _slice_first_k(s, 6, ("roc_auc", "f1_", "precision", "recall", "calibration", "fairness"))
    ),
    "ml.training_practice": (
        "Entrypoints, config-driven design, reproducibility, resume/checkpoints.",
        lambda s: _slice_first_k(s, 6, ("if __name__ == '__main__'", "train(", "Trainer(", "checkpoint", "seed"))
    ),
}

# -----------------------------------------
# 3) DAG registry (depends_on) & wave build
# -----------------------------------------
# Keep it small & sensible; deps ensure later metrics “see” early context if needed.
REGISTRY: Dict[str, Dict[str, Any]] = {
    # Level-0 (run first)
    "code.maintainability_band": {"depends_on": []},
    "code.docstring_coverage_band": {"depends_on": []},
    "code.cyclomatic_complexity_band": {"depends_on": []},
    "code.nested_loops_band": {"depends_on": []},

    # Level-1 (infra needs general code shape)
    "infra.parallel_patterns": {"depends_on": ["code.maintainability_band"]},
    "infra.data_pipeline": {"depends_on": ["code.maintainability_band"]},
    "infra.feature_engineering": {"depends_on": ["code.maintainability_band"]},
    "infra.security_hygiene": {"depends_on": ["code.maintainability_band"]},

    # Level-2 (serving/export reasonably after infra basics)
    "infra.inference_endpoint": {"depends_on": ["infra.parallel_patterns"]},
    "infra.model_export": {"depends_on": ["infra.feature_engineering"]},

    # Level-1 ML (independent from infra)
    "ml.framework_maturity": {"depends_on": []},
    "ml.experiment_tracking": {"depends_on": ["ml.framework_maturity"]},
    "ml.hpo_practice": {"depends_on": ["ml.experiment_tracking"]},
    "ml.data_validation": {"depends_on": ["ml.framework_maturity"]},
    "ml.training_practice": {"depends_on": ["ml.framework_maturity"]},
    "ml.evaluation_practice": {"depends_on": ["ml.training_practice"]},
}

def compute_waves(registry: Dict[str, Dict[str, Any]]) -> List[List[str]]:
    """Topological layering into waves."""
    remaining = {k: set(v.get("depends_on", [])) for k, v in registry.items()}
    waves: List[List[str]] = []
    visited = set()
    while remaining:
        ready = [n for n, deps in remaining.items() if deps <= visited]
        if not ready:
            # cycle or bad dep; run the rest in one wave deterministically
            ready = list(remaining.keys())
        waves.append(sorted(ready))
        for r in ready:
            visited.add(r)
            remaining.pop(r, None)
    return waves

# ----------------------------------------------------
# 4) Execution (RunnableParallel per wave) & scoring
# ----------------------------------------------------
CATEGORIES = {
    # Development Maturity
    "dev_maturity": {
        "metrics": [
            "code.cyclomatic_complexity_band",
            "code.maintainability_band",
            "code.docstring_coverage_band",
            "code.nested_loops_band",
            "infra.parallel_patterns",
            "infra.inference_endpoint",
            "infra.model_export",
            "infra.data_pipeline",
            "infra.feature_engineering",
            "infra.security_hygiene",
        ],
        "weight": 0.5,
    },
    # Innovation Pipeline
    "innovation": {
        "metrics": [
            "ml.framework_maturity",
            "ml.experiment_tracking",
            "ml.hpo_practice",
            "ml.data_validation",
            "ml.training_practice",
            "ml.evaluation_practice",
        ],
        "weight": 0.5,
    },
}

def run_once(repo_path: str, model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    load_dotenv()
    snapshot = collect_snapshot(repo_path)

    # shared LLM client (temp=0 for deterministic behavior)
    llm = ChatOpenAI(model=model_name, temperature=0)

    # prepare waves
    waves = compute_waves(REGISTRY)

    # storage
    metric_results: Dict[str, Dict[str, Any]] = {}

    # run wave-by-wave
    for wave in waves:
        tasks = {}
        for metric in wave:
            rubric, slicer = WRAPPERS[metric]
            ctx = slicer(snapshot)
            tasks[metric] = (lambda m=metric, r=rubric, c=ctx: call_llm_once(llm, m, r, c))
        # RunnableParallel expects callables -> we wrap with lambda
        runnable = RunnableParallel(**{k: (lambda fn=v: fn()) for k, v in tasks.items()})
        res: Dict[str, Dict[str, Any]] = runnable.invoke({})
        metric_results.update(res)

    # lightweight validation again + mirror legacy band (keep your ecosystem happy)
    for m, obj in metric_results.items():
        sc = int(obj.get("score", 3))
        obj["score"] = max(1, min(5, sc))
        obj["band"] = obj["score"]
        obj.setdefault("gaps", [])
        obj.setdefault("rationale", "No rationale.")

    # category & overall aggregation
    cat_scores: Dict[str, float] = {}
    for cat, cfg in CATEGORIES.items():
        scores = [metric_results[m]["score"] for m in cfg["metrics"] if m in metric_results]
        cat_scores[cat] = round(sum(scores) / max(1, len(scores)), 2)

    overall = round(
        CATEGORIES["dev_maturity"]["weight"] * cat_scores.get("dev_maturity", 0)
        + CATEGORIES["innovation"]["weight"] * cat_scores.get("innovation", 0),
        2,
    )

    return {
        "run_id": str(uuid.uuid4())[:8],
        "repo": Path(repo_path).name,
        "meta": snapshot["meta"],
        "fs_signals": snapshot["fs_signals"],  # helpful context traces
        "waves": waves,
        "metrics": metric_results,             # {metric_name: {score, rationale, gaps, band, score_0to100}}
        "category_scores": cat_scores,         # dev_maturity, innovation
        "overall_score": overall,
    }

# --------------------------------
# 5) Persistence (one JSON / run)
# --------------------------------
def persist(result: Dict[str, Any], out_dir: str = "runs_code_repo_mvp") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    run_id = result.get("run_id") or str(int(time.time()))
    out = Path(out_dir) / f"{result['repo']}_{run_id}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return out

# ----------------
# CLI entry point
# ----------------
def main():
    parser = argparse.ArgumentParser(description="Deterministic Code Repo Scanner (LangChain MVP)")
    parser.add_argument("--repo", required=True, help="Path to local git repository")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()

    result = run_once(args.repo, model_name=args.model)
    path = persist(result)
    print(f"✅ wrote: {path}")
    print(f"📊 overall: {result['overall_score']} (dev={result['category_scores']['dev_maturity']}, "
          f"innovation={result['category_scores']['innovation']})")

if __name__ == "__main__":
    main()