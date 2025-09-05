#!/usr/bin/env python3
"""Run the Code Repo Agent on a single repo (URL or local path) and write one JSON."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple
from urllib.parse import urlparse

from dotenv import load_dotenv

# ---- Make project root importable (so imports resolve when run as a module) ----
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --------------------------------------------------------------------------------

from dev_env_scanner_agent.orchestrator import MicroAgentOrchestrator  # noqa: E402
from dev_env_scanner_agent.logging_utils import setup_logger           # noqa: E402


def _is_url(s: str) -> bool:
    try:
        u = urlparse(s)
        return bool(u.scheme and u.netloc)
    except Exception:
        return False


def _split_owner_repo(path: str) -> Tuple[str, str]:
    # path like '/owner/repo.git' or '/group/subgroup/project.git'
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return ("unknown_owner", "unknown_repo")
    owner = parts[-2] if len(parts) >= 2 else "unknown_owner"
    repo = parts[-1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return (owner, repo)


def _clone_one(url: str, base_dir: Path, update_existing: bool = True, depth: int = 1) -> Path:
    """
    Clone a single URL under base_dir/<host>/<owner>/<repo>.
    If it already exists, optionally pull. Returns the local repo path.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "unknown").lower()
    owner, repo = _split_owner_repo(parsed.path or "")
    dest = base_dir / host / owner / repo
    dest.parent.mkdir(parents=True, exist_ok=True)

    if (dest / ".git").exists():
        if update_existing:
            try:
                subprocess.run(
                    ["git", "-C", str(dest), "pull", "--rebase", "--autostash"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                print(f"🔄 Updated: {dest}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  git pull failed for {dest}: {e.stderr.strip()}")
        else:
            print(f"⏭️  Skipping update (exists): {dest}")
        return dest

    try:
        cmd = ["git", "clone"]
        if depth and depth > 0:
            cmd.extend(["--depth", str(depth)])
        cmd.extend([url, str(dest)])
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(f"📥 Cloned {url} → {dest}")
        return dest
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone {url}: {e.stderr.strip()}") from e


def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _default_out_path(repo_arg: str, repo_dir: Path) -> Path:
    if _is_url(repo_arg):
        _, repo = _split_owner_repo(urlparse(repo_arg).path or "")
    else:
        repo = repo_dir.name or "repo"
    safe_repo = repo.replace("/", "_")
    out_dir = Path("runs_code_repo_mvp")
    out_dir.mkdir(parents=True, exist_ok=True)
    i = 1
    while True:
        f = out_dir / f"{safe_repo}_{i}.json"
        if not f.exists():
            return f
        i += 1




def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run Code Repo Agent on ONE repo (URL or local path) and write JSON."
    )
    p.add_argument(
        "--repo",
        required=True,
        help="Git URL or local path to the repository root (exactly one).",
    )
    p.add_argument(
        "--out",
        default="",
        help="Exact JSON file path to write. If omitted, a default under runs_code_repo_mvp/ is used.",
    )
    p.add_argument(
        "--clone-base",
        default="input_repos",
        help="Where to place the cloned repo when --repo is a URL (default: input_repos).",
    )
    p.add_argument(
        "--no-update-existing",
        action="store_true",
        help="If set and the repo already exists locally, skip 'git pull'.",
    )
    p.add_argument(
        "--clone-depth",
        type=int,
        default=1,
        help="Shallow clone depth (default 1). Use 0 or negative for full clone.",
    )
    p.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="OpenAI model; overrides env OPENAI_MODEL if provided.",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="LLM sampling temperature (mentor asked for deterministic: use 0.0).",
    )
    return p.parse_args()


def main() -> None:
    load_dotenv()
    setup_logger("logs/dev_env_scanner.log", level="INFO", serialize=False)
    args = parse_args()

    # 1) Resolve repo location (clone if URL, otherwise use local path)
    if _is_url(args.repo):
        base_dir = Path(args.clone_base).resolve()
        base_dir.mkdir(parents=True, exist_ok=True)
        repo_dir = _clone_one(
            url=args.repo,
            base_dir=base_dir,
            update_existing=(not args.no_update_existing),
            depth=args.clone_depth,
        )
    else:
        repo_dir = Path(args.repo).resolve()
        if not repo_dir.exists():
            raise FileNotFoundError(f"Repo path not found: {repo_dir}")
        if not (repo_dir / ".git").exists():
            print(f"⚠️  Warning: {repo_dir} does not look like a git repo (no .git). Proceeding anyway.")

    # 2) Run the orchestrator on JUST this repo
    orchestrator = MicroAgentOrchestrator(model=args.model, temperature=args.temperature)
    result: Dict = orchestrator.analyze_repo(str(repo_dir))

    # 3) Determine output path (exactly --out if provided, else default)
    out_file = Path(args.out).resolve() if args.out else _default_out_path(args.repo, repo_dir)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\n=== Code Repo Agent (single-repo) ===")
    print(f"Repo: {repo_dir}")
    print(f"Wrote: {out_file}")
    mb = result.get("metric_breakdown") or {}
    print(f"Metrics: {len(mb)}")


if __name__ == "__main__":
    main()