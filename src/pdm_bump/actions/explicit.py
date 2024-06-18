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


from traceback import format_exc as get_traceback
from typing import TYPE_CHECKING, final

from pdm_pfsc.logging import logger

from ..core.version import Version
from .base import VersionModifier, VersionPersister, action

if TYPE_CHECKING:
    from argparse import ArgumentParser


@final
@action
class SetExplicitVersionModifier(VersionModifier):
    """"""

    name: str = "to"
    description: str = "Sets a new version explicitly from CLI"

    def __init__(
        self,
        version: "Version",
        persister: "VersionPersister",
        new_version: list[str],
        **kwargs,
    ) -> None:
        super().__init__(version, persister, **kwargs)
        if len(new_version) != 1:
            raise ValueError("Only one value is supported")
        self.__new_version: str = new_version[0]

    def create_new_version(self) -> "Version":
        """"""
        try:
            new_version: "Version" = Version.from_string(self.__new_version)
            return new_version
        except ValueError as exc:
            err: str = f"'{self.__new_version}' is not a valid value."
            logger.exception(err, exc_info=True)
            logger.debug("Exception occurred: %s", get_traceback())
            raise ValueError(err) from exc

    @classmethod
    def _update_command(cls, sub_parser: "ArgumentParser") -> None:
        """

        Parameters
        ----------
        sub_parser: ArgumentParser :


        Returns
        -------

        """
        sub_parser.add_argument(
            "new_version",
            action="store",
            nargs=1,
            type=str,
            default=None,
            help="The next version to set.",
        )

        VersionModifier._update_command(sub_parser)
