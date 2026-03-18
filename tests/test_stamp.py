"""Tests for the stamp function."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from gitmatplotlib._git import GitInfo
from gitmatplotlib._stamp import stamp


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


class TestStamp:
    def test_stamp_with_git_info(self):
        fig, ax = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        text = stamp(fig, git_info=info)
        assert text is not None
        assert text.get_text() == "abc1234"

    def test_stamp_dirty(self):
        fig, ax = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=True, branch="main", repo="owner/repo")
        text = stamp(fig, git_info=info)
        assert text.get_text() == "abc1234*"

    def test_stamp_custom_format(self):
        fig, ax = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=True, branch="main", repo="owner/repo")
        text = stamp(fig, git_info=info, fmt="{repo} {branch}@{commit}{dirty}")
        assert text.get_text() == "owner/repo main@abc1234*"

    def test_stamp_axes_target(self):
        fig, ax = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        text = stamp(ax, git_info=info)
        assert text is not None
        assert text.get_text() == "abc1234"

    def test_stamp_none_uses_gcf(self):
        fig, ax = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        text = stamp(git_info=info)
        assert text is not None

    def test_stamp_sets_stamped_flag(self):
        fig, ax = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        stamp(fig, git_info=info)
        assert fig._gitmatplotlib_stamped is True

    def test_stamp_custom_style(self):
        fig, ax = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        text = stamp(
            fig,
            git_info=info,
            fontsize=10,
            color="blue",
            alpha=0.8,
            pos=(0.5, 0.5),
            ha="center",
            va="center",
        )
        assert text.get_fontsize() == 10
        assert text.get_color() == "blue"
        assert text.get_alpha() == 0.8

    def test_stamp_not_in_repo_silent(self):
        """stamp() should return None if not in a repo and strict=False."""
        fig, ax = plt.subplots()
        # Use a path that's definitely not a git repo
        text = stamp(fig, repo_path="/tmp", strict=False)
        assert text is None

    def test_stamp_not_in_repo_strict(self):
        """stamp() should raise if not in a repo and strict=True."""
        from gitmatplotlib._git import GitNotFoundError

        fig, ax = plt.subplots()
        with pytest.raises(GitNotFoundError):
            stamp(fig, repo_path="/tmp", strict=True)
