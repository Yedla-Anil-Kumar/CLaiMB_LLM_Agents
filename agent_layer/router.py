# agent_layer/router.py
from __future__ import annotations
from typing import Callable, Dict, Any
from .tool_loader_enterprise import load_tool

def route(fn_id: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Thin router for metric function ids."""
    return load_tool(fn_id)