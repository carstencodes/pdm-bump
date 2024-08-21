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


from traceback import format_exc as get_traceback
from typing import TYPE_CHECKING, Final, Optional, Protocol, cast, final

# MyPy does not recognize this during pull requests
from pdm.cli.commands.base import BaseCommand  # type: ignore
from pdm_pfsc.config import ConfigHolder
from pdm_pfsc.logging import (
    logger,
    setup_logger,
    traced_function,
    update_logger_from_project_ui,
)

from .actions import ExecutionContext, actions
from .core.config import Config
from .core.version import Pep440VersionFormatter, Version
from .storage import VersionSource, get_backend
from .vcs import (
    DefaultVcsProvider,
    VcsProvider,
    VcsProviderRegistry,
    vcs_providers,
)

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from pathlib import Path

    from pdm.termui import UI  # type: ignore


# Justification: Protocol for interoperability
class _CoreLike(Protocol):  # pylint: disable=R0903
    """"""

    ui: "UI"


class _ProjectLike(ConfigHolder, Protocol):
    """"""

    root: "Path"
    core: _CoreLike
    PYPROJECT_FILENAME: str

    def write_pyproject(self, show_message: bool) -> None:
        """

        Parameters
        ----------
        show_message: bool :


        Returns
        -------

        """
        # Method empty: Only a protocol stub
        raise NotImplementedError()


@final
class BumpCommand(BaseCommand):
    """"""

    # Justification: Fulfill a protocol
    name: "Final[str]" = "bump"  # pylint: disable=C0103
    description: str = "Bumps the version to a next version following PEP440."

    def __init__(self) -> None:
        super().__init__()
        self.__backend: "Optional[VersionSource]" = None

    @traced_function
    def add_arguments(self, parser: "ArgumentParser") -> None:
        """

        Parameters
        ----------
        parser: ArgumentParser :


        Returns
        -------

        """
        actions.update_parser(parser)

    @traced_function
    def save_version(self, version: "Version") -> None:
        """

        Parameters
        ----------
        version: Version :


        Returns
        -------

        """
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
    def handle(self, project: "_ProjectLike", options: "Namespace") -> None:
        """

        Parameters
        ----------
        project: _ProjectLike :

        options: Namespace :


        Returns
        -------

        """
        # This will not handling tracing or related parts
        # Should be evaluated at start-up time
        if hasattr(options, "verbose"):
            setup_logger(options.verbose)

        config: "Config" = Config(project)
        update_logger_from_project_ui(project.core.ui)

        selected_backend: "Optional[VersionSource]" = get_backend(
            config, project.root
        )

        self.__backend = selected_backend

        if selected_backend is None:
            pyproject_file = project.root / project.PYPROJECT_FILENAME
            logger.error("Cannot find version in %s", pyproject_file)
            return

        backend: "VersionSource" = cast("VersionSource", selected_backend)
        vcs_provider: "VcsProvider" = self._get_vcs_provider(project)

        try:
            actions.execute(
                options,
                ExecutionContext(
                    version=backend.current_version,
                    persister=self,
                    vcs_provider=vcs_provider,
                    hunk_source=backend,
                    config=config.pdm_bump,
                ),
            )
        except ValueError as exc:
            logger.exception("Failed to execute action", exc_info=True)
            logger.debug("Exception occurred: %s", get_traceback())
            raise SystemExit(1) from exc

    @traced_function
    def _get_vcs_provider(self, project: "_ProjectLike") -> VcsProvider:
        """

        Parameters
        ----------
        project: _ProjectLike :


        Returns
        -------

        """
        config: "Config" = Config(project)
        value = config.pdm_bump.vcs_provider

        registry: "VcsProviderRegistry" = vcs_providers

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
    def _version_to_string(self, version: "Version") -> str:
        """

        Parameters
        ----------
        version: Version :


        Returns
        -------

        """
        result: str = Pep440VersionFormatter().format(version)
        return result
