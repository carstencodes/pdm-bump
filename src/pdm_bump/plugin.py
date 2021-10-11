from argparse import ArgumentParser, Namespace
from typing import Optional
from pdm.cli.commands.base import BaseCommand
from pdm import termui
from pdm.core import Project
from pep440_version_utils import Version

class BumpCommand(BaseCommand):
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('what', action='store', choices=['major', 'minor', 'micro', 'pre-release', 'no-pre-release'], default=None, help="The part of the version to bump according to PEP 440: major.minor.micro.")
        parser.add_argument('--pre', action='store', choices=['alpha', 'beta', 'rc', 'c'], default=None, help="Sets a pre-release on the current version. If a pre-release is set, it can be removed using the final option. A new pre-release must greater then the current version. See PEP440 for details.")
        parser.add_argument("--dry-run", action='store_false', help='Do not perform a log-in')
        parser.description = "Bumps the version to a next version according to PEP440."

    def handle(self, project: Project, options: Namespace) -> None:
        version_value: Optional[str] = None
        log = project.core.ui.echo
        config: dict = project.pyproject
        if "project" in config and "version" in config["project"]:
            version_value = str(config["project"]["version"])

        if version_value is None:
            log (termui.red("Cannot find version in {}".format(termui.bold(project.pyproject_file))))
            return

        version: Version = Version(version_value)
        next_version: Optional[Version] = None
        if options.what is not None:
            if "major" == options.what:
                next_version = version.next_major()
            elif "minor" == options.what:
                next_version = version.next_minor()
            elif "micro" == options.what:
                next_version = version.next_micro()
            elif "pre-release" == options.what:
                if options.pre is not None:
                    if "alpha" == options.pre:
                        next_version = version.next_alpha()
                    elif "beta" == options.pre:
                        next_version = version.next_beta()
                    elif options.pre in ["rc", "c"]:
                        next_version = version.next_release_candidate()
                    else:
                        log(termui.red("E1"))
                        return
                else:
                    log(termui.red("E2"))
                    return
            elif "no-pre-release" == options.what:
                next_version = Version("{major}.{minor}.{micro}".format(
                    major=version.major,
                    minor=version.minor,
                    micro=version.micro
                ))
            else:
                log(termui.red("E3"))
                return
        
        else:
            log(termui.red("E4"))
            return

        if next_version is not None:
            project.pyproject["project"]["version"] = str(next_version)
            project.write_pyproject(True)
        else:
            return log(termui.red("E5"))
            return

