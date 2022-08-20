from argparse import ArgumentParser, Namespace
from typing import Optional, Union, cast

from pdm import termui
from pdm.cli.commands.base import BaseCommand
from pdm.core import Project
from pep440_version_utils import Version

from .config import Config
from .logging import logger


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
            choices=["major", "minor", "micro", "patch", "pre-release", "no-pre-release"],
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
            "--dry-run", action="store_false", help="Do not perform a log-in"
        )

    def handle(self, project: Project, options: Namespace) -> None:
        config: Config = Config(project.pyproject)
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
        next_version: Optional[Version] = None

        result: Union[Version, str] = _do_bump(version, options.what, options.pre)

        if not isinstance(result, str):
            next_version = cast(Optional[Version], result)
            if next_version is not None:
                config.set_pyproject_value(str(next_version), "project, version")
                project.write_pyproject(True)
            else:
                self._log_error(
                    "Failed to update version: No version set in {}".format(
                        termui.bold(project.pyproject_file)
                    )
                )
        else:
            self._log_error(project, str(result))

    def _log_error(self, project: Project, message: str) -> None:
        formatted_message: str = termui.red(message)
        project.core.ui.echo(formatted_message)
