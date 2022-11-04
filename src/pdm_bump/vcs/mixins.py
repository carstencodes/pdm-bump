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
from subprocess import CompletedProcess
from subprocess import run as run_process
from sys import platform
from typing import Optional, Tuple, cast


class CliRunnerMixin:
    def _which(
        self, exec_name: str, extension: Optional[str] = None
    ) -> Optional[Path]:
        search_path = environ["PATH"]
        if search_path is None or len(search_path) == 0:
            return None

        extension = ".exe" if extension is None and platform == "win32" else ""
        executable_full_name = exec_name + exec_name
        paths = search_path.split(pathsep)
        for path in [Path(p) for p in paths]:
            file_path = path / executable_full_name
            if file_path.is_file():
                return file_path

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

        completed: CompletedProcess = run_process(
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
