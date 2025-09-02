# agent_layer/tool_loader.py
import functools
from typing import Callable, Any
from agent_layer.validate import make_validated_metric
from cloud_infra_agent.agent_wrappers import run_metric

def load_function(metric_id: str) -> Callable[..., Any]:
    # make a function(ctx) that calls run_metric(ctx, metric_id)
    fn = functools.partial(run_metric, metric_id=metric_id)
    # use metric_id as the "name" for validation/category lookup
    return make_validated_metric(fn, metric_id)
