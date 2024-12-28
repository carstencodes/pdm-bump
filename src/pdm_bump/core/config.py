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
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any, Final, Optional, Protocol

from pdm_pfsc.config import (
    ConfigAccessor,
    ConfigItems,
    ConfigSection,
    IsMissing,
)
from pdm_pfsc.logging import traced_function

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterable, Mapping
    from pathlib import Path
    from types import SimpleNamespace

    from pdm.project.config import ConfigItem
    from pdm_pfsc.abstractions import ConfigHolder
    from pdm_pfsc.config import Config as SupportsConfigFile


class _SupportsAddConfigItems(Protocol):  # pylint: disable=R0903
    """"""

    def add_config(self, name: str, value: "ConfigItem") -> None:
        """"""
        raise NotImplementedError()


class _StringEnum(str, Enum):
    """"""

    # Justification: Zen of python: Explicit is better than implicit
    pass  # pylint: disable=W0107


class _ConfigKeys(_StringEnum):
    """"""

    VERSION = "version"
    VERSION_SOURCE = "source"
    VERSION_SOURCE_FILE_PATH = "path"
    BUILD_BACKEND = "build-backend"
    VCS_PROVIDER = "provider"
    PROJECT_METADATA = "project"


VERSION_CONFIG_KEY_NAME: "Final[str]" = _ConfigKeys.VERSION

COMMIT_MESSAGE_TEMPLATE_DEFAULT: "Final[str]" = (
    "chore: Bump version {from} to {to}\n\n"
    "Created a commit with a new version {to}.\n"
    "Previous version was {from}."
)
PERFORM_COMMIT_DEFAULT: "Final[bool]" = False
AUTO_TAG_DEFAULT: "Final[bool]" = False
TAG_ADD_PREFIX_DEFAULT: "Final[bool]" = True
ALLOW_DIRTY_DEFAULT: "Final[bool]" = False
VCS_PROVIDER_DEFAULT: "Final[str]" = "git-cli"


class _ConfigValues(_StringEnum):
    """"""

    VERSION_SOURCE_FILE = "file"
    VERSION_SOURCE_SCM = "scm"
    DEPRECATED_BUILD_BACKEND_PDM_PEP517_API = "pdm.pep517.api"
    BUILD_BACKEND_PDM_BACKEND = "pdm.backend"


class PdmBumpConfig:
    """"""

    def __init__(self, accessor: "_PdmBumpConfigAccessor") -> None:
        namespace = accessor.values
        self.__vcs_provider: str = namespace.vcs_provider
        self.__commit_msg_tpl: str = namespace.commit_msg_tpl
        self.__perform_commit: bool = namespace.perform_commit
        self.__auto_tag: bool = namespace.auto_tag
        self.__tag_add_prefix: bool = namespace.tag_add_prefix
        self.__allow_dirty: bool = namespace.allow_dirty

    @property
    def vcs_provider(self) -> "str":
        """"""
        return self.__vcs_provider

    @property
    def commit_msg_tpl(self) -> str:
        """"""
        return self.__commit_msg_tpl

    @property
    def perform_commit(self) -> bool:
        """"""
        return self.__perform_commit

    @property
    def auto_tag(self) -> bool:
        """"""
        return self.__auto_tag

    @property
    def tag_allow_dirty(self) -> bool:
        """"""
        return self.__allow_dirty

    @property
    def tag_add_prefix(self) -> bool:
        """"""
        return self.__tag_add_prefix

    def add_values_missing_in_cli(
        self, args: "argparse.Namespace"
    ) -> "argparse.Namespace":
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
        ns: "argparse.Namespace", key: str, value: Any
    ) -> "argparse.Namespace":
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

    def __init__(self, accessor: "ConfigAccessor") -> None:
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

    def __init__(self, accessor: "ConfigAccessor") -> None:
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
    def pdm_backend(self) -> "_PdmBackendConfig":
        """"""
        return self.__backend

    @property
    def version_source_file(self) -> "Optional[str]":
        """"""
        return self.__tool_mapping.get_config_value(
            _ConfigKeys.VERSION, _ConfigKeys.VERSION_SOURCE_FILE_PATH
        )


