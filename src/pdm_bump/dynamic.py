#
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2021-2023 Carsten Igel, Chase Sterling.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
""""""


from dataclasses import dataclass, field
from difflib import unified_diff
from functools import cached_property
from pathlib import Path
from re import M as MultilinePattern  # noqa: N811
from re import Match, Pattern
from re import compile as compile_re
from typing import Final, Optional, cast

from .core.config import Config, ConfigKeys, ConfigValues
from .core.logging import logger
from .core.version import Pep440VersionFormatter, Version

DEFAULT_REGEX: Final[Pattern[str]] = compile_re(
    r"^__version__\s*=\s*[\"'](?P<version>.+?)[\"']\s*(?:#.*)?$",
    MultilinePattern,
)


@dataclass
class _DiffData:
    original_lines: list[str] = field()
    new_lines: list[str] = field()

    def merge(self, other: "_DiffData") -> "_DiffData":
        """"""
        return _DiffData(self.original_lines, other.new_lines)


class DynamicVersionConfig:
    """"""

    __file: Path
    __pattern: Pattern[str]
    __file_encoding: str

    def __init__(
        self,
        file_path: Path,
        pattern: Pattern[str],
        encoding: str = "utf-8",
    ) -> None:
        self.__file = file_path
        self.__pattern = pattern
        self.__file_encoding = encoding

    @property
    def file(self) -> Path:
        """"""
        return self.__file

    @property
    def pattern(self) -> Pattern[str]:
        """"""
        return self.__pattern

    @cached_property
    def dynamic_version(self) -> Optional[str]:
        """"""
        with self.__file.open("r", encoding=self.__file_encoding) as file_ptr:
            match = self.__pattern.search(file_ptr.read())
        if match is not None:
            return match.group(ConfigKeys.VERSION)
        return None

    def replace_dynamic_version(self, new_version: str) -> _DiffData:
        """

        Parameters
        ----------
        new_version: str :


        Returns
        -------

        """
        with self.__file.open("r", encoding=self.__file_encoding) as file_ptr:
            version_file = file_ptr.read()
            match = self.__pattern.search(version_file)
            if match is None:
                raise ValueError("Failed to fetch version")
            match = cast(Match[str], match)
            version_start, version_end = match.span(ConfigKeys.VERSION)
            new_version_file = (
                version_file[:version_start]
                + new_version
                + version_file[version_end:]
            )
        with self.__file.open("w", encoding=self.__file_encoding) as file_ptr:
            file_ptr.write(new_version_file)

        return _DiffData(
            version_file.splitlines(),
            new_version_file.splitlines(),
        )

    @staticmethod
    def find_dynamic_config(
        root_path: Path, project_config: Config
    ) -> Optional["DynamicVersionConfig"]:
        """

        Parameters
        ----------
        root_path: Path :

        project_config: Config :


        Returns
        -------

        """
        if (
            project_config.get_pyproject_build_system(ConfigKeys.BUILD_BACKEND)
            == ConfigValues.DEPREACTED_BUILD_BACKEND_PDM_PEP517_API
            and project_config.get_pyproject_tool_config(
                ConfigKeys.VERSION, ConfigKeys.VERSION_SOURCE
            )
            == ConfigValues.VERSION_SOURCE_FILE
        ):
            logger.warning(
                "Build backend pdm-pep517 is deprecated. Consider upgrading."
            )
            file_path = project_config.get_pyproject_tool_config(
                ConfigKeys.VERSION, ConfigKeys.VERSION_SOURCE_FILE_PATH
            )
            return DynamicVersionConfig(
                file_path=root_path / file_path,
                pattern=DEFAULT_REGEX,
            )
        if (
            project_config.get_pyproject_build_system(ConfigKeys.BUILD_BACKEND)
            == ConfigValues.BUILD_BACKEND_PDM_BACKEND
        ):
            if (
                project_config.get_pyproject_tool_config(
                    ConfigKeys.VERSION, ConfigKeys.VERSION_SOURCE
                )
                == ConfigValues.VERSION_SOURCE_SCM
            ):
                logger.error(
                    "PDM bump cannot be used if version is fetched from scm"
                )
            if (
                project_config.get_pyproject_tool_config(
                    ConfigKeys.VERSION, ConfigKeys.VERSION_SOURCE
                )
                == ConfigValues.VERSION_SOURCE_FILE
            ):
                file_path = project_config.get_pyproject_tool_config(
                    ConfigKeys.VERSION, ConfigKeys.VERSION_SOURCE_FILE_PATH
                )
                return DynamicVersionConfig(
                    file_path=root_path / file_path,
                    pattern=DEFAULT_REGEX,
                )
        return None


# Justification: Implementation of minimal protocol
class DynamicVersionSource:  # pylint: disable=R0903
    """"""

    def __init__(self, project_root: Path, config: Config) -> None:
        self.__project_root = project_root
        self.__config = config
        self.__current_version: Optional[Version] = None
        self.__hunk: Optional[_DiffData] = None

    @property
    def is_enabled(self) -> bool:
        """"""
        return self.__config.meta_data.is_dynamic_version

    @property
    def source_file(self) -> Path:
        """"""
        return self.__get_dynamic_version().file

    def __get_current_version(self) -> Version:
        if self.__current_version is not None:
            return cast(Version, self.__current_version)

        dynamic: DynamicVersionConfig = self.__get_dynamic_version()
        version: Optional[str] = dynamic.dynamic_version
        if version is not None:
            self.__current_version = Version.from_string(version)
            return self.__current_version
        raise ValueError(
            f"Failed to find version in {dynamic.file}. "
            f"Make sure it matches {dynamic.pattern}"
        )

    def __set_current_version(self, version: Version) -> None:
        self.__current_version = version
        ver: str = Pep440VersionFormatter().format(version)
        config: DynamicVersionConfig = self.__get_dynamic_version()
        hunk = config.replace_dynamic_version(ver)
        if self.__hunk is not None:
            self.__hunk = hunk
        else:
            self.__hunk = cast(_DiffData, self.__hunk).merge(hunk)

    current_version = property(__get_current_version, __set_current_version)

    def __get_dynamic_version(self) -> DynamicVersionConfig:
        dynamic_version: Optional[
            DynamicVersionConfig
        ] = DynamicVersionConfig.find_dynamic_config(
            self.__project_root, self.__config
        )
        if dynamic_version is not None:
            dynamic: DynamicVersionConfig = cast(
                DynamicVersionConfig, dynamic_version
            )
            return dynamic
        raise ValueError(
            f"Failed to extract dynamic version from {self.__project_root}."
            f" Only pdm-pep517 `file` types are supported."
        )

    def get_source_file_change_hunks(self, repository_root: Path) -> list[str]:
        """"""
        dynamic_version_provider: Path = self.source_file
        relative_file_path: Path = dynamic_version_provider.relative_to(
            str(repository_root)
        )

        if self.__hunk is None:
            return []

        hunk: _DiffData = cast(_DiffData, self.__hunk)

        return list(
            unified_diff(
                hunk.original_lines,
                hunk.new_lines,
                fromfile=str(Path("a") / relative_file_path),
                tofile=str(Path("b") / relative_file_path),
                lineterm="",
            )
        )
