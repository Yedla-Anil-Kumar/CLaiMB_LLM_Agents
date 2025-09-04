# # cloud_infra_agent/agent_wrappers.py
# from typing import Dict, Any
# import os
# from pathlib import Path

# from .metric_input_loader import load_metric_input
# from .base_agents import BaseMicroAgent
# from .call_llm_ import call_llm

# def _agent() -> BaseMicroAgent:
#     return BaseMicroAgent(
#         model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
#         temperature=0.0,
#         api_key=os.getenv("OPENAI_API_KEY"),
#     )

# def _resolve_task_input(metric_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
#     # Prefer explicit params
#     if isinstance(ctx, dict):
#         p = ctx.get("params")
#         if isinstance(p, dict) and p:
#             return p
#         # If caller passed raw JSON directly, accept it
#         if ctx:
#             return ctx

#     # Fallback to samples for dev/demo
#     sample = (ctx or {}).get("sample_name", "healthy")
#     data_root = Path(__file__).resolve().parent / "Data"
#     return load_metric_input(sample_name=sample, metric_id=metric_id, base_dir=data_root)

# def run_metric(ctx: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
#     """Canonical entry: run one metric by dotted id."""
#     task_input = _resolve_task_input(metric_id, ctx)
#     out = call_llm(_agent(), metric_id, task_input) or {}
#     out.setdefault("metric_id", metric_id)  # keep dotted id in output
#     return out

# cloud_infra_agent/agent_wrappers.py
from typing import Dict, Any
import os
from pathlib import Path
from .base_agents import BaseMicroAgent
from .call_llm_ import call_llm

def _agent() -> BaseMicroAgent:
    return BaseMicroAgent(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

# def _resolve_task_input(metric_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
#     # Prefer explicit params
#     if isinstance(ctx, dict):
#         p = ctx.get("params")
#         if isinstance(p, dict) and p:
#             return p
#         # If caller passed raw JSON directly, accept it
#         if ctx:
#             return ctx
def _resolve_task_input(metric_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Shape the final 'task_input' that goes into the prompt builder.

    Expected shapes coming from the orchestrator/validator:
    - Preferred: ctx == {"params": {...}, "deps": {...}}  # deps optional
    - Legacy raw dict: ctx == {...}  → becomes {"params": ctx}
    - Wrapper-pass-through: ctx == {"context": {...}} → unwrap context
    - Fallback: load mapped sample file for this metric.
    """
    base_ctx = ctx or {}

    # Unwrap if validator/wrapper passed {"context": {...}}
    if isinstance(base_ctx, dict) and "context" in base_ctx and isinstance(base_ctx["context"], dict):
        base_ctx = base_ctx["context"]

    if isinstance(base_ctx, dict):
        has_params = isinstance(base_ctx.get("params"), dict)
        has_deps   = isinstance(base_ctx.get("deps"), dict)

        # ✅ Preferred path: pass through params/deps as-is (NO extra wrapping)
        if has_params or has_deps:
            out: Dict[str, Any] = {}
            if has_params:
                out["params"] = base_ctx["params"]
            if has_deps:
                out["deps"] = base_ctx["deps"]
            return out  # <<< EARLY RETURN so we don't wrap again

        # ✅ Legacy path: whole dict is raw params
        if base_ctx:
            return {"params": base_ctx}

    # # ✅ Fallback: load sample inputs (only if nothing else was provided)
    # # (you already import load_metric_input and Path at top)
    # samples_dir = Path(__file__).resolve().parent / "Data"
    # return load_metric_input(sample_name=base_ctx.get("sample_name", "healthy"),
    #                          metric_id=metric_id,
    #                          base_dir=samples_dir)
def run_metric(ctx: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
    """Canonical entry: run one metric by dotted id."""
    task_input = _resolve_task_input(metric_id, ctx)
    out = call_llm(_agent(), metric_id, task_input) or {}
    out.setdefault("metric_id", metric_id)  # keep dotted id in output
    return out
