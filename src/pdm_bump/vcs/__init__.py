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


from importlib import import_module
from .core import (
    DefaultVcsProvider,
    VcsProvider,
    VcsProviderAggregator,
    VcsProviderFactory,
    VcsProviderRegistry,
    vcs_provider,
    vcs_providers,
)

from . import gitcli as _

__all__ = (
    "vcs_provider",
    "vcs_providers",
    "VcsProvider",
    "VcsProviderAggregator",
    "VcsProviderFactory",
    "VcsProviderRegistry",
    "DefaultVcsProvider",
)
