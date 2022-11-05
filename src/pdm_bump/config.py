#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
from typing import Any, Optional, Protocol, cast

from .logging import logger, traced_function


class ConfigHolder(Protocol):
    @property
    def pyproject(self) -> dict[str, Any]:
        # Method empty: Only a protocol stub
        pass

    @property
    def config(self) -> dict[str, Any]:
        # Method empty: Only a protocol stub
        pass


@traced_function
def _get_config_value(config: dict[str, Any], *keys: str) -> Optional[Any]:
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
def _set_config_value(config: dict[str, Any], value: Any, *keys: str) -> None:
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
        config: dict[str, Any] = self.__project.pyproject
        return _get_config_value(config, *keys)

    @traced_function
    def get_config_value(self, *keys: str) -> Optional[Any]:
        config: dict[str, Any] = self.__project.config
        return _get_config_value(config, *keys)

    @traced_function
    def get_config_or_pyproject_value(self, *keys: str) -> Optional[Any]:
        config1: dict[str, Any] = self.__project.config
        config2: dict[str, Any] = self.__project.pyproject
        py_project_keys: list[str] = ["tool", "pdm", "plugins"] + list(keys)

        return _get_config_value(config1, *keys) or _get_config_value(
            config2, *tuple(py_project_keys)
        )

    @traced_function
    def set_pyproject_value(self, value: Any, *keys: str) -> None:
        config: dict[str, Any] = self.__project.pyproject
        _set_config_value(config, value, *keys)
