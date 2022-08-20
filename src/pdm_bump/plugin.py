from argparse import ArgumentParser, Namespace
from typing import Optional, Union, Tuple, Final, cast
from logging import DEBUG, INFO, WARN

from pdm import termui
from pdm.cli.commands.base import BaseCommand
from pdm.core import Project

from .version import Version, Pep440VersionFormatter

from .config import Config
from .logging import logger

from .action import VersionModifier, VersionModifierFactory, create_actions, ActionCollection

def _do_bump(
    version: Version, what: Optional[str], pre: Optional[str]
) -> Union[Version, str]:
    if what is not None:
        if "major" == what:
            return version.next_major()
        elif "minor" == what:
            return version.next_minor()
        elif "micro" == what or "patch" == what:
            return version.next_micro()
        elif "pre-release" == what:
            if pre is not None:
                if "alpha" == pre:
                    return version.next_alpha()
                elif "beta" == pre:
                    return version.next_beta()
                elif pre in ["rc", "c"]:
                    return version.next_release_candidate()
                else:
                    return "Invalid pre-release: {}. Must be one of alpha, beta, rc or c".format(
                        pre
                    )
            else:
                return "No pre-release kind set. Please provide one of the following values: alpha, beta, rc, c"
        elif "no-pre-release" == what:
            return Version(
                "{major}.{minor}.{micro}".format(
                    major=version.major, minor=version.minor, micro=version.micro
                )
            )
        else:
            return "Invalid version part to bump: {}. Must be one of major, minor, micro/patch, pre-release or no-prerelease.".format(
                what
            )

    else:
        return "No version part to bump set. Please provide on of the following values: major, minor, micro, pre-release or no-pre-release"


class BumpCommand(BaseCommand):
    name: str = "bump"
    description: str = "Bumps the version to a next version according to PEP440."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "what",
            action="store",
            choices=[
                "major",
                "minor",
                "micro",
                "patch",
                "pre-release",
                "no-pre-release",
            ],
            default=None,
            help="The part of the version to bump according to PEP 440: major.minor.micro.",
        )
        parser.add_argument(
            "--pre",
            action="store",
            choices=["alpha", "beta", "rc", "c"],
            default=None,
            help="Sets a pre-release on the current version. If a pre-release is set, it can be removed using the final option. A new pre-release must greater then the current version. See PEP440 for details.",
        )
        parser.add_argument(
            "--dry-run", "-n", action="store_true", help="Do not store incremented version"
        )
        parser.add_argument(
            "--micro", action="store_true", help="When setting pre-release, specifies whether micro version shall be incremented as well"
        )
        parser.add_argument(
            "--reset", action="store_true", help="When setting epoch, reset version to 1.0.0"
        )
        parser.add_argument(
            "--remove", action="store_true", help="When incrementing major, minor, micro or epoch, remove all pre-release parts"
        )

    def handle(self, project: Project, options: Namespace) -> None:
        config: Config = Config(project.pyproject)
        self._setup_logger(options.verbose)
        
        version_value: Optional[str] = cast(
            Optional[str], config.get_pyproject_value("project", "version")
        )

        if version_value is None:
            self._log_error(
                project,
                "Cannot find version in {}".format(termui.bold(project.pyproject_file)),
            )
            return

        version: Version = Version(version_value)

        actions: ActionCollection = self._get_actions(
            options.micro, options.reset, options.remove)
        
        
        modifier: VersionModifier = self._get_action(actions, version, options.what, options.pre)
        
        result: Version = modifier.create_new_version()

        config.set_pyproject_value(str(next_version), "project, version")
        if not options.dry_run:
            project.write_pyproject(True)
    
    def _get_action(self, actions: ActionCollection, version: Version, what: str, pre: Optional[str]) -> VersionModifier:
        modifierFactory: VersionModifierFactory
        if pre is not None:
            modifierFactory = actions.get_action_with_option(what, pre)
        else:
            modifierFactory = actions.get_action(what)
            
        modifier: VersionModifier = modifierFactory(version)
        return modifier
        
            
    def _get_actions(self, increment_micro: bool, reset_version: bool, remove_parts: bool) -> ActionCollection:
        actions: ActionCollection = create_actions(
            increment_micro=increment_micro, 
            reset_version=reset_version,
            remove_parts=remove_parts)
        
        return actions

    def _log_error(self, project: Project, message: str) -> None:
        formatted_message: str = termui.red(message)
        project.core.ui.echo(formatted_message)
        
    def _setup_logger(self, verbosity_level: int) -> None:
        log_levels: Final[Tuple[int, int, int]] = (WARN, INFO, DEBUG)
        log_level_id: int = min(verbosity_level, len(log_levels) - 1)
        log_level: int = log_levels[log_level_id]
        logger.setLevel(log_level)
        
    def _version_to_string(self, version: Version) -> str:
        result: str = Pep440VersionFormatter().format(version)
        return result
