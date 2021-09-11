from .plugin import BumpCommand as _Command
from pdm.core import Core as _Core

def main(core: _Core) -> None:
    core.register_command(_Command, 'bump')