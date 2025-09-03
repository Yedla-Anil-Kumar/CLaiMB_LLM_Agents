# agent_layer/router_mlops.py
from typing import Dict, Any, Callable
from .tool_loader_mlops import load_tool

def route(metric_id: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    return load_tool(metric_id)