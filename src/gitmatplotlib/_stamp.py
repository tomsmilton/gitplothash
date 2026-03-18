"""Core stamp function for annotating matplotlib figures."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gitmatplotlib._git import (
    GitInfo,
    GitNotFoundError,
    auto_commit as _auto_commit,
    get_git_info,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.text import Text

logger = logging.getLogger(__name__)

_UNSET: Any = object()

_DEFAULTS: dict[str, Any] = {}

# The built-in defaults used when no configure() has been called
# and no explicit value is passed to stamp().
_BUILTIN_DEFAULTS: dict[str, Any] = {
    "fmt": "{commit}{dirty}",
    "dirty_marker": " (dirty)",
    "pos": (0.99, 0.01),
    "ha": "right",
    "va": "bottom",
    "fontsize": 10,
    "color": "gray",
    "alpha": 0.5,
    "fontfamily": "monospace",
    "repo_path": None,
    "auto_commit": False,
    "commit_message": "gitmatplotlib: auto-snapshot",
    "strict": False,
}


def configure(**kwargs: Any) -> None:
    """Set default stamp options for the rest of the session.

    Call this once at the start of a notebook and all subsequent
    ``stamp()`` calls (including via ``enable()``) will use these
    defaults. Any argument passed explicitly to ``stamp()`` still
    takes precedence.

    Parameters
    ----------
    **kwargs
        Any keyword argument accepted by :func:`stamp`.

    Examples
    --------
    >>> import gitmatplotlib
    >>> gitmatplotlib.configure(
    ...     fmt="{repo}@{commit}{dirty}",
    ...     fontsize=8,
    ...     color="blue",
    ...     auto_commit=True,
    ... )
    """
    invalid = set(kwargs) - set(_BUILTIN_DEFAULTS)
    if invalid:
        raise TypeError(
            f"Unknown configuration keys: {invalid}. "
            f"Valid keys: {set(_BUILTIN_DEFAULTS)}"
        )
    _DEFAULTS.update(kwargs)


def reset_config() -> None:
    """Reset all defaults back to built-in values."""
    _DEFAULTS.clear()


def _resolve(name: str, explicit: Any) -> Any:
    """Return the explicit value if set, else the configured default, else the built-in default."""
    if explicit is not _UNSET:
        return explicit
    return _DEFAULTS.get(name, _BUILTIN_DEFAULTS[name])


def stamp(
    target: Figure | Axes | None = None,
    *,
    fmt: Any = _UNSET,
    dirty_marker: Any = _UNSET,
    pos: Any = _UNSET,
    ha: Any = _UNSET,
    va: Any = _UNSET,
    fontsize: Any = _UNSET,
    color: Any = _UNSET,
    alpha: Any = _UNSET,
    fontfamily: Any = _UNSET,
    repo_path: Any = _UNSET,
    git_info: GitInfo | None = None,
    auto_commit: Any = _UNSET,
    commit_message: Any = _UNSET,
    strict: Any = _UNSET,
) -> Text | None:
    """Annotate a matplotlib figure with git commit info.

    All keyword arguments fall back to values set via :func:`configure`,
    then to built-in defaults.

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
        (x, y) position in figure fraction coordinates (0-1).
    ha, va : str
        Horizontal and vertical alignment.
    fontsize : int
        Font size in points.
    color : str
        Text color.
    alpha : float
        Text transparency (0-1).
    fontfamily : str
        Font family.
    repo_path : str or Path, optional
        Path to the git repository. Defaults to cwd.
    git_info : GitInfo, optional
        Pre-fetched git info. Skips subprocess calls if provided.
    auto_commit : bool
        If True, stage and commit all changes before stamping.
    commit_message : str
        Commit message used when auto_commit is True.
    strict : bool
        If True, raise on git errors. If False (default), silently skip.

    Returns
    -------
    matplotlib.text.Text or None
        The text artist added, or None if stamping was skipped.
    """
    import matplotlib.pyplot as plt

    # Resolve all parameters against configured defaults
    fmt = _resolve("fmt", fmt)
    dirty_marker = _resolve("dirty_marker", dirty_marker)
    pos = _resolve("pos", pos)
    ha = _resolve("ha", ha)
    va = _resolve("va", va)
    fontsize = _resolve("fontsize", fontsize)
    color = _resolve("color", color)
    alpha = _resolve("alpha", alpha)
    fontfamily = _resolve("fontfamily", fontfamily)
    repo_path = _resolve("repo_path", repo_path)
    auto_commit = _resolve("auto_commit", auto_commit)
    commit_message = _resolve("commit_message", commit_message)
    strict = _resolve("strict", strict)

    # Resolve the figure
    if target is None:
        fig = plt.gcf()
    elif hasattr(target, "get_figure"):
        # It's an Axes
        fig = target.get_figure()
    else:
        # Assume it's a Figure
        fig = target

    # Auto-commit if requested
    if auto_commit:
        _auto_commit(repo_path, message=commit_message)

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
