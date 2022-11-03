#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#

from typing import Protocol, cast

from .config import Config
from .version import Version, Pep440VersionFormatter


class _ProjectWriter(Protocol):
    def write_pyproject(self, show_message: bool) -> None:
        # Method empty: Only a protocol stub
        pass


class StaticPep621VersionSource:
    def __init__(self, project: _ProjectWriter, config: Config) -> None:
        self.__project = project
        self.__config = config

    @property
    def is_enabled(self) -> bool:
        return self.__config.get_pyproject_value("project", "version") is not None

    def __get_current_version(self) -> Version:
        v: str = cast(str, self.__config.get_pyproject_value("project", "version"))
        return Version.from_string(v)

    def __set_current_version(self, v: Version) -> None:
        formatter: Pep440VersionFormatter = Pep440VersionFormatter()
        version: str = formatter.format(v)
        self.__config.set_pyproject_value(version, "project", "version")

    current_version = property(__get_current_version, __set_current_version)

    def save_value(self) -> None:
        self.__project.write_pyproject(True)

