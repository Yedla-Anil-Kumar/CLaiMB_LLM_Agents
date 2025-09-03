# mvp/__init__.py
from __future__ import annotations
from typing import Any, Dict, Tuple
from pathlib import Path
from workflows.enterprise_workflow import run_workflow

def run_once(run_id: str | None = None, verbose: bool = True) -> Tuple[Path, Dict[str, Any]]:
    """
    Public entrypoint, as requested by mentor doc:
      from mvp import run_once
      run_once("enterprise-scan-2025-09-01T0900", verbose=True)
    """
    return run_workflow(run_id=run_id, verbose=verbose)