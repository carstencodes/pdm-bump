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
from functools import cached_property
from pathlib import Path
from subprocess import CalledProcessError
from typing import List, Optional, Tuple, cast

from ..logging import logger
from ..version import Version
from .core import VcsProvider, VcsProviderError, vcs_provider
from .git import GitCommonVcsProviderFactory
from .mixins import CliRunnerMixin


class GitCliVcsProvider(VcsProvider, CliRunnerMixin):
    __GIT_EXECUTABLE_NAME = "git"

    @cached_property
    def git_executable_path(self) -> Path:
        logger.debug("Searching for %s executable", self.__GIT_EXECUTABLE_NAME)
        git_executable_path: Optional[Path] = self._which(
            self.__GIT_EXECUTABLE_NAME
        )
        if git_executable_path is None:
            raise FileNotFoundError(
                f"No executable '{self.__GIT_EXECUTABLE_NAME}' found in PATH"
            )
        return cast(Path, git_executable_path)

    @property
    def is_available(self) -> bool:
        logger.debug("Checking, if we're working on a git repository")
        exit_code, _out, _err = self.run(
            self.git_executable_path,
            ("rev-parse", "--root-dir"),
            raise_on_exit=False,
            cwd=self.current_path,
        )
        return 0 == exit_code

    @property
    def is_clean(self) -> bool:
        try:
            logger.debug("Checking, if there are any changes")
            _ex, out, _err = self.run(
                self.git_executable_path,
                ("status", "--porcelain"),
                cwd=self.current_path,
                raise_on_exit=True,
            )

            dirty_files = [
                ln
                for ln in out.splitlines()
                if not ln.strip().startswith("??")
            ]

            logger.debug(
                "The following files have been reported as modified: \n %s",
                "\n".join(dirty_files),
            )

            return len(dirty_files) == 0
        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to check if {self.current_path} is a clean "
                f"git repository. Reason: {cpe.stderr}"
            ) from cpe

    def check_in_items(self, message: str, *files: Tuple[Path, ...]) -> None:
        try:
            args: List[str] = ["add", "--update"]
            args.extend(str(f) for f in files)
            logger.debug(
                "Checking in the following files: \n%s",
                ", ".join([str(f) for f in files]),
            )
            _ = self.run(
                self.git_executable_path,
                tuple(args),
                raise_on_exit=True,
                cwd=self.current_path,
            )
            logger.debug("Creating new commit with message '%s'", message)
            _ = self.run(
                self.git_executable_path,
                ("commit", "-m", f'"{message}"'),
                raise_on_exit=True,
                cwd=self.current_path,
            )
        except CalledProcessError as cpe:
            f_args = ",".join([str(f) for f in files])
            raise VcsProviderError(
                f"Failed to check in items in {self.current_path} "
                f"using {f_args}. Reason: {cpe.stderr}"
            ) from cpe

    def create_tag_from_string(self, version_formatted: str) -> None:
        try:
            logger.info(
                "Creating tag '%s' on current commit.", version_formatted
            )
            _ = self.run(
                self.git_executable_path,
                ("tag", version_formatted),
                raise_on_exit=True,
                cwd=self.current_path,
            )
        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to create tag {version_formatted} "
                f"in {self.current_path}. Reason: {cpe.stderr}"
            ) from cpe

    def get_most_recent_tag(self) -> Optional[Version]:
        try:
            logger.debug("Checking for most recent tag.")
            _, output, _ = self.run(
                self.git_executable_path,
                ("describe", "--tags", "--abbrev=0"),
                raise_on_exit=True,
                cwd=self.current_path,
            )
        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to receive most recent tag. . Reason: {cpe.stderr}"
            ) from cpe

        if output.strip() == "":
            logger.debug("Could not find a tagged version.")
            return None

        logger.debug("Found version '%s'", output)
        return Version.from_string(output)

    def get_number_of_changes_since_last_release(self) -> int:
        try:
            logger.debug("Searching last tag ...")
            _, output, _ = self.run(
                self.git_executable_path,
                ("describe", "--tags"),
                raise_on_exit=False,
                cwd=self.current_path,
            )
            if output.strip() == "":
                raise VcsProviderError("Failed to fetch most recent tag")
            logger.debug("Found tag '%s'", output)
            _, output, _ = self.run(
                self.git_executable_path,
                ("rev-list", f"{output}..HEAD", "--count"),
                raise_on_exit=True,
                cwd=self.current_path,
            )
            logger.debug("Git return %s changes", output)

            return int(output)
        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to receive number of commits since last tag."
                f" Reason: {cpe.stderr}"
            ) from cpe

    def get_changes_not_checked_in(self) -> int:
        try:
            logger.debug("Searching for changes")
            _, output, _ = self.run(
                self.git_executable_path,
                ("status", "--porcelain"),
                raise_on_exit=True,
                cwd=self.current_path,
            )
            logger.debug(
                "The following have been modified or added:\n%s", output
            )
            lines = output.split("\n")
            return len(lines)
        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to receive number of changes that are not committed."
                f" Reason: {cpe.stderr}"
            ) from cpe


@vcs_provider("git-cli")
class GitCliVcsProviderFactory(GitCommonVcsProviderFactory):
    def _create_provider(self, path: Path) -> VcsProvider:
        return GitCliVcsProvider(path)
