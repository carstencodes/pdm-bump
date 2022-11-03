#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
from pathlib import Path
from subprocess import CalledProcessError
from typing import List, Optional, Tuple

from ..version import Version
from .core import VcsProvider, VcsProviderError, vcs_provider
from .git import GitCommonVcsProviderFactory
from .mixins import CliRunnerMixin


class GitCliVcsProvider(VcsProvider, CliRunnerMixin):
    __GIT_EXECUTABLE_NAME = "git"

    @property
    def is_available(self) -> bool:
        exit_code, _out, _err = self.run(
            self.__GIT_EXECUTABLE_NAME,
            ("rev-parse", "--root-dir"),
            raise_on_exit=False,
            cwd=self.current_path,
        )
        return 0 == exit_code

    @property
    def is_clean(self) -> bool:
        try:
            _ex, out, _err = self.run(
                self.__GIT_EXECUTABLE_NAME,
                ("status", "--porcelain"),
                cwd=self.current_path,
                raise_on_exit=True,
            )

            dirty_files = [
                ln
                for ln in out.splitlines()
                if not ln.strip().startswith(b"??")
            ]

            return len(dirty_files) == 0
        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to check if {self.current_path} is a clean "
                f"git repository."
            ) from cpe

    def check_in_items(self, message: str, *files: Tuple[Path, ...]) -> None:
        try:
            args: List[str] = ["add", "--update"]
            args.extend(str(f) for f in files)
            _ = self.run(
                self.__GIT_EXECUTABLE_NAME,
                tuple(args),
                raise_on_exit=True,
                cwd=self.current_path,
            )
            _ = self.run(
                self.__GIT_EXECUTABLE_NAME,
                ("commit", "-m", f'"{message}"'),
                raise_on_exit=True,
                cwd=self.current_path,
            )
        except CalledProcessError as cpe:
            f_args = ",".join([str(f) for f in files])
            raise VcsProviderError(
                f"Failed to check in items in {self.current_path} "
                f"using {f_args}."
            ) from cpe

    def create_tag_from_string(self, version_formatted: str) -> None:
        try:
            _ = self.run(
                self.__GIT_EXECUTABLE_NAME,
                ("tag", f"v{version_formatted}"),
                raise_on_exit=True,
                cwd=self.current_path,
            )
        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to create tag f{version_formatted} "
                f"in {self.current_path}."
            ) from cpe

    def get_most_recent_tag(self) -> Optional[Version]:
        try:
            _, output, _ = self.run(
                self.__GIT_EXECUTABLE_NAME,
                ("describe", "--tags"),
                raise_on_exit=True,
                cwd=self.current_path,
            )
        except CalledProcessError as cpe:
            raise VcsProviderError(
                "Failed to receive most recent tag"
            ) from cpe

        if output.strip() == "":
            return None

        return Version.from_string(output)

    def get_number_of_changes_since_last_release(self) -> int:
        try:
            _, output, _ = self.run(
                self.__GIT_EXECUTABLE_NAME,
                ("describe", "--tags"),
                raise_on_exit=False,
                cwd=self.current_path,
            )
            if output.strip() == "":
                raise VcsProviderError("Failed to fetch most recent tag")
            _, output, _ = self.run(
                self.__GIT_EXECUTABLE_NAME,
                ("rev-list", f"{output}..HEAD", "--count"),
                raise_on_exit=True,
                cwd=self.current_path,
            )

            return int(output)
        except CalledProcessError as cpe:
            raise VcsProviderError(
                "Failed to receive number of commits" " since last tag."
            ) from cpe

    def get_changes_not_checked_in(self) -> int:
        try:
            _, output, _ = self.run(
                self.__GIT_EXECUTABLE_NAME,
                ("status", "--porcelain"),
                raise_on_exit=True,
                cwd=self.current_path,
            )
            lines = output.split("\n")
            return len(lines)
        except CalledProcessError as cpe:
            raise VcsProviderError(
                "Failed to receive number of changes" "that are not committed"
            ) from cpe


@vcs_provider("git-cli")
class GitCliVcsProviderFactory(GitCommonVcsProviderFactory):
    def _create_provider(self, path: Path) -> VcsProvider:
        return GitCliVcsProvider(path)
