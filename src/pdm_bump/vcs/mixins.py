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

from os import environ, pathsep
from pathlib import Path
from subprocess import run as stdlib_run_process
from sys import platform
from typing import Optional, Protocol, Tuple, Union, cast

from ..logging import logger


class _CompletedProcessLike(Protocol):
    @property
    def returncode(self) -> int:
        raise NotImplementedError()

    @property
    def stdout(self) -> str:
        raise NotImplementedError()

    @property
    def stderr(self) -> str:
        raise NotImplementedError()


class _ProcessRunningCallable(Protocol):
    def __call__(
        self,
        cmd: list[str],
        *,
        check: bool,
        capture_output: bool,
        cwd: Optional[Union[str, Path]],
        encoding: str = "utf-8",
    ) -> _CompletedProcessLike:
        raise NotImplementedError()


class ProcessRunner:
    run_process: Optional[_ProcessRunningCallable] = None

    def _run_process(
        self,
        cmd: list[str],
        *,
        check: bool,
        capture_output: bool,
        cwd: Optional[Union[str, Path]],
        encoding: str = "utf-8",
    ) -> _CompletedProcessLike:
        if self.run_process is not None:
            run_proc: _ProcessRunningCallable = cast(
                _ProcessRunningCallable, self.run_process
            )
            return run_proc(
                cmd,
                check=check,
                capture_output=capture_output,
                cwd=cwd,
                encoding=encoding,
            )

        return stdlib_run_process(
            cmd,
            check=check,
            capture_output=capture_output,
            cwd=cwd,
            encoding=encoding,
        )


class CliRunnerMixin(ProcessRunner):
    def _which(
        self, exec_name: str, extension: Optional[str] = None
    ) -> Optional[Path]:
        search_path = environ["PATH"]
        logger.debug(
            "Searching for executable '%s' using search path '%s'",
            exec_name,
            search_path,
        )
        if search_path is None or len(search_path) == 0:
            return None

        extension = ".exe" if extension is None and platform == "win32" else ""
        executable_full_name = exec_name + extension
        paths = search_path.split(pathsep)
        for path in [Path(p) for p in paths]:
            logger.debug(
                "Searching for '%s' in '%s'", executable_full_name, path
            )
            file_path = path / executable_full_name
            if file_path.is_file():
                logger.debug("Found %s", file_path)
                return file_path

        logger.debug("Could not find %s", executable_full_name)
        return None

    def run(
        self,
        /,
        executable: Path,
        args: Tuple[str, ...],
        *,
        raise_on_exit: bool = False,
        cwd: Optional[Path] = None,
    ) -> Tuple[int, str, str]:
        cmd = []
        cmd.append(str(executable))
        for arg in args:
            cmd.append(arg)

        logger.debug(
            "Running command '%s' with args [%s]",
            str(executable),
            ",".join(args),
        )

        completed: _CompletedProcessLike = self._run_process(
            cmd,
            check=raise_on_exit,
            capture_output=True,
            cwd=cwd,
            encoding="utf-8",
        )

        logger.debug("Process exited with code %d", completed.returncode)
        logger.debug(
            "Process wrote the following to stdout: \n%s", completed.stdout
        )
        logger.debug(
            "Process wrote the following to stderr: \n%s", completed.stderr
        )

        return (
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
