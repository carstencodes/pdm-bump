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

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from difflib import unified_diff
from functools import cached_property
from pathlib import Path
from re import M as MultilinePattern  # noqa: N811
from re import Pattern
from re import compile as compile_re
from typing import TYPE_CHECKING, Final, Iterable, Optional, cast

from pdm_pfsc.logging import logger, traced_function

from .core.version import Pep440VersionFormatter, Version
from .vcs import HunkSource

if TYPE_CHECKING:
    from re import Match

    from .core.config import Config


# Justification: Minimal protocol. Maybe false positive,
# since 2 public methods available
class VersionSource(ABC, HunkSource):  # pylint: disable=R0903
    """"""

    @property
    @abstractmethod
    def current_version(self) -> "Version":
        """"""
        raise NotImplementedError()  # pylint: disable=R0801

    @current_version.setter
    @abstractmethod
    def current_version(self, version: "Version") -> None:
        raise NotImplementedError()  # pylint: disable=R0801

    @abstractmethod
    def get_source_file_change_hunks(self) -> list[str]:
        """"""
        raise NotImplementedError()


@dataclass
class _DiffData:
    original_lines: "list[str]" = field()
    new_lines: "list[str]" = field()

    @traced_function
    def merge(self, other: "_DiffData") -> "_DiffData":
        """"""
        return _DiffData(self.original_lines, other.new_lines)


class _VersionLine:
    """"""

    def __init__(self, prefix: str) -> None:
        """"""
        self.__prefix = prefix
        self.__version_group_name = "version"

    @traced_function
    def compile_pattern(self) -> Pattern[str]:
        """"""
        return compile_re(
            self.pattern,
            MultilinePattern,
        )

    @property
    @traced_function
    def version_group_name(self) -> str:
        """"""
        return self.__version_group_name

    @version_group_name.setter
    @traced_function
    def version_group_name(self, value: str) -> None:
        """"""
        self.__version_group_name = value

    @property
    @traced_function
    def pattern(self) -> str:
        """"""
        pattern = ""
        pattern += rf"^{self.__prefix}\s*="
        pattern += rf"\s*[\"'](?P<{self.__version_group_name}>.+?)[\"']"
        pattern += r"\s*(?:#.*)?$"
        return pattern


class _DynamicVersionConfig:
    """"""

    __file: "Path"
    __pattern: "Pattern[str]"
    __file_encoding: str

    def __init__(
        self,
        file_path: "Path",
        line_config: "_VersionLine",
        encoding: str = "utf-8",
    ) -> None:
        self.__file = file_path
        self.__line_config = line_config
        self.__file_encoding = encoding
        self.__pattern = line_config.compile_pattern()

    @cached_property
    @traced_function
    def dynamic_version(self) -> "Optional[str]":
        """"""
        with self.__file.open("r", encoding=self.__file_encoding) as file_ptr:
            match = self.__pattern.search(file_ptr.read())
        if match is not None:
            return match.group(self.__line_config.version_group_name)
        return None

    @traced_function
    def replace_dynamic_version(self, new_version: str) -> "_DiffData":
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
            match = cast("Match[str]", match)
            version_start, version_end = match.span(
                self.__line_config.version_group_name
            )
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


