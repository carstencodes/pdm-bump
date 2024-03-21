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
import sys
from collections.abc import Iterable, Mapping
from enum import Enum, IntEnum, auto
from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Any, Final, Optional, Protocol, cast

from pyproject_metadata import StandardMetadata
from tomli_w import dump as dump_toml

from .logging import logger, traced_function

if sys.version_info >= (3, 11, 0):
    # suspicious mypy behavior
    from tomllib import load as load_toml  # type: ignore
else:
    # Python 3.11 -> mypy will not recognize this
    from tomli import load as load_toml  # type: ignore


class _ConfigMapping(dict[str, Any]):
    @traced_function
    def get_config_value(
        self,
        *keys: str,
        default_value: Optional[Any] = None,
        store_default: bool = False,
        readonly: bool = True,
    ) -> Optional[Any]:
        """

        Parameters
        ----------
        *keys: str :

        default_value: Optional[Any] :
             (Default value = None)

        store_default: bool:
            (Default value = False)

        readonly: bool:
            (Default value = True)

        Returns
        -------

        """
        key: str = ".".join(keys)
        logger.debug("Searching for '%s' in configuration", key)
        logger.debug("Configuration is set to: \n%s", self)

        front: str
        config: _ConfigMapping = self
        if len(keys) > 1:
            front = keys[0]
            if front in config.keys():
                logger.debug("Found configuration section %s", front)
                cfg = _ConfigMapping(cast(dict[str, Any], config[front]))
                if not readonly:
                    config[front] = cfg
                return cfg.get_config_value(
                    *tuple(keys[1:]),
                    default_value=default_value,
                    store_default=store_default,
                    readonly=readonly,
                )

            logger.debug("Could not find configuration section %s.", front)
            if not readonly and store_default:
                config[front] = default_value
            return default_value

        front = keys[0]

        is_default: bool = front not in config.keys()
        result = default_value if is_default else config[front]
        logger.debug("Found value at '%s' is: %s", key, result)

        if _ConfigMapping.__is_primitive(result):
            if not readonly and is_default and store_default:
                config[front] = result
            return result

        result = _ConfigMapping(cast(dict[str, Any], result))
        if not readonly:
            config[front] = result

        return result

    @staticmethod
    def __is_primitive(value: Any) -> bool:
        return isinstance(value, (bool, str, int, float, type(None)))

    @traced_function
    def set_config_value(self, value: Any, *keys: str) -> None:
        """

        Parameters
        ----------
        value: Any :

        *keys: str :


        Returns
        -------

        """
        front: str

        key: str = ".".join(keys)
        logger.debug("Setting '%s' to '%s'", key, value)

        config = self
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


# Justification: Minimal protocol
class ConfigHolder(Protocol):  # pylint: disable=R0903
    """"""

    root: Path
    PYPROJECT_FILENAME: str

    @property
    def config(self) -> Mapping[str, Any]:
        """"""
        # Method empty: Only a protocol stub
        raise NotImplementedError()


class _StringEnum(str, Enum):
    """"""

    # Justification: Zen of python: Explicit is better than implicit
    pass  # pylint: disable=W0107


class _ConfigSections(_StringEnum):
    """"""

    PDM_BUMP: Final[str] = "pdm_bump"
    PDM_BUMP_VCS: Final[str] = "vcs"


class _ConfigKeys(_StringEnum):
    """"""

    VERSION: Final[str] = "version"
    VERSION_SOURCE: Final[str] = "source"
    VERSION_SOURCE_FILE_PATH: Final[str] = "path"
    BUILD_BACKEND: Final[str] = "build-backend"
    VCS_PROVIDER: Final[str] = "provider"
    PROJECT_METADATA: Final[str] = "project"


VERSION_CONFIG_KEY_NAME: Final[str] = _ConfigKeys.VERSION


class _ConfigValues(_StringEnum):
    """"""

    VERSION_SOURCE_FILE: Final[str] = "file"
    VERSION_SOURCE_SCM: Final[str] = "scm"
    DEPRECATED_BUILD_BACKEND_PDM_PEP517_API: Final[str] = "pdm.pep517.api"
    BUILD_BACKEND_PDM_BACKEND: Final[str] = "pdm.backend"


class _ConfigSection(IntEnum):
    """"""

    ROOT = auto()
    METADATA = auto()
    PLUGIN_CONFIG = auto()
    BUILD_SYSTEM = auto()
    TOOL_CONFIG = auto()


# only a protocol
class _Config(Protocol):  # pylint: disable=R0903
    """"""

    @cached_property
    @traced_function
    def pyproject_file(self) -> Path:
        """"""
        raise NotImplementedError()


