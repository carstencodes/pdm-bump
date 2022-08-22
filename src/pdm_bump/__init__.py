from typing import List, Final
from importlib.metadata import version as __get_version
from importlib.metadata import PackageNotFoundError

from .cli import main as register_plugin

main = register_plugin

try:
    __version__: Final[str] = __get_version(__package__ or __name__)
except PackageNotFoundError:
    # Only occurs in development, since package is not installed properly
    __version__: Final[str] = "0.0.0"

__all__: List[str] = [main.__name__]
