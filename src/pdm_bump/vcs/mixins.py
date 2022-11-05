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
from typing import AnyStr, Optional, Protocol, Tuple, Union, cast

from ..logging import logger


class _CompletedProcessLike(Protocol):
    @property
    def returncode(self) -> int:
        raise NotImplementedError()

    @property
    def stdout(self) -> AnyStr:
        raise NotImplementedError()

    @property
    def stderr(self) -> AnyStr:
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
    run_process: _ProcessRunningCallable = cast(
        _ProcessRunningCallable, stdlib_run_process
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

        completed: _CompletedProcessLike = super().run_process(
            cmd,
            check=raise_on_exit,
            capture_output=True,
            cwd=cwd,
            encoding="utf-8",
        )
        return (
            completed.returncode,
            cast(str, completed.stdout),
            cast(str, completed.stderr),
        )
