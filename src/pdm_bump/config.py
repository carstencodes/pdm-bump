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


class Config:
    def __init__(self, project: ConfigHolder) -> None:
        self.__project: ConfigHolder = project

    @traced_function
    def get_pyproject_value(self, *keys: str) -> Optional[Any]:
        config: _ConfigMapping = self._get_pyproject_config(False)
        return _get_config_value(config, *keys)

    @traced_function
    def get_config_value(self, *keys: str) -> Optional[Any]:
        config: dict[str, Any] = self.__project.config
        return _get_config_value(config, *keys)

    @traced_function
    def get_config_or_pyproject_value(self, *keys: str) -> Optional[Any]:
        config1: _ConfigMapping = self.__project.config
        config2: _ConfigMapping = self._get_pyproject_config()

        return _get_config_value(config1, *keys) or _get_config_value(
            config2, *keys
        )

    @traced_function
    def set_pyproject_value(self, value: Any, *keys: str) -> None:
        config: _ConfigMapping = self._get_pyproject_config(False)
        _set_config_value(config, value, *keys)

    @traced_function
    def _get_pyproject_config(self,
                              load_settings: bool = True) -> _ConfigMapping:
        project: _ModernPyProject = self.__project.pyproject
        if isinstance(project, PyProject):
            pyproject: PyProject = cast(PyProject, project)
            if (load_settings):
                settings: Table = pyproject.settings
                return cast(_ConfigMapping, settings.setdefault("plugins", {}))

            return cast(_ConfigMapping, project.read().value)

        if isinstance(project, dict):
            return cast(_ConfigMapping, project)

        logger.error("Failed to load project configuration.")
        return {}
