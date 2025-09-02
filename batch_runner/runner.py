import os, sys, json, glob, yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from .engine_bridge import run_engine_on_batch

# If your batch JSONs live in nested subfolders (e.g., inputs/*.json), set True.
# You said your files are DIRECTLY in the batch folder (e.g., .../healthy/availability_incidents.json),
# so leave this False.
RECURSIVE_INPUTS = False

# ---------- utils ----------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm(p: str) -> str:
    # Normalize to absolute, resolved path for consistent state keys
    return str(Path(p).resolve())

def _load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _load_state(state_file: str) -> Dict[str, Any]:
    if not os.path.exists(state_file):
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        return {"processed": {}}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        state = {"processed": {}}
    # normalize existing keys once so comparisons are consistent
    proc = state.get("processed", {}) or {}
    state["processed"] = {_norm(k): v for k, v in proc.items()}
    return state

def _save_state(state_file: str, state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def _list_batch_dirs(inputs_root: str) -> List[str]:
    try:
        return [
            _norm(os.path.join(inputs_root, d))
            for d in os.listdir(inputs_root)
            if os.path.isdir(os.path.join(inputs_root, d))
        ]
    except FileNotFoundError:
        print(f"[runner] Inputs root does not exist: {inputs_root}")
        return []

def _matched_files(batch_dir: str, patterns: List[str]) -> List[str]:
    matches: List[str] = []
    pats = patterns or ["*.json"]
    if RECURSIVE_INPUTS:
        for root, _, _ in os.walk(batch_dir):
            for pat in pats:
                for p in glob.glob(os.path.join(root, pat)):
                    matches.append(p)
    else:
        for pat in pats:
            for p in glob.glob(os.path.join(batch_dir, pat)):
                matches.append(p)
    return matches

def _has_required_files(batch_dir: str, patterns: List[str]) -> bool:
    return len(_matched_files(batch_dir, patterns)) > 0

def _lock_path(batch_dir: str) -> str:
    return os.path.join(batch_dir, ".lock")

def _why_excluded(d_abs: str, processed_abs: set, patterns: List[str]) -> str | None:
    """Return reason if excluded, else None (i.e., it's a candidate)."""
    if d_abs in processed_abs:
        return "already processed"
    if os.path.exists(_lock_path(d_abs)):
        return "locked"
    if not _has_required_files(d_abs, patterns):
        return "no input files"
    return None

def _pick_next_pending_batch(inputs_root: str, state: Dict[str, Any], patterns: List[str]) -> Optional[str]:
    inputs_root = _norm(inputs_root)
    processed_abs = set((state.get("processed") or {}).keys())

    subdirs = _list_batch_dirs(inputs_root)
    print("[runner] subdirs:", [os.path.basename(s) for s in subdirs])

    # Show explicit skip reasons + sample of matches for visibility
    for d in subdirs:
        why = _why_excluded(d, processed_abs, patterns)
        name = os.path.basename(d)
        if why:
            extra = ""
            if why == "no input files":
                m = _matched_files(d, patterns)
                extra = f" (found 0; patterns={patterns})"
            print(f"[runner] skip {name}: {why}{extra}")

    candidates = [d for d in subdirs if _why_excluded(d, processed_abs, patterns) is None]
    print("[runner] pending candidates:", [os.path.basename(s) for s in candidates])

    if not candidates:
        return None

    # Policy: pick the most recently modified pending folder (newest first)
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]

# ---------- main ----------

def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent  # project root
    cfg = _load_config(str(Path(__file__).resolve().parent / "config.yaml"))

    inputs_root  = _norm(os.path.join(repo_root, cfg.get("inputs_root",  "CloudInfraAgent/Data/Inputs")))
    outputs_root = _norm(os.path.join(repo_root, cfg.get("outputs_root", "CloudInfraAgent/Data/Outputs")))
    state_file   = _norm(os.path.join(repo_root, cfg.get("state_file",   "CloudInfraAgent/Data/state/processed.json")))
    patterns     = cfg.get("file_glob_patterns", ["*.json"])
    engine_cmd   = cfg.get("engine_command") or ""
    engine_call  = cfg.get("engine_callable") or ""

    print(f"[runner] Using inputs_root={inputs_root}")
    print(f"[runner] Using outputs_root={outputs_root}")
    print(f"[runner] Using state_file={state_file}")
    print(f"[runner] Using engine_callable={engine_call or '(none)'}")
    print(f"[runner] Using engine_command={engine_cmd or '(none)'}")

    state = _load_state(state_file)
    batch_dir = _pick_next_pending_batch(inputs_root, state, patterns)
    if not batch_dir:
        print("[runner] No pending batches to process.")
        return 0

    lock = _lock_path(batch_dir)
    if os.path.exists(lock):
        print(f"[runner] Batch is locked (already processing?): {batch_dir}")
        return 0

    Path(lock).write_text(_now_iso())
    print(f"[runner] Locked batch: {batch_dir}")

    try:
        batch_name = os.path.basename(batch_dir.rstrip(os.sep))
        out_dir = _norm(os.path.join(outputs_root, batch_name))
        os.makedirs(out_dir, exist_ok=True)

        rc = run_engine_on_batch(batch_dir, out_dir, engine_cmd, engine_call)
        if rc != 0:
            print(f"[runner] Engine failed with return code {rc}")
            return rc

        # Mark processed with normalized absolute path
        state.setdefault("processed", {})[_norm(batch_dir)] = {
            "processed_at": _now_iso(),
            "output_dir": out_dir,
            "return_code": rc,
        }
        _save_state(state_file, state)

        print(f"[runner] SUCCESS for batch {batch_dir} → {out_dir}/result.json")
        return 0
    finally:
        try:
            os.remove(lock)
            print(f"[runner] Unlocked batch: {batch_dir}")
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    sys.exit(main())
