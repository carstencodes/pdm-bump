from typing import List

from .cli import main as register_plugin

main = register_plugin

__all__: List[str] = [ 'main' ]