class _ConfigAccessor:
    def __init__(self, config: _Config, cfg_holder: ConfigHolder) -> None:
        self.__config = config
        self.__mapping = _ConfigMapping(cfg_holder.config)

    @property
    def pyproject_file(self) -> Path:
        """"""
        return self.__config.pyproject_file

    @traced_function
    def get_config_value(self, *keys: tuple[str, ...]) -> Optional[Any]:
        """

        Parameters
        ----------
        *keys: tuple[str, ...] :


        Returns
        -------

        """
        return self.__mapping.get_config_value(*keys)

    @traced_function
    def get_config_or_pyproject_value(
        self, *keys: tuple[str, ...]
    ) -> Optional[Any]:
        """

        Parameters
        ----------
        *keys: tuple[str, ...] :


        Returns
        -------

        """
        config1: _ConfigMapping = self.__mapping
        config2: _ConfigMapping = self.get_pyproject_config(
            _ConfigSection.PLUGIN_CONFIG
        )

        return config1.get_config_value(*keys) or config2.get_config_value(
            *keys
        )

    @traced_function
    def set_pyproject_metadata(self, value: Any, *keys: str) -> None:
        """

        Parameters
        ----------
        value: Any :

        *keys: tuple[str, ...] :


        Returns
        -------

        """
        config: _ConfigMapping = self.get_pyproject_config(_ConfigSection.ROOT)
        new_config: _ConfigMapping = config.get_config_value(
            _ConfigKeys.PROJECT_METADATA, default_value={}, readonly=False
        )
        new_config.set_config_value(value, *keys)
        self._write_config(config)

    def _write_config(self, config: _ConfigMapping) -> None:
        """

        Parameters
        ----------
        config: _ConfigMapping :


        Returns
        -------

        """
        with BytesIO() as buffer:
            dump_toml(config, buffer)

            with open(self.pyproject_file, "wb+") as file_ptr:
                file_ptr.write(buffer.getvalue())
                logger.info(
                    "Successfully saved configuration to %s",
                    self.pyproject_file,
                )

    @traced_function
    def get_pyproject_config(self, section: _ConfigSection) -> _ConfigMapping:
        """

        Parameters
        ----------
        section: _ConfigSection :


        Returns
        -------

        """
        project_data: _ConfigMapping = self._read_config()
        section_key: Iterable[str] = ()
        if section in (
            _ConfigSection.TOOL_CONFIG,
            _ConfigSection.PLUGIN_CONFIG,
        ):
            sk: list[str] = ["tool", "pdm"]
            if _ConfigSection.PLUGIN_CONFIG == section:
                sk.extend(["bump-plugin"])
            section_key = tuple(sk)
        elif _ConfigSection.BUILD_SYSTEM == section:
            section_key = ("build-system",)
        elif _ConfigSection.METADATA == section:
            section_key = ("project",)
        elif _ConfigSection.ROOT == section:
            return project_data or _ConfigMapping({})

        data = project_data.get_config_value(
            *section_key, default_value=_ConfigMapping({})
        )

        return cast(_ConfigMapping, data)

    @traced_function
    def _read_config(self) -> _ConfigMapping:
        """"""
        project_file = self.pyproject_file
        with open(project_file, "rb") as file_pointer:
            return _ConfigMapping(load_toml(file_pointer))

    @traced_function
    def get_pyproject_metadata(self, *keys: str) -> Optional[Any]:
        """

        Parameters
        ----------
        *keys: tuple[str, ...] :


        Returns
        -------

        """
        config: _ConfigMapping = self.get_pyproject_config(
            _ConfigSection.METADATA
        )
        return config.get_config_value(*keys)

    @traced_function
    def get_pyproject_tool_config(self, *keys: str) -> Optional[Any]:
        """

        Parameters
        ----------
        *keys: tuple[str, ...] :


        Returns
        -------

        """
        config: _ConfigMapping = self.get_pyproject_config(
            _ConfigSection.TOOL_CONFIG
        )
        return config.get_config_value(*keys)

    @cached_property
    @traced_function
    def meta_data(self) -> StandardMetadata:
        """"""
        data: _ConfigMapping = self.get_pyproject_config(_ConfigSection.ROOT)
        meta: StandardMetadata = StandardMetadata.from_pyproject(data)
        return meta


class _ConfigNamespace:
    def __init__(
        self,
        namespace: str,
        accessor: _ConfigAccessor,
        parent: "_ConfigNamespace | None" = None,
    ) -> None:
        """
        Parameters
        ----------
        namespace: str :
        parent : _ConfigNamespace | None :


        Returns
        -------

        """
        self.__parent = parent
        self.__namespace = namespace
        self.__accessor = accessor

    @property
    def parent(self) -> "_ConfigNamespace | None":
        """"""
        return self.__parent

    @property
    def namespace(self) -> tuple[str, ...]:
        """"""
        if self.__parent is None:
            return tuple(self.__namespace)
        return tuple(list(self.__parent.namespace) + [self.__namespace])

    def _get_value(self, name: str) -> Any:
        config_names: tuple[str, ...] = tuple(list(self.namespace) + [name])
        return self.__accessor.get_config_value(*config_names)


