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
import sys
from enum import Enum, IntEnum, auto
from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Any, Final, Iterable, Optional, Protocol, cast

from pyproject_metadata import StandardMetadata
from tomli_w import dump as dump_toml

from .logging import logger, traced_function

if sys.version_info >= (3, 10, 0):
    # suspicious mypy behavior
    from typing import TypeAlias  # type: ignore
else:
    from typing_extensions import TypeAlias

if sys.version_info >= (3, 11, 0):
    # suspicious mypy behavior
    from tomllib import load as load_toml  # type: ignore
else:
    # Python 3.11 -> mypy will not recognize this
    from tomli import load as load_toml  # type: ignore


_ConfigMapping: TypeAlias = dict[str, Any]


class _StringEnum(str, Enum):
    pass


# Justification: Minimal protocol
class ConfigHolder(Protocol):  # pylint: disable=R0903
    root: Path
    PYPROJECT_FILENAME: str

    @property
    def config(self) -> _ConfigMapping:
        # Method empty: Only a protocol stub
        pass


@traced_function
def _get_config_value(
    config: _ConfigMapping, *keys: str, default_value: Optional[Any] = None
) -> Optional[Any]:
    front: str

    key: str = ".".join(keys)
    logger.debug("Searching for '%s' in configuration", key)
    logger.debug("Configuration is set to: \n%s", config)

    while len(keys) > 1:
        front = keys[0]
        if front in config.keys():
            logger.debug("Found configuration section %s", front)
            config = cast(dict[str, Any], config[front])
            keys = tuple(keys[1:])
        else:
            logger.debug("Could not find configuration section %s.", front)
            return default_value

    front = keys[0]

    result = default_value if front not in config.keys() else config[front]
    logger.debug("Found value at '%s' is: %s", key, result)
    return result


@traced_function
def _set_config_value(config: _ConfigMapping, value: Any, *keys: str) -> None:
    front: str

    key: str = ".".join(keys)
    logger.debug("Setting '%s' to '%s'", key, value)

    while len(keys) > 1:
        front = keys[0]
        if front not in config.keys():
            logger.debug(
                "Key '%s' was not found. Adding empty configuration", front
            )
            config[front] = {}
        config = config[front]
        keys = tuple(keys[1:])

    front = keys[0]
    config[front] = value


class ConfigSections(_StringEnum):
    PDM_BUMP: Final[str] = "pdm_bump"
    PDM_BUMP_VCS: Final[str] = "vcs"


class ConfigKeys(_StringEnum):
    VERSION: Final[str] = "version"
    VERSION_SOURCE: Final[str] = "source"
    VERSION_SOURCE_FILE_PATH: Final[str] = "path"
    BUILD_BACKEND: Final[str] = "build-backend"
    VCS_PROVIDER: Final[str] = "provider"
    PROJECT_METADATA: Final[str] = "project"


class ConfigValues(_StringEnum):
    VERSION_SOURCE_FILE: Final[str] = "file"
    BUILD_BACKEND_PDM_PEP517_API: Final[str] = "pdm.pep517.api"


# Justification: Currently no more meta data to check
class ProjectMetaData:  # pylint: disable=R0903
    def __init__(self, meta_data: StandardMetadata) -> None:
        self.__meta_data = meta_data

    @property
    def is_dynamic_version(self) -> bool:
        return ConfigKeys().VERSION in self.__meta_data.dynamic


class _ConfigSection(IntEnum):
    ROOT = auto()
    METADATA = auto()
    PLUGIN_CONFIG = auto()
    BUILD_SYSTEM = auto()
    TOOL_CONFIG = auto()


class Config:
    def __init__(self, project: ConfigHolder) -> None:
        self.__project: ConfigHolder = project

    @cached_property
    @traced_function
    def pyproject_file(self) -> Path:
        return self.__project.root / self.__project.PYPROJECT_FILENAME

    @property
    @traced_function
    def meta_data(self) -> ProjectMetaData:
        data: _ConfigMapping = self._get_pyproject_config(_ConfigSection.ROOT)
        meta: StandardMetadata = StandardMetadata.from_pyproject(data)
        return ProjectMetaData(meta)

    @traced_function
    def get_pyproject_metadata(self, *keys: str) -> Optional[Any]:
        config: _ConfigMapping = self._get_pyproject_config(
            _ConfigSection.METADATA
        )
        return _get_config_value(config, *keys)

    @traced_function
    def get_pyproject_build_system(self, *keys: str) -> Optional[Any]:
        config: _ConfigMapping = self._get_pyproject_config(
            _ConfigSection.BUILD_SYSTEM
        )
        return _get_config_value(config, *keys)

    @traced_function
    def get_pyproject_tool_config(self, *keys: str) -> Optional[Any]:
        config: _ConfigMapping = self._get_pyproject_config(
            _ConfigSection.TOOL_CONFIG
        )
        return _get_config_value(config, *keys)

    @traced_function
    def get_config_value(self, *keys: str) -> Optional[Any]:
        config: dict[str, Any] = self.__project.config
        return _get_config_value(config, *keys)

    @traced_function
    def get_config_or_pyproject_value(self, *keys: str) -> Optional[Any]:
        config1: _ConfigMapping = self.__project.config
        config2: _ConfigMapping = self._get_pyproject_config(
            _ConfigSection.PLUGIN_CONFIG
        )

        return _get_config_value(config1, *keys) or _get_config_value(
            config2, *keys
        )

    @traced_function
    def set_pyproject_metadata(self, value: Any, *keys: str) -> None:
        config: _ConfigMapping = self._get_pyproject_config(
            _ConfigSection.ROOT
        )
        new_config: _ConfigMapping = _get_config_value(
            config, ConfigKeys.PROJECT_METADATA, default_value={}
        )
        _set_config_value(new_config, value, *keys)
        self._write_config(config)

    def _write_config(self, config: _ConfigMapping) -> None:
        with BytesIO() as buffer:
            dump_toml(config, buffer)

            with open(self.pyproject_file, "wb+") as file_ptr:
                file_ptr.write(buffer.getvalue())
                logger.info(
                    "Successfully saved configuration to %s",
                    self.pyproject_file,
                )

    @traced_function
    def _get_pyproject_config(self, section: _ConfigSection) -> _ConfigMapping:
        project_data: _ConfigMapping = self._read_config()
        section_key: Iterable[str] = ()
        if section in (
            _ConfigSection.TOOL_CONFIG,
            _ConfigSection.PLUGIN_CONFIG,
        ):
            section_key = ["tool", "pdm"]
            if _ConfigSection.PLUGIN_CONFIG == section:
                section_key.extend(["plugins", "bump"])
            section_key = tuple(section_key)
        elif _ConfigSection.BUILD_SYSTEM == section:
            section_key = ("build-system",)
        elif _ConfigSection.METADATA == section:
            section_key = ("project",)
        elif _ConfigSection.ROOT == section:
            return project_data or {}

        data = _get_config_value(project_data, *section_key, default_value={})

        return cast(_ConfigMapping, data)

    @traced_function
    def _read_config(self) -> dict[str, Any]:
        project_file = self.pyproject_file
        with open(project_file, "rb") as file_pointer:
            return load_toml(file_pointer)
