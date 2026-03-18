"""Auto-stamping via IPython hooks and context managers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from gitmatplotlib._stamp import stamp

_ORIGINAL_SHOW = None
_ORIGINAL_SAVEFIG = None
_POST_EXECUTE_HOOK = None
_ENABLED = False
_STAMP_KWARGS: dict[str, Any] = {}


def _stamp_open_figures(**stamp_kwargs: Any) -> None:
    """Stamp all currently open matplotlib figures that haven't been stamped yet."""
    import matplotlib.pyplot as plt

    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        if not getattr(fig, "_gitmatplotlib_stamped", False):
            stamp(fig, **stamp_kwargs)


def _stamp_figure_if_needed(fig: Any) -> None:
    """Stamp a single figure if auto-stamping is enabled and it hasn't been stamped."""
    if _ENABLED and not getattr(fig, "_gitmatplotlib_stamped", False):
        stamp(fig, **_STAMP_KWARGS)


def enable(ip: Any = None, **stamp_kwargs: Any) -> None:
    """Register hooks that auto-stamp all figures.

    Call this once (e.g. in the first cell of a notebook) and every
    subsequent plot will be annotated with git commit info. Stamps are
    applied automatically on ``plt.show()``, ``fig.savefig()``, and
    at the end of each Jupyter cell.

    Parameters
    ----------
    ip : IPython shell instance, optional
        If None, uses ``get_ipython()``.
    **stamp_kwargs
        Keyword arguments forwarded to :func:`stamp`.
    """
    global _POST_EXECUTE_HOOK, _ORIGINAL_SHOW, _ORIGINAL_SAVEFIG
    global _ENABLED, _STAMP_KWARGS

    import matplotlib.figure
    import matplotlib.pyplot as plt

    # Clean up any previous enable() call
    disable(ip)

    _ENABLED = True
    _STAMP_KWARGS.update(stamp_kwargs)

    # 1. Patch plt.show — stamps all open figures before showing.
    _ORIGINAL_SHOW = plt.show

    def patched_show(*args: Any, **kwargs: Any) -> None:
        _stamp_open_figures(**stamp_kwargs)
        _ORIGINAL_SHOW(*args, **kwargs)

    plt.show = patched_show  # type: ignore[assignment]

    # 2. Patch Figure.savefig — stamps the figure before saving.
    #    This ensures the stamp is present even if savefig is called
    #    before show, or show is never called at all.
    _ORIGINAL_SAVEFIG = matplotlib.figure.Figure.savefig

    def patched_savefig(self: Any, *args: Any, **kwargs: Any) -> Any:
        _stamp_figure_if_needed(self)
        return _ORIGINAL_SAVEFIG(self, *args, **kwargs)

    matplotlib.figure.Figure.savefig = patched_savefig  # type: ignore[assignment]

    # 3. Register a post_execute IPython hook as a fallback for the
    #    inline backend, which renders figures without explicit show/savefig.
    if ip is None:
        try:
            from IPython import get_ipython
            ip = get_ipython()
        except ImportError:
            ip = None

    if ip is not None:
        def post_execute_hook() -> None:
            _stamp_open_figures(**stamp_kwargs)

        _POST_EXECUTE_HOOK = post_execute_hook
        ip.events.register("post_execute", post_execute_hook)

        # Move our hook to the front so it runs before the inline
        # backend closes figures.
        callbacks = ip.events.callbacks.get("post_execute", [])
        if post_execute_hook in callbacks:
            callbacks.remove(post_execute_hook)
            callbacks.insert(0, post_execute_hook)


def disable(ip: Any = None) -> None:
    """Remove all auto-stamp hooks.

    Parameters
    ----------
    ip : IPython shell instance, optional
        If None, uses ``get_ipython()``.
    """
    global _POST_EXECUTE_HOOK, _ORIGINAL_SHOW, _ORIGINAL_SAVEFIG
    global _ENABLED

    import matplotlib.figure
    import matplotlib.pyplot as plt

    _ENABLED = False
    _STAMP_KWARGS.clear()

    # Restore plt.show
    if _ORIGINAL_SHOW is not None:
        plt.show = _ORIGINAL_SHOW  # type: ignore[assignment]
        _ORIGINAL_SHOW = None

    # Restore Figure.savefig
    if _ORIGINAL_SAVEFIG is not None:
        matplotlib.figure.Figure.savefig = _ORIGINAL_SAVEFIG  # type: ignore[assignment]
        _ORIGINAL_SAVEFIG = None

    # Remove IPython hook
    if _POST_EXECUTE_HOOK is not None:
        if ip is None:
            try:
                from IPython import get_ipython
                ip = get_ipython()
            except ImportError:
                ip = None

        if ip is not None:
            try:
                ip.events.unregister("post_execute", _POST_EXECUTE_HOOK)
            except ValueError:
                pass
        _POST_EXECUTE_HOOK = None


@contextmanager
def auto_stamp(**stamp_kwargs: Any):
    """Context manager that stamps every figure on ``plt.show()``.

    Usage::

        with gitmatplotlib.auto_stamp():
            plt.plot([1, 2, 3])
            plt.show()  # figure is stamped automatically

    Parameters
    ----------
    **stamp_kwargs
        Keyword arguments forwarded to :func:`stamp`.
    """
    import matplotlib.pyplot as plt

    original_show = plt.show

    def patched_show(*args: Any, **kwargs: Any) -> None:
        _stamp_open_figures(**stamp_kwargs)
        original_show(*args, **kwargs)

    plt.show = patched_show  # type: ignore[assignment]
    try:
        yield
    finally:
        plt.show = original_show  # type: ignore[assignment]
