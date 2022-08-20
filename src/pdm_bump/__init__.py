from typing import List
from importlib.metadata import version as __get_version

from .cli import main as register_plugin

main = register_plugin

__version__: str = __get_version(__package__ or __name__)

__all__: List[str] = [main.__name__]
