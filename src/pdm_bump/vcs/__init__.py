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

from ..core.loader import loader as _loader
from .core import (
    DefaultVcsProvider,
    VcsProvider,
    VcsProviderAggregator,
    VcsProviderFactory,
    VcsProviderRegistry,
    vcs_provider,
    vcs_providers,
)

# Justification: Add items to registry
_loader.load_modules_of_package(
    __file__, __name__, "__init__", "core", "mixins"
)

__all__ = (
    "vcs_provider",
    "vcs_providers",
    "VcsProvider",
    "VcsProviderAggregator",
    "VcsProviderFactory",
    "VcsProviderRegistry",
    "DefaultVcsProvider",
)
