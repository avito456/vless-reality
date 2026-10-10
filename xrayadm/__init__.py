from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("xrayadm")  # single source of truth: pyproject.toml
except PackageNotFoundError:
    __version__ = "unknown"

PROG_NAME = "xrayadm"
