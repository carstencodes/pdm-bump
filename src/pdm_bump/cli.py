#
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2021-2023 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
""""""

from typing import TYPE_CHECKING, Optional, Protocol

from .core.config import Config
from .plugin import BumpCommand as _Command

if TYPE_CHECKING:
    from pdm.project.config import ConfigItem as _ConfigItem


class _CoreLike(Protocol):
    """"""

    def register_command(
        self, command: type[_Command], name: Optional[str] = None
    ) -> None:
        """

        Parameters
        ----------
        command: type[_Command] :

        name: Optional[str] :
             (Default value = None)

        Returns
        -------

        """
        # Method empty: Only a protocol stub
        raise NotImplementedError()

    @staticmethod
    def add_config(name: str, config_item: "_ConfigItem") -> None:
        """

        Parameters
        ----------
        name: str :

        config_item: _ConfigItem :


        Returns
        -------

        """
        # Method empty: Only a protocol stub
        raise NotImplementedError()


def main(core: _CoreLike) -> None:
    """

    Parameters
    ----------
    core: _CoreLike :


    Returns
    -------

    """
    core.register_command(_Command)

    config_map = Config.get_config()

    config_map.propagate(core)
