# workflows/code_repo_workflow.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, List

# add root for imports
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_layer.orchestrator import run as run_agent  # noqa: E402

# If you already have these utilities, import them. Otherwise, keep these minimal helpers.
def _list_source_files(repo_path: Path) -> List[Path]:
    return [p for p in repo_path.rglob("*.py") if p.is_file()]

def _list_all_files(repo_path: Path) -> List[str]:
    return [str(p) for p in repo_path.rglob("*") if p.is_file()]

MAX_FILES_PER_REPO = 50
MAX_SNIPPET_BYTES  = 3000

def _read_snippets(paths: Iterable[Path]) -> List[str]:
    out: List[str] = []
    half = max(1, MAX_SNIPPET_BYTES // 2)
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        if len(text) <= MAX_SNIPPET_BYTES:
            out.append(text)
        else:
            out.append(text[:half] + "\n# ...\n" + text[-half:])
    return out

def collect_snapshot(repo_dir: Path) -> Dict[str, Any]:
    src = _list_source_files(repo_dir)
    # prefer interesting files first
    keywords = ("src/", "train", "eval", "serve", "api", "pipeline", "dag", "flow", "inference")
    pri = [p for p in src if any(k in str(p).lower() for k in keywords)]
    seen = set()
    ordered: List[Path] = []
    for p in pri + src:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    picked = ordered[:MAX_FILES_PER_REPO]

    snapshot = {
        "code_snippets": _read_snippets(picked),
        "file_paths": _list_all_files(repo_dir),
    }
    return snapshot

def run_workflow(repo_path: str) -> Dict[str, Any]:
    repo_dir = Path(repo_path).resolve()
    snapshot = collect_snapshot(repo_dir)
    return run_agent(snapshot, out_dir=Path("runs_code_repo_mvp"))