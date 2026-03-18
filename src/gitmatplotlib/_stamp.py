"""Core stamp function for annotating matplotlib figures."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from gitmatplotlib._git import GitInfo, GitNotFoundError, get_git_info

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.text import Text

logger = logging.getLogger(__name__)


def stamp(
    target: Figure | Axes | None = None,
    *,
    fmt: str = "{commit}{dirty}",
    dirty_marker: str = "*",
    pos: tuple[float, float] = (0.99, 0.01),
    ha: str = "right",
    va: str = "bottom",
    fontsize: int = 6,
    color: str = "gray",
    alpha: float = 0.5,
    fontfamily: str = "monospace",
    repo_path: str | Path | None = None,
    git_info: GitInfo | None = None,
    strict: bool = False,
) -> Text | None:
    """Annotate a matplotlib figure with git commit info.

    Parameters
    ----------
    target : Figure, Axes, or None
        The figure to annotate. If Axes, uses its parent figure.
        If None, uses ``plt.gcf()``.
    fmt : str
        Format string. Placeholders: {commit}, {dirty}, {branch}, {repo}.
    dirty_marker : str
        String inserted for {dirty} when the working tree is dirty.
    pos : tuple of float
        (x, y) position in figure fraction coordinates (0–1).
    ha, va : str
        Horizontal and vertical alignment.
    fontsize : int
        Font size in points.
    color : str
        Text color.
    alpha : float
        Text transparency (0–1).
    fontfamily : str
        Font family.
    repo_path : str or Path, optional
        Path to the git repository. Defaults to cwd.
    git_info : GitInfo, optional
        Pre-fetched git info. Skips subprocess calls if provided.
    strict : bool
        If True, raise on git errors. If False (default), silently skip.

    Returns
    -------
    matplotlib.text.Text or None
        The text artist added, or None if stamping was skipped.
    """
    import matplotlib.pyplot as plt

    # Resolve the figure
    if target is None:
        fig = plt.gcf()
    elif hasattr(target, "get_figure"):
        # It's an Axes
        fig = target.get_figure()
    else:
        # Assume it's a Figure
        fig = target

    # Get git info
    if git_info is None:
        try:
            git_info = get_git_info(repo_path)
        except GitNotFoundError:
            if strict:
                raise
            logger.debug("gitmatplotlib: not in a git repo, skipping stamp")
            return None

    label = git_info.label(fmt=fmt, dirty_marker=dirty_marker)

    text_artist = fig.text(
        pos[0],
        pos[1],
        label,
        ha=ha,
        va=va,
        fontsize=fontsize,
        color=color,
        alpha=alpha,
        fontfamily=fontfamily,
        transform=fig.transFigure,
    )
    fig._gitmatplotlib_stamped = True
    return text_artist
