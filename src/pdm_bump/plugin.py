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
from logging import DEBUG, INFO
from pathlib import Path
from traceback import format_exc as get_traceback
from typing import Final, Optional, Protocol, cast, final

from pdm.cli.commands.base import BaseCommand

from .action import (
    COMMAND_NAMES,
    PRERELEASE_OPTIONS,
    ActionCollection,
    VersionModifier,
    VersionModifierFactory,
    create_actions,
)
from .config import Config, ConfigHolder
from .dynamic import (
    find_dynamic_config,
    get_dynamic_version,
    replace_dynamic_version,
)
from .logging import TRACE, logger, traced_function
from .version import Pep440VersionFormatter, Version


class _ProjectLike(ConfigHolder, Protocol):
    root: Path

    @property
    def pyproject_file(self) -> str:
        # Method empty: Only a protocol stub
        pass

    def write_pyproject(self, show_message: bool) -> None:
        # Method empty: Only a protocol stub
        pass


@final
class BumpCommand(BaseCommand):
    name: Final[str] = "bump"
    description: Final[
        str
    ] = "Bumps the version to a next version according to PEP440."

    @traced_function
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "what",
            action="store",
            choices=list(COMMAND_NAMES),
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
            "--remove",
            action="store_true",
            help="When incrementing major, minor, micro or epoch, "
            + "remove all pre-release parts",
        )
        parser.add_argument(
            "--trace", action="store_true", help="Enable trace output"
        )
        parser.add_argument(
            "--debug", action="store_true", help="Enable debug output"
        )

    @traced_function
    def handle(self, project: _ProjectLike, options: Namespace) -> None:
        config: Config = Config(project)
        self._setup_logger(options.trace, options.debug)

        version_value: Optional[str] = cast(
            Optional[str], config.get_pyproject_value("project", "version")
        )

        dynamic_version_config = None
        if version_value is None and "version" in config.get_pyproject_value(
            "project", "dynamic"
        ):
            dynamic_version_config = find_dynamic_config(project.root, config)
            if dynamic_version_config:
                version_value = get_dynamic_version(dynamic_version_config)

        if version_value is None:
            logger.error("Cannot find version in %s", project.pyproject_file)
            return

        version: Version = Version.from_string(version_value)

        actions: ActionCollection = self._get_actions(
            options.micro, options.reset, options.remove
        )

        modifier: VersionModifier = self._get_action(
            actions, version, options.what, options.pre
        )

        result: Version
        try:
            result = modifier.create_new_version()
        except ValueError as exc:
            logger.exception(
                "Failed to update version to next version", exc_info=False
            )
            logger.debug("Exception occurred: %s", get_traceback())
            raise SystemExit(1) from exc

        next_version: str = self._version_to_string(result)

        if options.dry_run:
            logger.info("Would write new version %s", next_version)
            return
        if dynamic_version_config:
            replace_dynamic_version(dynamic_version_config, next_version)
        else:
            config.set_pyproject_value(next_version, "project", "version")
            project.write_pyproject(True)

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
    def _setup_logger(self, trace: bool, debug: bool) -> None:
        level: int = INFO
        if debug:
            level = DEBUG
        if trace:
            level = TRACE
        logger.setLevel(level)

    @traced_function
    def _version_to_string(self, version: Version) -> str:
        result: str = Pep440VersionFormatter().format(version)
        return result
