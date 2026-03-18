# gitmatplotlib

Stamp your matplotlib plots with the current git commit hash so you can always trace which version of your code produced a figure. Designed for Jupyter notebook workflows where you're iterating on analysis for a paper.

Shows the short commit hash and flags uncommitted changes as `(dirty)`.

## Install

```bash
pip install git+ssh://git@github.com/tomsmilton/gitplothash.git
```

Or for local development:

```bash
git clone git@github.com:tomsmilton/gitplothash.git
cd gitplothash
pip install -e .
```

## Quick Start

```python
import matplotlib.pyplot as plt
import gitmatplotlib

plt.plot([1, 2, 3], [1, 4, 9])
gitmatplotlib.stamp()
plt.show()
```

This adds a small annotation like `a1b2c3d` (or `a1b2c3d (dirty)` if there are uncommitted changes) in the bottom-right corner of your figure.

## Auto-stamp every plot in a notebook

Call `enable()` once in your first cell and all subsequent plots are stamped automatically:

```python
import gitmatplotlib
gitmatplotlib.enable()
```

To stop auto-stamping:

```python
gitmatplotlib.disable()
```

## Auto-commit before stamping

Use `auto_commit=True` to automatically commit all changes before stamping. This ensures the commit hash always corresponds to a clean snapshot of the code that produced the plot:

```python
gitmatplotlib.stamp(auto_commit=True)

# Or with enable() for all plots
gitmatplotlib.enable(auto_commit=True)
```

## Customisation

### Include repo name and branch

```python
gitmatplotlib.stamp(fmt="{repo} {branch}@{commit}{dirty}")
# → "tomsmilton/gitplothash main@a1b2c3d"
```

Format placeholders: `{commit}`, `{dirty}`, `{branch}`, `{repo}`

### Change position and style

```python
gitmatplotlib.stamp(
    pos=(0.01, 0.99),   # top-left
    ha="left",
    va="top",
    fontsize=8,
    color="blue",
    alpha=0.3,
)
```

### Stamp a specific figure or axes

```python
fig, axes = plt.subplots(1, 2)
gitmatplotlib.stamp(fig)
gitmatplotlib.stamp(axes[0])  # uses parent figure
```

## API

| Function | Description |
|---|---|
| `stamp(target, ...)` | Add git info annotation to a figure |
| `enable(...)` | Auto-stamp all plots in a Jupyter notebook |
| `disable()` | Stop auto-stamping |
| `auto_stamp(...)` | Context manager that stamps on `plt.show()` |
| `get_git_info()` | Get a `GitInfo` object with commit, dirty, branch, repo |
| `auto_commit()` | Stage and commit all changes if the tree is dirty |
