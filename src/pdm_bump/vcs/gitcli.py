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


from functools import cached_property
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile
from typing import Optional, cast

from pdm_pfsc.logging import logger
from pdm_pfsc.proc import CliRunnerMixin

from ..core.version import Pep440VersionFormatter, Version
from .core import HunkSource, VcsProvider, VcsProviderError, vcs_provider
from .git import GitCommonVcsProviderFactory
from .history import Commit, History


class GitCliVcsProvider(VcsProvider, CliRunnerMixin):
    """"""

    __GIT_EXECUTABLE_NAME = "git"

    @cached_property
    def git_executable_path(self) -> Path:
        """"""
        logger.debug("Searching for %s executable", self.__GIT_EXECUTABLE_NAME)
        git_executable_path: Optional[Path] = self._which(
            self.__GIT_EXECUTABLE_NAME
        )
        if git_executable_path is None:
            raise FileNotFoundError(
                f"No executable '{self.__GIT_EXECUTABLE_NAME}' found in PATH"
            )
        return cast("Path", git_executable_path)

    @cached_property
    def git_root_dir_path(self) -> Path:
        """"""
        try:
            logger.debug("Searching for git root directory")
            _ex, out, _err = self.run(
                self.git_executable_path,
                ("rev-parse", "--show-toplevel"),
                raise_on_exit=True,
                cwd=self.current_path,
            )
            git_root_dir_path = Path(out.strip())
            logger.debug("Found git root directory at %s", git_root_dir_path)
            return git_root_dir_path
        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to receive git root directory. Reason: {cpe.stderr}"
            ) from cpe

    @property
    def is_available(self) -> bool:
        """"""
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
        """"""
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

    def check_in_items(self, message: str, *files: tuple[Path, ...]) -> None:
        """

        Parameters
        ----------
        message: str :

        *files: tuple[Path, ...] :


        Returns
        -------

        """
        try:
            args: list[str] = ["add", "--update"]
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
        """

        Parameters
        ----------
        version_formatted: str :


        Returns
        -------

        """
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
        """"""
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
        """"""
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
        """"""
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

    def get_history(self, since_last_tag: bool = True) -> History:
        """"""
        commit_history: str = ""
        if since_last_tag:
            last_tag: Optional[Version] = self.get_most_recent_tag()
            if last_tag is not None:
                last_tag_name: str = (
                    f"v{Pep440VersionFormatter().format(last_tag)}"
                )
                commit_history = f"{last_tag_name}..HEAD"

        try:
            _, output, _ = self.run(
                self.git_executable_path,
                ("log", commit_history, "--format=%s"),
                raise_on_exit=True,
                cwd=self.current_path,
            )
            logger.debug(
                "The following commits have been received for %s:\n%s",
                commit_history,
                output,
            )
            commit_texts: list[str] = output.split("\n")

            commits: list[Commit] = [
                Commit(t) for t in commit_texts if t.strip() != ""
            ]

            return History(commits)

        except CalledProcessError as cpe:
            raise VcsProviderError(
                f"Failed to receive commit history. Reason: {cpe.stderr}"
            ) from cpe

    def check_in_deltas(self, message: str, *hunks: HunkSource) -> None:
        """"""
        self.__apply_cached_patch(hunks)
        self.__commit_staged_files(message)

    def __apply_cached_patch(self, hunks: tuple[HunkSource, ...]) -> None:
        with NamedTemporaryFile(
            mode="wt",
            suffix=".patch",
            prefix="pdm-bump.git",
            delete=False,
        ) as target_file:
            for hunk in hunks:
                rel_path: Path = hunk.source_file_path.relative_to(
                    self.current_path
                )
                target_file.write(
                    f"diff --git {Path('a') / rel_path}"
                    f" {Path('b') / rel_path}\n"
                )
                for line in hunk.get_source_file_change_hunks():
                    logger.trace(line)
                    target_file.write(f"{line}\n")

            target_file.flush()

            logger.debug("Wrote hunks to %s", target_file.name)

            args = ["apply", "--cached"]
            working_dir = self.current_path
            if self.git_root_dir_path != self.current_path:
                directory = self.current_path.relative_to(
                    self.git_root_dir_path
                )
                args.extend(["--directory", f"{directory}"])
                working_dir = self.git_root_dir_path
            args.append(f"{target_file.name}")

            try:
                self.run(
                    self.git_executable_path,
                    tuple(args),
                    raise_on_exit=True,
                    cwd=working_dir,
                )
            finally:
                Path(target_file.name).unlink()

    def __commit_staged_files(self, message) -> None:
        with NamedTemporaryFile(
            "wt",
            suffix="message",
            prefix="pdm-bump.git",
            delete=False,
        ) as target_file:
            logger.trace(message)
            target_file.write(message)

            target_file.flush()
            logger.debug("Wrote message '%s' to %s", message, target_file.name)

            try:
                self.run(
                    self.git_executable_path,
                    ("commit", "-F", f"{target_file.name}"),
                    raise_on_exit=True,
                    cwd=self.current_path,
                )
            finally:
                Path(target_file.name).unlink()


@vcs_provider("git-cli")
class GitCliVcsProviderFactory(GitCommonVcsProviderFactory):
    """"""

    def _create_provider(self, path: Path) -> VcsProvider:
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        return GitCliVcsProvider(path)
