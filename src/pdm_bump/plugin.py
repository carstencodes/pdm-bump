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
from argparse import ArgumentParser, Namespace
from pathlib import Path
from traceback import format_exc as get_traceback
from typing import Final, Optional, Protocol, cast, final

# MyPy does not recognize this during pull requests
from pdm.cli.commands.base import BaseCommand  # type: ignore
from pdm.termui import UI  # type: ignore

from .action import COMMAND_NAMES as MODIFIER_ACTIONS
from .action import (
    PRERELEASE_OPTIONS,
    ActionCollection,
    VersionModifier,
    VersionModifierFactory,
    create_actions,
)
from .auto import COMMAND_NAMES as VCS_BASED_ACTIONS
from .auto import apply_vcs_based_actions
from .config import Config, ConfigHolder, ConfigKeys, ConfigSections
from .dynamic import DynamicVersionSource
from .logging import logger, traced_function, update_logger_from_project_ui
from .source import StaticPep621VersionSource
from .vcs import (
    DefaultVcsProvider,
    VcsProvider,
    VcsProviderRegistry,
    vcs_providers,
)
from .version import Pep440VersionFormatter, Version


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

    @traced_function
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "what",
            action="store",
            choices=list(MODIFIER_ACTIONS) + list(VCS_BASED_ACTIONS),
            default=None,
            help="The part of the version to bump according to PEP 440: "
            + "major.minor.micro.",
        )
        parser.add_argument(
            "--pre",
            action="store",
            choices=list(PRERELEASE_OPTIONS),
            default=None,
            help="Sets a pre-release on the current version."
            + " If a pre-release is set, it can be removed "
            + "using the final option. A new pre-release "
            + "must greater then the current version."
            + " See PEP440 for details.",
        )
        parser.add_argument(
            "--dry-run",
            "-n",
            action="store_true",
            help="Do not store incremented version",
        )
        parser.add_argument(
            "--micro",
            action="store_true",
            help="When setting pre-release, specifies "
            + "whether micro version shall "
            + "be incremented as well",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="When setting epoch, reset version to 1.0.0",
        )
        parser.add_argument(
            "--no-remove",
            action="store_false",
            help="When incrementing major, minor, micro or epoch, "
            + "do not remove all pre-release parts",
        )

    @traced_function
    def handle(self, project: _ProjectLike, options: Namespace) -> None:
        config: Config = Config(project)
        update_logger_from_project_ui(project.core.ui)

        selected_backend: Optional[_VersionSource] = self._select_backend(
            project, config
        )

        if selected_backend is None:
            pyproject_file = project.root / project.PYPROJECT_FILENAME
            logger.error("Cannot find version in %s", pyproject_file)
            return

        backend: _VersionSource = cast(_VersionSource, selected_backend)

        version: Version = backend.current_version

        next_version: Version = self._get_next_version(
            version, project, options
        )

        if next_version == version:
            logger.info(
                "Version did not change after application. "
                "No need to persist new version."
            )
            return

        if options.dry_run:
            logger.info("Would write new version %s", next_version)
            return

        self._save_new_version(backend, next_version)

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
    def _get_next_version(
        self, version: Version, project: _ProjectLike, options: Namespace
    ) -> Version:
        actions: ActionCollection = self._get_actions(
            options.micro, options.reset, options.no_remove
        )

        vcs_provider: VcsProvider = self._get_vcs_provider(project)
        apply_vcs_based_actions(actions, vcs_provider, options.dry_run)

        modifier: VersionModifier = self._get_action(
            actions, version, options.what, options.pre
        )

        try:
            return modifier.create_new_version()
        except ValueError as exc:
            logger.exception(
                "Failed to update version to next version", exc_info=False
            )
            logger.debug("Exception occurred: %s", get_traceback())
            raise SystemExit(1) from exc

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
    def _save_new_version(
        self, backend: _VersionSource, next_version: Version
    ) -> None:
        backend.current_version = next_version

    @traced_function
    def _get_action(
        self,
        actions: ActionCollection,
        version: Version,
        what: str,
        pre: Optional[str],
    ) -> VersionModifier:
        modifier_factory: VersionModifierFactory
        if pre is not None:
            modifier_factory = actions.get_action_with_option(what, pre)
        else:
            modifier_factory = actions.get_action(what)

        modifier: VersionModifier = modifier_factory(version)
        return modifier

    @traced_function
    def _get_actions(
        self, increment_micro: bool, reset_version: bool, remove_parts: bool
    ) -> ActionCollection:
        actions: ActionCollection = create_actions(
            increment_micro=increment_micro,
            reset_version=reset_version,
            remove_parts=remove_parts,
        )

        return actions

    @traced_function
    def _version_to_string(self, version: Version) -> str:
        result: str = Pep440VersionFormatter().format(version)
        return result
