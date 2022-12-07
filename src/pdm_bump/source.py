#
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#

from typing import Protocol, Union, cast, runtime_checkable

from .config import Config
from .logging import logger
from .version import Pep440VersionFormatter, Version


# Justification: Minimal protocol
class _ProjectWriter(Protocol):  # pylint: disable=R0903
    def write(self, show_message: bool) -> None:
        # Method empty: Only a protocol stub
        pass


@runtime_checkable
class _ProjectWriterClassic(Protocol):  # pylint: disable=R0903
    def write_pyproject(self, show_message: bool) -> None:
        # Method empty: Only a protocol stub
        pass


# Justification: Minimal protocol
@runtime_checkable
class _ProjectWriterHolder(Protocol):  # pylint: disable=R0903
    pyproject: _ProjectWriter


class StaticPep621VersionSource:
    def __init__(
        self,
        project: Union[_ProjectWriterHolder, _ProjectWriterClassic],
        config: Config,
    ) -> None:
        self.__project = project
        self.__config = config

    @property
    def is_enabled(self) -> bool:
        return self.__config.get_pyproject_metadata("version") is not None

    def __get_current_version(self) -> Version:
        version: str = cast(
            str, self.__config.get_pyproject_metadata("version")
        )
        return Version.from_string(version)

    def __set_current_version(self, ver: Version) -> None:
        formatter: Pep440VersionFormatter = Pep440VersionFormatter()
        version: str = formatter.format(ver)
        self.__config.set_pyproject_metadata(version, "version")

    current_version = property(__get_current_version, __set_current_version)

    def save_value(self) -> None:
        if isinstance(self.__project, _ProjectWriterHolder):
            cast(_ProjectWriterHolder, self.__project).pyproject.write(True)
        elif isinstance(self.__project, _ProjectWriterClassic):
            cast(_ProjectWriterClassic, self.__project).write_pyproject(True)
        else:
            logger.error("Failed to save new version to project file.")
