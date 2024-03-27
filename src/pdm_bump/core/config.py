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
import argparse
from collections.abc import Iterable, Mapping
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Any, Final, Optional

from pdm_pfsc.abstractions import ConfigHolder
from pdm_pfsc.config import (
    ConfigAccessor,
    ConfigNamespace,
    ConfigSection,
    IsMissing,
)
from pdm_pfsc.logging import traced_function


class _StringEnum(str, Enum):
    """"""

    # Justification: Zen of python: Explicit is better than implicit
    pass  # pylint: disable=W0107


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


class _ConfigSections(_StringEnum):
    """"""

    PDM_BUMP: Final[str] = "pdm_bump"
    PDM_BUMP_VCS: Final[str] = "vcs"


class _PdmBumpVcsConfig(ConfigNamespace):
    def __init__(
        self, accessor: ConfigAccessor, pdm_bump: "PdmBumpConfig"
    ) -> None:
        super().__init__(_ConfigSections.PDM_BUMP_VCS, accessor, pdm_bump)

    @property
    def provider(self) -> str:
        """"""
        return self._get_value(_ConfigKeys.VCS_PROVIDER)


class PdmBumpConfig(ConfigNamespace):
    """"""

    def __init__(self, accessor: ConfigAccessor) -> None:
        super().__init__(_ConfigSections.PDM_BUMP, accessor, None)
        self.__vcs = _PdmBumpVcsConfig(accessor, self)

    @property
    def vcs(self) -> _PdmBumpVcsConfig:
        """"""
        return self.__vcs

    @property
    def commit_msg_tpl(self) -> str:
        """"""
        return self._get_value("commit_msg_tpl")

    @property
    def perform_commit(self) -> bool:
        """"""
        return self._get_value("perform_commit") or False

    @property
    def auto_tag(self) -> bool:
        """"""
        return self._get_value("auto_tag") or False

    @property
    def tag_allow_dirty(self) -> bool:
        """"""
        return self._get_value("allow_dirty") or False

    @property
    def tag_add_prefix(self) -> bool:
        """"""
        return self._get_value("tag_add_prefix") or True

    def add_values_missing_in_cli(
        self, args: argparse.Namespace
    ) -> argparse.Namespace:
        """"""

        args = PdmBumpConfig.__update_args(args, "commit", self.perform_commit)
        args = PdmBumpConfig.__update_args(
            args, "commit_message", self.commit_msg_tpl
        )
        args = PdmBumpConfig.__update_args(args, "tag", self.auto_tag)
        args = PdmBumpConfig.__update_args(args, "dirty", self.tag_allow_dirty)
        args = PdmBumpConfig.__update_args(
            args, "prepend_letter_v", self.tag_add_prefix
        )

        return args

    @staticmethod
    def __update_args(
        ns: argparse.Namespace, key: str, value: Any
    ) -> argparse.Namespace:
        if key not in ns:
            setattr(ns, key, value)
        else:
            stored_value: Optional[Any] = getattr(ns, key)
            if stored_value is None and value is not None:
                setattr(ns, key, value)
            elif isinstance(stored_value, IsMissing):
                if value is None:
                    setattr(ns, key, stored_value.raw_value())
                else:
                    setattr(ns, key, value)

        return ns


class _PdmBackendConfig:
    """"""

    def __init__(self, accessor: ConfigAccessor) -> None:
        """"""
        self.__mapping = accessor.get_pyproject_config(
            ConfigSection.TOOL_CONFIG
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

    def __init__(self, accessor: ConfigAccessor) -> None:
        """"""
        self.__accessor = accessor
        self.__mapping = accessor.get_pyproject_config(
            ConfigSection.BUILD_SYSTEM
        )
        self.__tool_mapping = accessor.get_pyproject_config(
            ConfigSection.TOOL_CONFIG
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

    def __init__(self, accessor: ConfigAccessor) -> None:
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


class _PdmBumpConfigAccessor(ConfigAccessor):
    @property
    def plugin_config_name(self) -> Iterable[str]:
        return {"bump-plugin"}


class _EmptyConfig:
    @property
    def root(self) -> Path:
        """"""
        raise NotImplementedError()

    @root.setter
    def root(self, value: Path) -> None:
        """"""
        raise NotImplementedError()

    # Justification: Fulfill protocol
    @property
    # pylint: disable=C0103
    def PYPROJECT_FILENAME(self) -> str:  # noqa: N802 NOSONAR
        """"""
        raise NotImplementedError()

    # Justification: Fulfill protocol
    @PYPROJECT_FILENAME.setter
    # pylint: disable=C0103
    def PYPROJECT_FILENAME(self, value: str) -> None:  # noqa: N802 NOSONAR
        """"""
        raise NotImplementedError()

    @property
    def config(self) -> Mapping[str, Any]:
        """"""
        return {}


# Justification: Just a protocol implementation
class _DummyConfig:  # pylint: disable=R0903
    @property
    def pyproject_file(self) -> Path:
        """"""
        raise NotImplementedError()


class Config:
    """"""

    def __init__(self, project: ConfigHolder) -> None:
        self.__project: ConfigHolder = project
        accessor: ConfigAccessor = _PdmBumpConfigAccessor(self, project)
        self.__pdm_bump = PdmBumpConfig(accessor)
        self.__meta_data = _MetaDataConfig(accessor)

    @staticmethod
    def get_plugin_config_key_prefix() -> str:
        """"""
        config: ConfigHolder = _EmptyConfig()
        accessor: ConfigAccessor = _PdmBumpConfigAccessor(
            _DummyConfig(), config
        )
        section: ConfigSection = ConfigSection.PLUGIN_CONFIG
        paths: Iterable[str]
        paths = accessor.get_config_section_path(section)

        return ".".join(paths)

    @property
    def pdm_bump(self) -> PdmBumpConfig:
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
