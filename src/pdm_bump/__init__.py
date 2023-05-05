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


from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as __get_version
from typing import Final

from .cli import main as register_plugin

main = register_plugin


def _get_version(name: str) -> str:
    """

    Parameters
    ----------
    name: str :


    Returns
    -------

    """
    try:
        return __get_version(name)
    except PackageNotFoundError:
        # Only occurs in development, since package is not installed properly
        return "0.0.0"


__version__: Final[str] = _get_version(__package__ or __name__)

__all__: list[str] = [main.__name__]
