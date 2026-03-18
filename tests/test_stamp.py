"""Tests for the stamp function."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from gitmatplotlib._git import GitInfo
from gitmatplotlib._stamp import configure, reset_config, stamp


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")
    reset_config()


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
        assert text.get_text() == "abc1234 (dirty)"

    def test_stamp_custom_format(self):
        fig, ax = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=True, branch="main", repo="owner/repo")
        text = stamp(fig, git_info=info, fmt="{repo} {branch}@{commit}{dirty}")
        assert text.get_text() == "owner/repo main@abc1234 (dirty)"

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


class TestConfigure:
    def test_configure_sets_defaults(self):
        info = GitInfo(commit="abc1234", dirty=True, branch="main", repo="owner/repo")
        configure(fmt="{repo}@{commit}{dirty}", fontsize=8, color="blue")

        fig, ax = plt.subplots()
        text = stamp(fig, git_info=info)
        assert text.get_text() == "owner/repo@abc1234 (dirty)"
        assert text.get_fontsize() == 8
        assert text.get_color() == "blue"

    def test_explicit_overrides_configure(self):
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        configure(fmt="{repo}@{commit}", color="blue")

        fig, ax = plt.subplots()
        text = stamp(fig, git_info=info, fmt="{commit}", color="red")
        assert text.get_text() == "abc1234"
        assert text.get_color() == "red"

    def test_reset_config(self):
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        configure(fmt="{repo}@{commit}", fontsize=20)
        reset_config()

        fig, ax = plt.subplots()
        text = stamp(fig, git_info=info)
        # Should use built-in defaults after reset
        assert text.get_text() == "abc1234"
        assert text.get_fontsize() == 10

    def test_configure_invalid_key(self):
        with pytest.raises(TypeError, match="Unknown configuration keys"):
            configure(nonexistent_param="value")
