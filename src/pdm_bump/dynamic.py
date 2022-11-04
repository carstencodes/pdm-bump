#
# Copyright (c) 2021-2022 Carsten Igel, Chase Sterling.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, cast

from .config import Config
from .version import Pep440VersionFormatter, Version

DEFAULT_REGEX = re.compile(
    r"^__version__\s*=\s*[\"'](?P<version>.+?)[\"']\s*(?:#.*)?$", re.M
)


@dataclass
class DynamicVersionConfig:
    file: Path
    regex: re.Pattern


class DynamicVersionSource:
    def __init__(self, project_root: Path, config: Config) -> None:
        self.__project_root = project_root
        self.__config = config
        self.__current_version: Optional[Version] = None

    @property
    def is_enabled(self) -> bool:
        dynamic_items: Optional[list[str]] = cast(
            list[str], self.__config.get_pyproject_value("project", "dynamic")
        )
        return dynamic_items is not None and "version" in dynamic_items

    def __get_current_version(self) -> Version:
        if self.__current_version is not None:
            return cast(Version, self.__current_version)

        dynamic: DynamicVersionConfig = self.__get_dynamic_version()
        version: Optional[str] = __get_dynamic_version(dynamic)
        if version is not None:
            self.__current_version = Version.from_string(version)
            return self.__current_version
        raise ValueError(
            f"Failed to find version in {dynamic.file}. "
            f"Make sure it matches {dynamic.regex}"
        )

    def __set_current_version(self, version: Version) -> None:
        self.__current_version = version

    current_version = property(__get_current_version, __set_current_version)

    def save_value(self) -> None:
        if self.__current_version is None:
            raise ValueError("No current value set")
        version: Version = cast(Version, self.__current_version)
        ver: str = Pep440VersionFormatter().format(version)
        config: DynamicVersionConfig = self.__get_dynamic_version()
        __replace_dynamic_version(config, ver)

    def __get_dynamic_version(self) -> DynamicVersionConfig:
        dynamic_version: Optional[
            DynamicVersionConfig
        ] = __find_dynamic_config(self.__project_root, self.__config)
        if dynamic_version is not None:
            dynamic: DynamicVersionConfig = cast(
                DynamicVersionConfig, dynamic_version
            )
            return dynamic
        raise ValueError(
            f"Failed to extract dynamic version from {self.__project_root}."
            f" Only pdm-pep517 `file` types are supported."
        )


def __find_dynamic_config(
    root_path: Path, project_config: Config
) -> Optional[DynamicVersionConfig]:
    if (
        project_config.get_pyproject_value("build-system", "build-backend")
        == "pdm.pep517.api"
        and project_config.get_pyproject_value(
            "tool", "pdm", "version", "source"
        )
        == "file"
    ):
        file_path = project_config.get_pyproject_value(
            "tool", "pdm", "version", "path"
        )
        return DynamicVersionConfig(
            file=root_path / file_path,
            regex=DEFAULT_REGEX,
        )
    return None


def __get_dynamic_version(config: DynamicVersionConfig) -> Optional[str]:
    with config.file.open("r") as file_ptr:
        match = config.regex.search(file_ptr.read())
    if match is not None:
        return match.group("version")
    return None


def __replace_dynamic_version(
    config: DynamicVersionConfig, new_version: str
) -> None:
    with config.file.open("r") as file_ptr:
        version_file = file_ptr.read()
        match = config.regex.search(version_file)
        if match is None:
            raise ValueError("Failed to fetch version")
        match = cast(re.Match[str], match)
        version_start, version_end = match.span("version")
        new_version_file = (
            version_file[:version_start]
            + new_version
            + version_file[version_end:]
        )
    with config.file.open("w") as file_ptr:
        file_ptr.write(new_version_file)