class _VersionStorageBackend(VersionSource, ABC):
    """"""

    def __init__(self, config: "Config", repository_root: "Path") -> None:
        self.__config = config
        self.__repository_root = repository_root
        self.__current_version: "Version | None" = None
        self.__hunk: "Optional[_DiffData]" = None

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """"""
        raise NotImplementedError()  # pylint: disable=R0801

    @property
    @abstractmethod
    def source_file_path(self) -> "Path":
        """"""
        raise NotImplementedError()  # pylint: disable=R0801

    @property
    @traced_function
    def _config(self) -> "Config":
        """"""
        return self.__config

    @property
    @traced_function
    def _repository_root(self) -> "Path":
        """"""
        return self.__repository_root

    @property
    @abstractmethod
    def line_identifier(self) -> "_VersionLine":
        """"""
        raise NotImplementedError()

    @property
    @traced_function
    def current_version(self) -> "Version":
        """"""
        if self.__current_version is None:
            dynamic: "_DynamicVersionConfig" = self._get_current_version_config
            version_line_value: "Optional[str]" = dynamic.dynamic_version
            if version_line_value is None:
                raise ValueError(
                    f"Failed to find version in {self.source_file_path}. "
                    f"Make sure it matches {self.line_identifier.pattern}"
                )
            self.__current_version = Version.from_string(version_line_value)

        return self.__current_version

    @current_version.setter
    @traced_function
    def current_version(self, new_version: "Version") -> None:
        """"""
        self.__current_version = new_version
        version_str = Pep440VersionFormatter().format(new_version)
        hunk = self._get_current_version_config.replace_dynamic_version(
            version_str
        )
        if self.__hunk is None:
            self.__hunk = hunk
        else:
            self.__hunk = cast("_DiffData", self.__hunk).merge(hunk)

    @cached_property
    @traced_function
    def _get_current_version_config(self) -> "_DynamicVersionConfig":
        """"""
        config: "_DynamicVersionConfig" = _DynamicVersionConfig(
            self.source_file_path, self.line_identifier
        )
        return config

    @traced_function
    def get_source_file_change_hunks(self) -> list[str]:
        """"""
        if self.__hunk is None:
            return []

        dynamic_version_provider: "Path" = self.source_file_path
        relative_file_path: "Path" = dynamic_version_provider.relative_to(
            str(self._repository_root)
        )
        hunk: "_DiffData" = cast("_DiffData", self.__hunk)

        return list(
            unified_diff(
                hunk.original_lines,
                hunk.new_lines,
                fromfile=str(Path("a") / relative_file_path),
                tofile=str(Path("b") / relative_file_path),
                lineterm="",
            )
        )


class _Pep621StorageBackend(_VersionStorageBackend):
    """"""

    Pattern: "Final[_VersionLine]" = _VersionLine("version")

    @property
    @traced_function
    def source_file_path(self) -> "Path":
        """"""
        return self._config.pyproject_file

    @property
    @traced_function
    def is_enabled(self) -> "bool":
        """"""
        return self._config.meta_data.version is not None

    @property
    @traced_function
    def line_identifier(self) -> "_VersionLine":
        """"""
        return self.Pattern


class _DynamicStorageBackend(_VersionStorageBackend, ABC):
    """"""

    Pattern: "Final[_VersionLine]" = _VersionLine("__version__")

    @property
    @traced_function
    def is_enabled(self) -> "bool":
        """"""
        return self._config.meta_data.is_dynamic_version


class _PdmPep517StorageBackend(_DynamicStorageBackend):
    """"""

    @property
    @traced_function
    def source_file_path(self) -> "Path":
        """"""
        build_system = self._config.meta_data.build_system
        file_path = build_system.version_source_file
        if file_path is None:
            raise ValueError(
                "Invalid configuration for deprecated PDM PEP517 configuration"
            )

        logger.warning(
            "Build backend pdm-pep517 is deprecated. Consider upgrading."
        )

        return self._repository_root / file_path

    @property
    @traced_function
    def is_enabled(self) -> "bool":
        """"""
        build_system = self._config.meta_data.build_system
        return (
            super().is_enabled
            and build_system.uses_deprecated_build_backed_pdm_pep517
        )

    @property
    @traced_function
    def line_identifier(self) -> "_VersionLine":
        """"""
        return self.Pattern


class _PdmBackendStorageBackend(_DynamicStorageBackend):
    """"""

    @property
    @traced_function
    def source_file_path(self) -> "Path":
        """"""
        build_system = self._config.meta_data.build_system
        file_path = build_system.version_source_file
        if file_path is None:
            raise ValueError(
                "Invalid configuration for PDM Backend configuration"
            )

        return self._repository_root / file_path

    @property
    @traced_function
    def is_enabled(self) -> "bool":
        """"""
        build_system = self._config.meta_data.build_system
        return (
            super().is_enabled
            and build_system.uses_pdm_backend
            and not build_system.pdm_backend.use_scm
            and build_system.pdm_backend.use_file
        )

    @property
    @traced_function
    def line_identifier(self) -> "_VersionLine":
        """"""
        return self.Pattern


@traced_function
def get_all_backends(
    config: "Config", repository_root: "Path"
) -> "Iterable[_VersionStorageBackend]":
    """"""
    yield _Pep621StorageBackend(config, repository_root)
    yield _PdmPep517StorageBackend(config, repository_root)
    yield _PdmBackendStorageBackend(config, repository_root)


@traced_function
def get_backend(
    config: "Config", repository_root: "Path"
) -> "Optional[VersionSource]":
    """"""
    for backend in get_all_backends(config, repository_root):
        if backend.is_enabled:
            return backend

    return None
