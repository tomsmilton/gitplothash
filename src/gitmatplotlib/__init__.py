"""gitmatplotlib - Annotate matplotlib plots with git commit info."""

from gitmatplotlib._auto import auto_stamp, disable, enable
from gitmatplotlib._git import GitInfo, GitNotFoundError, get_git_info
from gitmatplotlib._stamp import stamp

__all__ = [
    "auto_stamp",
    "disable",
    "enable",
    "get_git_info",
    "GitInfo",
    "GitNotFoundError",
    "stamp",
]
