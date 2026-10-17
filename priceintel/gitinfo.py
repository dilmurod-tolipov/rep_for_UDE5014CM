"""Which code produced a run: commit hash and whether the working tree had uncommitted changes."""
import subprocess

from priceintel.config import REPO_ROOT


def git_state() -> tuple[str, bool]:
    """Returns (commit, dirty). ('unknown', True) if git is unavailable."""
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                                text=True, check=True, timeout=10).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True,
                                text=True, check=True, timeout=10).stdout.strip()
        return (commit if len(commit) == 40 else "unknown"), bool(status)
    except (OSError, subprocess.SubprocessError):
        return "unknown", True
