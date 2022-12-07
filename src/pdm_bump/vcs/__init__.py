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
from .core import (
    DefaultVcsProvider,
    VcsProvider,
    VcsProviderFactory,
    VcsProviderRegistry,
    vcs_provider,
    vcs_providers,
)

# Justification: Add items to registry
from .gitcli import *  # noqa: disable=F401,F403

__all__ = (
    "vcs_provider",
    "vcs_providers",
    "VcsProvider",
    "VcsProviderFactory",
    "VcsProviderRegistry",
    "DefaultVcsProvider",
)
