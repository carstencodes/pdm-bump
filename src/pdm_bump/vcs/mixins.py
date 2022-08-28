#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
from io import StringIO
from pathlib import Path
from subprocess import CompletedProcess
from subprocess import run as run_process
from typing import Optional, Tuple, cast


class CliRunnerMixin:
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

        cp: CompletedProcess = run_process(
            cmd,
            check=raise_on_exit,
            capture_output=True,
            cwd=cwd,
            encoding="utf-8",
        )
        return (cp.returncode, cast(str, cp.stdout), cast(str, cp.stderr))
