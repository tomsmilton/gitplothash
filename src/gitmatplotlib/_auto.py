"""Auto-stamping via IPython hooks and context managers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from gitmatplotlib._stamp import stamp


def _stamp_open_figures(**stamp_kwargs: Any) -> None:
    """Stamp all currently open matplotlib figures that haven't been stamped yet."""
    import matplotlib.pyplot as plt

    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        if not getattr(fig, "_gitmatplotlib_stamped", False):
            stamp(fig, **stamp_kwargs)


_POST_EXECUTE_HOOK = None


def enable(ip: Any = None, **stamp_kwargs: Any) -> None:
    """Register an IPython hook that auto-stamps all figures after each cell.

    Call this once (e.g. in the first cell of a notebook) and every
    subsequent plot will be annotated with git commit info.

    Parameters
    ----------
    ip : IPython shell instance, optional
        If None, uses ``get_ipython()``.
    **stamp_kwargs
        Keyword arguments forwarded to :func:`stamp`.
    """
    global _POST_EXECUTE_HOOK

    if ip is None:
        from IPython import get_ipython

        ip = get_ipython()
    if ip is None:
        raise RuntimeError("Not in an IPython/Jupyter environment")

    # Remove existing hook if any
    if _POST_EXECUTE_HOOK is not None:
        try:
            ip.events.unregister("post_execute", _POST_EXECUTE_HOOK)
        except ValueError:
            pass

    def post_execute_hook() -> None:
        _stamp_open_figures(**stamp_kwargs)

    _POST_EXECUTE_HOOK = post_execute_hook

    # Register our hook, then move it to the front of the callback list
    # so it runs BEFORE the matplotlib inline backend closes the figures.
    ip.events.register("post_execute", post_execute_hook)
    callbacks = ip.events.callbacks.get("post_execute", [])
    if post_execute_hook in callbacks:
        callbacks.remove(post_execute_hook)
        callbacks.insert(0, post_execute_hook)


def disable(ip: Any = None) -> None:
    """Remove the auto-stamp IPython hook.

    Parameters
    ----------
    ip : IPython shell instance, optional
        If None, uses ``get_ipython()``.
    """
    global _POST_EXECUTE_HOOK

    if _POST_EXECUTE_HOOK is None:
        return

    if ip is None:
        from IPython import get_ipython

        ip = get_ipython()
    if ip is None:
        return

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
