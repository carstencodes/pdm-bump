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
from enum import IntEnum, auto
from typing import Any, Optional, Protocol, Union, cast

from pdm.project.project_file import PyProject
from tomlkit.items import Table

from .logging import logger, traced_function

if sys.version_info >= (3, 10, 0):
    # suspicious mypy behavior
    from typing import TypeAlias  # type: ignore
else:
    from typing_extensions import TypeAlias


_ConfigMapping: TypeAlias = dict[str, Any]
_ModernPyProject: TypeAlias = Union[_ConfigMapping, PyProject]


class ConfigHolder(Protocol):
    @property
    def pyproject(self) -> _ModernPyProject:
        # Method empty: Only a protocol stub
        pass

    @property
    def config(self) -> _ConfigMapping:
        # Method empty: Only a protocol stub
        pass


@traced_function
def _get_config_value(config: _ConfigMapping, *keys: str) -> Optional[Any]:
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
            return None

    front = keys[0]

    result = None if front not in config.keys() else config[front]
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


class _ConfigSection(IntEnum):
    METADATA = auto()
    PLUGIN_CONFIG = auto()
    BUILD_SYSTEM = auto()
    TOOL_CONFIG = auto()


class Config:
    def __init__(self, project: ConfigHolder) -> None:
        self.__project: ConfigHolder = project

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
            _ConfigSection.METADATA
        )
        _set_config_value(config, value, *keys)

    @traced_function
    def _get_pyproject_config(self, section: _ConfigSection) -> _ConfigMapping:
        project: _ModernPyProject = self.__project.pyproject
        if isinstance(project, PyProject):
            pyproject: PyProject = cast(PyProject, project)
            return self._get_pyproject_file_value(pyproject, section)

        if isinstance(project, dict):
            data: _ConfigMapping = cast(_ConfigMapping, project)
            return self._get_pyproject_raw_data_value(data, section)

        logger.error("Failed to load project configuration.")
        return {}

    @traced_function
    def _get_pyproject_file_value(
        self, pyproject: PyProject, section: _ConfigSection
    ) -> _ConfigMapping:
        if section == _ConfigSection.PLUGIN_CONFIG:
            settings: Table = pyproject.settings
            return cast(_ConfigMapping, settings.setdefault("plugins", {}))
        if section == _ConfigSection.TOOL_CONFIG:
            tool_settings: Table = pyproject.settings
            return cast(_ConfigMapping, tool_settings)
        if section == _ConfigSection.BUILD_SYSTEM:
            build_system: dict = pyproject.build_system
            return cast(_ConfigMapping, build_system)
        if section == _ConfigSection.METADATA:
            metadata: Table = pyproject.metadata
            return cast(_ConfigMapping, metadata)

        logger.error("Failed to determine section to load")
        return {}

    @traced_function
    def _get_pyproject_raw_data_value(
        self, data: _ConfigMapping, section: _ConfigSection
    ) -> _ConfigMapping:
        if section == _ConfigSection.PLUGIN_CONFIG:
            for element in ["tools", "pdm", "plugins"]:
                data = data[element] if element in data.keys() else {}
            return cast(_ConfigMapping, data)
        if section == _ConfigSection.TOOL_CONFIG:
            for element in ["tools", "pdm"]:
                data = data[element] if element in data.keys() else {}
            return cast(_ConfigMapping, data)
        if section == _ConfigSection.BUILD_SYSTEM:
            return cast(
                _ConfigMapping,
                data["build-system"] if "build-system" in data.keys() else {},
            )
        if section == _ConfigSection.METADATA:
            return cast(
                _ConfigMapping,
                data["project"] if "project" in data.keys() else {},
            )

        logger.error("Failed to determine section to load")
        return {}
