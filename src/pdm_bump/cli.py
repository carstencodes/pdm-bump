from pdm.core import Core as _Core

from .plugin import BumpCommand as _Command
from .logging import logger


def main(core: _Core) -> None:
    core.register_command(_Command)