class _PdmBumpVcsConfig(_ConfigNamespace):
    def __init__(
        self, accessor: _ConfigAccessor, pdm_bump: "_PdmBumpConfig"
    ) -> None:
        super().__init__(_ConfigSections.PDM_BUMP_VCS, accessor, pdm_bump)

    @property
    def provider(self) -> str:
        """"""
        return self._get_value(_ConfigKeys.VCS_PROVIDER)


class _PdmBumpConfig(_ConfigNamespace):
    def __init__(self, accessor: _ConfigAccessor) -> None:
        super().__init__(_ConfigSections.PDM_BUMP, accessor, None)
        self.__vcs = _PdmBumpVcsConfig(accessor, self)

    @property
    def vcs(self) -> _PdmBumpVcsConfig:
        """"""
        return self.__vcs


class _PdmBackendConfig:
    """"""

    def __init__(self, accessor: _ConfigAccessor) -> None:
        """"""
        self.__mapping = accessor.get_pyproject_config(
            _ConfigSection.TOOL_CONFIG
        )

    @property
    def use_scm(self) -> bool:
        """"""
        return (
            self.__mapping.get_config_value(
                _ConfigKeys.VERSION, _ConfigKeys.VERSION_SOURCE
            )
            == _ConfigValues.VERSION_SOURCE_SCM
        )

    @property
    def use_file(self) -> bool:
        """"""
        return (
            self.__mapping.get_config_value(
                _ConfigKeys.VERSION, _ConfigKeys.VERSION_SOURCE
            )
            == _ConfigValues.VERSION_SOURCE_FILE
        )


class _BuildSystemConfig:
    """"""

    def __init__(self, accessor: _ConfigAccessor) -> None:
        """"""
        self.__accessor = accessor
        self.__mapping = accessor.get_pyproject_config(
            _ConfigSection.BUILD_SYSTEM
        )
        self.__tool_mapping = accessor.get_pyproject_config(
            _ConfigSection.TOOL_CONFIG
        )
        self.__backend = _PdmBackendConfig(accessor)

    @property
    def build_backend(self) -> str:
        """"""
        return self.__mapping.get_config_value(_ConfigKeys.BUILD_BACKEND)

    @property
    def uses_deprecated_build_backed_pdm_pep517(self) -> bool:
        """"""
        return (
            self.build_backend
            == _ConfigValues.DEPRECATED_BUILD_BACKEND_PDM_PEP517_API
            and self.__accessor.get_pyproject_tool_config(
                _ConfigKeys.VERSION, _ConfigKeys.VERSION_SOURCE
            )
            == _ConfigValues.VERSION_SOURCE_FILE
        )

    @property
    def uses_pdm_backend(self) -> bool:
        """"""
        return self.build_backend == _ConfigValues.BUILD_BACKEND_PDM_BACKEND

    @property
    def pdm_backend(self) -> _PdmBackendConfig:
        """"""
        return self.__backend

    @property
    def version_source_file(self) -> Optional[str]:
        """"""
        return self.__tool_mapping.get_config_value(
            _ConfigKeys.VERSION, _ConfigKeys.VERSION_SOURCE_FILE_PATH
        )


class _MetaDataConfig:
    """"""

    def __init__(self, accessor: _ConfigAccessor) -> None:
        """"""
        self.__accessor = accessor
        self.__build_system = _BuildSystemConfig(accessor)

    @property
    def version(self) -> Optional[str]:
        """"""
        return self.__accessor.get_pyproject_metadata(_ConfigKeys.VERSION)

    @version.setter
    def version(self, value: str) -> None:
        """"""
        self.__accessor.set_pyproject_metadata(value, _ConfigKeys.VERSION)

    @property
    def build_system(self) -> _BuildSystemConfig:
        """"""
        return self.__build_system

    @property
    def is_dynamic_version(self) -> bool:
        """"""
        return _ConfigKeys.VERSION in self.__accessor.meta_data.dynamic


class Config:
    """"""

    def __init__(self, project: ConfigHolder) -> None:
        self.__project: ConfigHolder = project
        accessor: _ConfigAccessor = _ConfigAccessor(self, project)
        self.__pdm_bump = _PdmBumpConfig(accessor)
        self.__meta_data = _MetaDataConfig(accessor)

    @property
    def pdm_bump(self) -> _PdmBumpConfig:
        """"""
        return self.__pdm_bump

    @property
    def meta_data(self) -> _MetaDataConfig:
        """"""
        return self.__meta_data

    @cached_property
    @traced_function
    def pyproject_file(self) -> Path:
        """"""
        return self.__project.root / self.__project.PYPROJECT_FILENAME
