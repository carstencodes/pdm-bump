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
from argparse import ArgumentParser, Namespace
from pathlib import Path
from traceback import format_exc as get_traceback
from typing import Final, Optional, Protocol, cast, final

# MyPy does not recognize this during pull requests
from pdm.cli.commands.base import BaseCommand  # type: ignore
from pdm.termui import UI  # type: ignore

from .actions import actions
from .core.config import Config, ConfigHolder, ConfigKeys, ConfigSections
from .core.logging import (
    logger,
    traced_function,
    update_logger_from_project_ui,
)
from .core.version import Pep440VersionFormatter, Version
from .dynamic import DynamicVersionSource
from .source import StaticPep621VersionSource
from .vcs import (
    DefaultVcsProvider,
    VcsProvider,
    VcsProviderRegistry,
    vcs_providers,
)


# Justification: Protocol for interoperability
class _CoreLike(Protocol):  # pylint: disable=R0903
    ui: UI


class _ProjectLike(ConfigHolder, Protocol):
    root: Path
    core: _CoreLike
    PYPROJECT_FILENAME: str

    def write_pyproject(self, show_message: bool) -> None:
        # Method empty: Only a protocol stub
        pass


# Justification: Minimal protocol. Maybe false positive,
# since 2 public methods available
class _VersionSource(Protocol):  # pylint: disable=R0903
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()

    def __get_current_version(self) -> Version:
        raise NotImplementedError()

    def __set_current_version(self, version: Version) -> None:
        raise NotImplementedError()

    current_version: property = property(
        __get_current_version, __set_current_version
    )


@final
class BumpCommand(BaseCommand):
    name: Final[str] = "bump"
    description: str = "Bumps the version to a next version following PEP440."

    def __init__(self, parser) -> None:
        super().__init__(parser)
        self.__backend: Optional[_VersionSource] = None

    @traced_function
    def add_arguments(self, parser: ArgumentParser) -> None:
        actions.update_parser(parser)

    @traced_function
    def save_version(self, version: Version) -> None:
        if self.__backend is None:
            msg = ". ".join(
                (
                    "No source for a version could be determined.",
                    "Saving version failed.",
                )
            )
            logger.error(msg)
            return

        self.__backend.current_version = version

    @traced_function
    def handle(self, project: _ProjectLike, options: Namespace) -> None:
        config: Config = Config(project)
        update_logger_from_project_ui(project.core.ui)

        selected_backend: Optional[_VersionSource] = self._select_backend(
            project, config
        )

        self.__backend = selected_backend

        if selected_backend is None:
            pyproject_file = project.root / project.PYPROJECT_FILENAME
            logger.error("Cannot find version in %s", pyproject_file)
            return

        backend: _VersionSource = cast(_VersionSource, selected_backend)
        vcs_provider: VcsProvider = self._get_vcs_provider(project)

        try:
            actions.execute(
                options, backend.current_version, self, vcs_provider
            )
        except ValueError as exc:
            logger.exception("Failed to execute action", exc_info=True)
            logger.debug("Exception occurred: %s", get_traceback())
            raise SystemExit(1) from exc

    @traced_function
    def _get_vcs_provider(self, project: _ProjectLike) -> VcsProvider:
        config: Config = Config(project)
        value = config.get_config_or_pyproject_value(
            ConfigSections.PDM_BUMP,
            ConfigSections.PDM_BUMP_VCS,
            ConfigKeys.VCS_PROVIDER,
        )

        registry: VcsProviderRegistry = vcs_providers

        if value is not None:
            provider_name: str = str(value)
            factory_method = registry[provider_name]
            if factory_method is not None:
                factory = factory_method()
                return factory.force_create_provider(project.root)
        else:
            provider = registry.find_repository_root(project.root)
            if provider is not None:
                return provider

        return DefaultVcsProvider(project.root)

    @traced_function
    def _select_backend(
        self, project: _ProjectLike, config: Config
    ) -> Optional[_VersionSource]:
        static_backend: _VersionSource = StaticPep621VersionSource(
            project, config
        )
        dynamic_backend: _VersionSource = DynamicVersionSource(
            project.root, config
        )

        selected_backend: Optional[_VersionSource] = None
        for backend in (static_backend, dynamic_backend):
            if backend.is_enabled:
                selected_backend = backend
                break

        return selected_backend

    @traced_function
    def _version_to_string(self, version: Version) -> str:
        result: str = Pep440VersionFormatter().format(version)
        return result
