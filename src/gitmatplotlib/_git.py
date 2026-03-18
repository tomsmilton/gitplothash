"""Git info retrieval via subprocess."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitNotFoundError(RuntimeError):
    """Raised when git is not installed or cwd is not inside a git repo."""


@dataclass(frozen=True)
class GitInfo:
    """Information about the current git state."""

    commit: str
    dirty: bool
    branch: str | None
    repo: str | None

    def label(
        self,
        fmt: str = "{commit}{dirty}",
        dirty_marker: str = "*",
    ) -> str:
        """Format git info into a display string.

        Available placeholders: {commit}, {dirty}, {branch}, {repo}
        """
        return fmt.format(
            commit=self.commit,
            dirty=dirty_marker if self.dirty else "",
            branch=self.branch or "detached",
            repo=self.repo or "unknown",
        )


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=5,
    )


def _parse_repo_name(remote_url: str) -> str:
    """Extract 'owner/repo' from a git remote URL.

    Handles both SSH (git@github.com:owner/repo.git) and
    HTTPS (https://github.com/owner/repo.git) formats.
    """
    url = remote_url.strip()
    # SSH format: git@github.com:owner/repo.git
    if ":" in url and url.startswith("git@"):
        path = url.split(":", 1)[1]
    else:
        # HTTPS format: strip the scheme and host
        # e.g. https://github.com/owner/repo.git -> owner/repo.git
        parts = url.split("/")
        # Take last two parts: owner/repo.git
        path = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]

    # Remove .git suffix
    if path.endswith(".git"):
        path = path[:-4]
    return path


def get_git_info(repo_path: str | Path | None = None) -> GitInfo:
    """Get git info for the repo containing repo_path.

    Parameters
    ----------
    repo_path : str, Path, or None
        Path within the git repository. Defaults to cwd.

    Returns
    -------
    GitInfo

    Raises
    ------
    GitNotFoundError
        If git is not available or the path is not in a git repo.
    """
    cwd = Path(repo_path) if repo_path else Path.cwd()

    # Get short commit hash
    result = _run_git(["rev-parse", "--short", "HEAD"], cwd)
    if result.returncode != 0:
        raise GitNotFoundError(
            f"Not a git repository or git not installed: {result.stderr.strip()}"
        )
    commit = result.stdout.strip()

    # Check dirty status: staged/unstaged changes
    diff_result = _run_git(["diff", "--quiet", "HEAD"], cwd)
    dirty = diff_result.returncode != 0

    # Also check for untracked files
    if not dirty:
        status_result = _run_git(["status", "--porcelain"], cwd)
        if status_result.stdout.strip():
            dirty = True

    # Get branch name
    branch_result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    if branch == "HEAD":
        branch = None  # Detached HEAD

    # Get repo name from remote
    remote_result = _run_git(["remote", "get-url", "origin"], cwd)
    if remote_result.returncode == 0 and remote_result.stdout.strip():
        repo = _parse_repo_name(remote_result.stdout)
    else:
        # Fallback to directory name of the repo root
        root_result = _run_git(["rev-parse", "--show-toplevel"], cwd)
        if root_result.returncode == 0:
            repo = Path(root_result.stdout.strip()).name
        else:
            repo = None

    return GitInfo(commit=commit, dirty=dirty, branch=branch, repo=repo)
