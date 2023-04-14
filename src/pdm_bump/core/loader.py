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

from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
from traceback import format_exc as get_traceback
from typing import Final

from .logging import logger, traced_function


# Justification: loader should be single instance only.
class _Loader:  # pylint: disable=R0903
    def __init__(self) -> None:
        self.__loaded: set[str] = set()

    @traced_function
    def load_modules_of_package(
        self, file_path: str, pkg_name: str, *skip: str
    ) -> None:
        file_pth = Path(file_path)
        if not file_pth.exists() or not file_pth.is_file():
            raise FileNotFoundError(file_path)

        pkg_path: Path = file_pth.absolute().parent

        for _, module_name, is_pkg in iter_modules([str(pkg_path)]):
            full_name: str = f"{pkg_name}.{module_name}"
            if (
                module_name not in skip
                and not is_pkg
                and full_name not in self.__loaded
            ):
                try:
                    logger.debug(
                        "Loading module %s from package %s",
                        module_name,
                        pkg_name,
                    )
                    rel_module_name = f".{module_name}"
                    _ = import_module(rel_module_name, pkg_name)
                    self.__loaded.add(full_name)
                except ImportError:
                    logger.exception(
                        "Error loading module %s from %s",
                        module_name,
                        pkg_name,
                        exc_info=False,
                    )
                    logger.debug("Error loading module: %s", get_traceback())


# Justification: Intended to use as a regular variable
loader: Final[_Loader] = _Loader()  # pylint: disable=C0103
