#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
from typing import Optional, Protocol, Type

from pdm.project.config import ConfigItem as _ConfigItem

from .logging import logger as _logger
from .plugin import BumpCommand as _Command


class _CoreLike(Protocol):
    def register_command(
        self, command: Type[_Command], name: Optional[str] = None
    ) -> None:
        # Method empty: Only a protocol stub
        pass

    @staticmethod
    def add_config(name: str, config_item: _ConfigItem) -> None:
        # Method empty: Only a protocol stub
        pass


def main(core: _CoreLike) -> None:
    core.register_command(_Command)