class _MetaDataConfig:
    """"""

    def __init__(self, accessor: "ConfigAccessor") -> None:
        """"""
        self.__accessor = accessor
        self.__build_system = _BuildSystemConfig(accessor)

    @property
    def version(self) -> "Optional[str]":
        """"""
        return self.__accessor.get_pyproject_metadata(_ConfigKeys.VERSION)

    @property
    def build_system(self) -> "_BuildSystemConfig":
        """"""
        return self.__build_system

    @property
    def is_dynamic_version(self) -> bool:
        """"""
        return _ConfigKeys.VERSION in self.__accessor.meta_data.dynamic


class _PdmBumpConfigAccessor(ConfigAccessor):
    def __init__(
        self,
        config: "SupportsConfigFile",
        cfg_holder: "ConfigHolder",
    ) -> None:
        super().__init__(config, cfg_holder)
        self.__items = ConfigItems(self)
        self.__items.add_config_value(
            "commit_msg_tpl",
            description=(
                "The default commit message. "
                "Uses templates 'from' and 'to'."
            ),
            default=COMMIT_MESSAGE_TEMPLATE_DEFAULT,
        )
        self.__items.add_config_value(
            "perform_commit",
            description=(
                "If set to true, commit the " "bumped changes automatically"
            ),
            default=PERFORM_COMMIT_DEFAULT,
        )
        self.__items.add_config_value(
            "auto_tag",
            description=(
                "Create a tag after bumping " "and committing the changes"
            ),
            default=AUTO_TAG_DEFAULT,
        )
        self.__items.add_config_value(
            "tag_add_prefix",
            description="Adds the prefix v to the version tag",
            default=TAG_ADD_PREFIX_DEFAULT,
        )
        self.__items.add_config_value(
            "allow_dirty",
            description="Allows tagging the project, if it is dirty",
            default=ALLOW_DIRTY_DEFAULT,
        )
        self.__items.add_config_value(
            "vcs_provider",
            description="Configures the VCS Provider to use.",
            default=VCS_PROVIDER_DEFAULT,
            use_env_var=True,
        )

    @property
    def plugin_config_name(self) -> "Iterable[str]":
        return {"bump"}

    @property
    def values(self) -> "SimpleNamespace":
        """"""
        return self.__items.to_namespace()

    def propagate(self, target: "_SupportsAddConfigItems") -> None:
        """"""
        self.__items.propagate(target)


class _EmptyConfig:
    @property
    def root(self) -> "Path":
        """"""
        raise NotImplementedError()

    @root.setter
    def root(self, value: "Path") -> None:
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
    def config(self) -> "Mapping[str, Any]":
        """"""
        return {}


# Justification: Just a protocol implementation
class _DummyConfig:  # pylint: disable=R0903
    @property
    def pyproject_file(self) -> "Path":
        """"""
        raise NotImplementedError()


class Config:
    """"""

    def __init__(self, project: "ConfigHolder") -> None:
        self.__project: "ConfigHolder" = project
        accessor: "_PdmBumpConfigAccessor" = _PdmBumpConfigAccessor(
            self, project
        )
        self.__pdm_bump = PdmBumpConfig(accessor)
        self.__meta_data = _MetaDataConfig(accessor)

    @staticmethod
    def get_config() -> "_PdmBumpConfigAccessor":
        """"""
        config: "ConfigHolder" = _EmptyConfig()
        accessor: "_PdmBumpConfigAccessor" = _PdmBumpConfigAccessor(
            _DummyConfig(), config
        )

        return accessor

    @property
    def pdm_bump(self) -> "PdmBumpConfig":
        """"""
        return self.__pdm_bump

    @property
    def meta_data(self) -> "_MetaDataConfig":
        """"""
        return self.__meta_data

    @cached_property
    @traced_function
    def pyproject_file(self) -> "Path":
        """"""
        return self.__project.root / self.__project.PYPROJECT_FILENAME
