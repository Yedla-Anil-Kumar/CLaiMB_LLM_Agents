# agent_layer/router.py
from __future__ import annotations
from typing import Dict, List
from langchain_core.runnables import RunnableLambda
from .tool_loader import load_tool

def route(metric_id: str) -> RunnableLambda:
    """Return a Runnable that accepts a snapshot dict and produces JSON for the metric."""
    return RunnableLambda(load_tool(metric_id))

def route_many(metric_ids: List[str]) -> Dict[str, RunnableLambda]:
    return {mid: route(mid) for mid in metric_ids}