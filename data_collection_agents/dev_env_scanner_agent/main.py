#!/usr/bin/env python3
"""Run LLM micro-agents across local or URL-provided repos (clones into provider buckets)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import subprocess
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from dotenv import load_dotenv

# ---- Make project root importable (so imports resolve when run from scripts/) ----
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ---------------------------------------------------------------------------------

from dev_env_scanner_agent.orchestrator import (  # noqa: E402
    MicroAgentOrchestrator,
)
from dev_env_scanner_agent.logging_utils import setup_logger  # noqa: E402


# ----------------------------- Repo discovery ----------------------------- #
def find_git_repos(base: Path) -> Iterable[Path]:
    """Yield repo roots that contain a .git directory."""
    for root, dirs, _ in os.walk(base):
        if ".git" in dirs:
            yield Path(root)
            # Do not descend into nested repos beneath this one
            dirs.clear()


# ----------------------------- URL cloning -------------------------------- #
def _host_bucket(host: str) -> str:
    h = host.lower()
    if "github.com" in h:
        return "Github_repos"
    if "gitlab" in h:
        return "Gitlab_repos"
    return "Other_repos"


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


def _clone_or_update_repo(url: str, base_dir: Path, update_existing: bool = True, depth: int = 1) -> Tuple[Path, bool]:
    """
    Clone a single repo URL under a provider bucket. If exists, optionally pull.
    Returns (repo_path, did_clone).
    """
    parsed = urlparse(url)
    host = parsed.hostname or "unknown"
    bucket = _host_bucket(host)

    owner, repo = _split_owner_repo(parsed.path or "")
    # For "Other" hosts, keep host as extra grouping to avoid collisions
    parent = base_dir / bucket
    if bucket == "Other_repos":
        parent = parent / host
    dest = parent / owner / repo
    dest.parent.mkdir(parents=True, exist_ok=True)

    git_dir = dest / ".git"
    if git_dir.exists():
        if update_existing:
            try:
                subprocess.run(
                    ["git", "-C", str(dest), "pull", "--rebase", "--autostash"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                print(f"🔄 Updated existing repo: {dest}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  git pull failed for {dest}: {e.stderr.strip()}")
        else:
            print(f"⏭️  Skipping update (exists): {dest}")
        return dest, False

    # Clone fresh
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
        return dest, True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone {url}: {e.stderr.strip()}")
        return dest, False


def _parse_urls_arg(urls: List[str]) -> List[str]:
    out: List[str] = []
    for u in urls or []:
        # allow comma-separated blobs
        for part in str(u).split(","):
            s = part.strip()
            if s:
                out.append(s)
    return out


def clone_repos_from_inputs(
    base_dir: Path,
    urls: List[str],
    urls_file: str | None,
    update_existing: bool = True,
    depth: int = 1,
) -> List[Path]:
    """Clone or update all URLs; return list of repo paths."""
    all_urls: List[str] = []
    all_urls.extend(_parse_urls_arg(urls))
    if urls_file:
        p = Path(urls_file)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    all_urls.append(line)

    if not all_urls:
        return []

    repo_paths: List[Path] = []
    for u in all_urls:
        dest, ok = _clone_or_update_repo(u, base_dir, update_existing=update_existing, depth=depth)
        if (dest / ".git").exists():
            repo_paths.append(dest)
    return repo_paths


# --------------------------- Per-repo scanning ---------------------------- #
def scan_single_repo(
    repo_path: Path,
    model: str,
    temperature: float,
    per_repo_dir: Path,
) -> Tuple[str, Dict]:
    """Scan one repository with a fresh orchestrator instance and return a consolidated object:
       { "agent": "...", "metric_breakdown": { "<metric_id>": {...} } }"""
    orchestrator = MicroAgentOrchestrator(model=model, temperature=temperature)
    result = orchestrator.analyze_repo(str(repo_path))

    # Write one valid JSON object per repo
    per_repo_dir.mkdir(parents=True, exist_ok=True)
    out_file = per_repo_dir / f"{repo_path.name}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return repo_path.name, result


# ------------------------------- CLI ------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clone GitHub/GitLab URLs into provider buckets then run micro-agents in parallel."
    )
    parser.add_argument(
        "--base",
        default="input_repos",
        help="Base folder for clones & scanning (default: input_repos).",
    )
    parser.add_argument(
        "--urls",
        nargs="*",
        default=[],
        help="One or more repo URLs (space- or comma-separated). Example: --urls https://github.com/org/repo https://gitlab.com/group/proj",
    )
    parser.add_argument(
        "--urls-file",
        default="",
        help="Path to a file containing repo URLs (newline-separated; # for comments).",
    )
    parser.add_argument(
        "--no-update-existing",
        action="store_true",
        help="If set, skip 'git pull' for already-cloned repos.",
    )
    parser.add_argument(
        "--clone-depth",
        type=int,
        default=1,
        help="Shallow clone depth (default 1). Use 0 or negative for full clone.",
    )
    parser.add_argument(
        "--out",
        default="data/micro_agents/all_results.json",
        help="Aggregate JSON output path.",
    )
    parser.add_argument(
        "--per-repo-dir",
        default="data/per_repo_outputs",
        help="Directory to store per-repo JSON results.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="OpenAI model; overrides env OPENAI_MODEL if provided.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="LLM sampling temperature.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=min(8, (os.cpu_count() or 4) * 2),
        help="Maximum parallel workers (default: min(8, 2*CPU)).",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    setup_logger("logs/dev_env_scanner.log", level="INFO", serialize=False)
    args = parse_args()

    base_dir = Path(args.base).resolve()
    out_path = Path(args.out).resolve()
    per_repo_dir = Path(args.per_repo_dir).resolve()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    per_repo_dir.mkdir(parents=True, exist_ok=True)
    base_dir.mkdir(parents=True, exist_ok=True)

    # 1) Clone from provided URLs (if any) into provider buckets
    cloned = clone_repos_from_inputs(
        base_dir=base_dir,
        urls=args.urls,
        urls_file=args.urls_file or None,
        update_existing=(not args.no_update_existing),
        depth=args.clone_depth,
    )
    if cloned:
        print(f"📚 Prepared {len(cloned)} repos from URLs under {base_dir}")

    # 2) Discover all repos under base (including newly cloned)
    repos: List[Path] = list(find_git_repos(base_dir))
    print(f"🔍 Found {len(repos)} repos under {base_dir}\n")

    aggregate: List[Dict] = []
    errors: List[Tuple[str, str]] = []

    # 3) Scan in parallel
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(
                scan_single_repo,
                repo_path,
                args.model,
                args.temperature,
                per_repo_dir,
            ): repo_path
            for repo_path in repos
        }

        for future in as_completed(futures):
            repo_path = futures[future]
            name = repo_path.name
            try:
                repo_name, result = future.result()
                mb = result.get("metric_breakdown", {}) or {}
                print(f"✅ {repo_name:<30} wrote {len(mb)} metrics")
                aggregate.append({
                    "repo": repo_name,
                    "agent": result.get("agent", "micro_agent_orchestrator"),
                    "metric_breakdown": mb,
                })
            except Exception as exc:
                msg = f"{type(exc).__name__}: {exc}"
                print(f"❌ Error scanning {name}: {msg}")
                errors.append((name, msg))

    # 4) Write aggregate
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Per-repo results written to: {per_repo_dir}")
    print(f"🧾 Aggregate JSON written to : {out_path}")
    if errors:
        print("\n⚠️  Repos with errors:")
        for name, msg in errors:
            print(f"   - {name}: {msg}")


if __name__ == "__main__":
    main()