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
from typing import Optional, Protocol

# MyPy cannot resolve this during pull request
from pdm.project.config import ConfigItem as _ConfigItem  # type: ignore

from .plugin import BumpCommand as _Command


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
        pass

    @staticmethod
    def add_config(name: str, config_item: _ConfigItem) -> None:
        """

        Parameters
        ----------
        name: str :
            
        config_item: _ConfigItem :
            

        Returns
        -------

        """
        # Method empty: Only a protocol stub
        pass


def main(core: _CoreLike) -> None:
    """

    Parameters
    ----------
    core: _CoreLike :
        

    Returns
    -------

    """
    core.register_command(_Command)
