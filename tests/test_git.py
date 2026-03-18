"""Tests for git info retrieval."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from gitmatplotlib._git import GitInfo, GitNotFoundError, _parse_repo_name, get_git_info


class TestGitInfo:
    def test_label_clean(self):
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        assert info.label() == "abc1234"

    def test_label_dirty(self):
        info = GitInfo(commit="abc1234", dirty=True, branch="main", repo="owner/repo")
        assert info.label() == "abc1234*"

    def test_label_custom_dirty_marker(self):
        info = GitInfo(commit="abc1234", dirty=True, branch="main", repo="owner/repo")
        assert info.label(dirty_marker=" (dirty)") == "abc1234 (dirty)"

    def test_label_with_branch(self):
        info = GitInfo(commit="abc1234", dirty=False, branch="feature", repo="owner/repo")
        assert info.label(fmt="{branch}@{commit}{dirty}") == "feature@abc1234"

    def test_label_with_repo(self):
        info = GitInfo(commit="abc1234", dirty=True, branch="main", repo="owner/repo")
        assert info.label(fmt="{repo} {commit}{dirty}") == "owner/repo abc1234*"

    def test_label_detached_head(self):
        info = GitInfo(commit="abc1234", dirty=False, branch=None, repo=None)
        assert info.label(fmt="{branch}@{commit}") == "detached@abc1234"

    def test_label_no_repo(self):
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo=None)
        assert info.label(fmt="{repo}:{commit}") == "unknown:abc1234"


class TestParseRepoName:
    def test_ssh_url(self):
        assert _parse_repo_name("git@github.com:owner/repo.git") == "owner/repo"

    def test_https_url(self):
        assert _parse_repo_name("https://github.com/owner/repo.git") == "owner/repo"

    def test_https_no_git_suffix(self):
        assert _parse_repo_name("https://github.com/owner/repo") == "owner/repo"

    def test_ssh_no_git_suffix(self):
        assert _parse_repo_name("git@github.com:owner/repo") == "owner/repo"

    def test_whitespace_stripped(self):
        assert _parse_repo_name("  git@github.com:owner/repo.git\n") == "owner/repo"


class TestGetGitInfo:
    def test_real_repo(self, tmp_path):
        """Test with an actual git repo."""
        subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, check=True, capture_output=True,
        )
        # Create a file and commit
        (tmp_path / "test.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path, check=True, capture_output=True,
        )

        info = get_git_info(tmp_path)
        assert len(info.commit) >= 7
        assert info.dirty is False
        assert info.branch is not None

    def test_dirty_repo(self, tmp_path):
        """Test dirty detection."""
        subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, check=True, capture_output=True,
        )
        (tmp_path / "test.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path, check=True, capture_output=True,
        )

        # Make the repo dirty
        (tmp_path / "test.txt").write_text("changed")

        info = get_git_info(tmp_path)
        assert info.dirty is True

    def test_not_a_repo(self, tmp_path):
        with pytest.raises(GitNotFoundError):
            get_git_info(tmp_path)
