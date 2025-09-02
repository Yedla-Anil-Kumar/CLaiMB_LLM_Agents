# cloud_infra_agent/agent_wrappers.py
from typing import Dict, Any
import os
from pathlib import Path

from .metric_input_loader import load_metric_input
from .base_agents import BaseMicroAgent
from .call_llm_ import call_llm

def _agent() -> BaseMicroAgent:
    return BaseMicroAgent(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

def _resolve_task_input(metric_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    # Prefer explicit params
    if isinstance(ctx, dict):
        p = ctx.get("params")
        if isinstance(p, dict) and p:
            return p
        # If caller passed raw JSON directly, accept it
        if ctx:
            return ctx

    # Fallback to samples for dev/demo
    sample = (ctx or {}).get("sample_name", "healthy")
    data_root = Path(__file__).resolve().parent / "Data"
    return load_metric_input(sample_name=sample, metric_id=metric_id, base_dir=data_root)

def run_metric(ctx: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
    """Canonical entry: run one metric by dotted id."""
    task_input = _resolve_task_input(metric_id, ctx)
    out = call_llm(_agent(), metric_id, task_input) or {}
    out.setdefault("metric_id", metric_id)  # keep dotted id in output
    return out
