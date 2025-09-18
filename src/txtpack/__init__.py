"""txtpack - Pack/unpack multiple files into a single file."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("txtpack")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["__version__"]
