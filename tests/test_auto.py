"""Tests for auto-stamping."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from gitmatplotlib._auto import auto_stamp, _stamp_open_figures
from gitmatplotlib._git import GitInfo


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


class TestStampOpenFigures:
    def test_stamps_unstamped_figures(self):
        fig1, _ = plt.subplots()
        fig2, _ = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        _stamp_open_figures(git_info=info)
        assert getattr(fig1, "_gitmatplotlib_stamped", False) is True
        assert getattr(fig2, "_gitmatplotlib_stamped", False) is True

    def test_skips_already_stamped(self):
        fig, _ = plt.subplots()
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        _stamp_open_figures(git_info=info)
        # Get the text elements count
        texts_before = len(fig.texts)
        # Stamp again — should not add another annotation
        _stamp_open_figures(git_info=info)
        assert len(fig.texts) == texts_before


class TestAutoStampContext:
    def test_context_manager(self):
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        with auto_stamp(git_info=info):
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])
            plt.show()
        assert getattr(fig, "_gitmatplotlib_stamped", False) is True

    def test_context_manager_restores_show(self):
        original_show = plt.show
        info = GitInfo(commit="abc1234", dirty=False, branch="main", repo="owner/repo")
        with auto_stamp(git_info=info):
            pass
        assert plt.show is original_show
