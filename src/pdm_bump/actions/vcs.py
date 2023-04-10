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

from typing import final

from ..core.logging import logger
from ..core.version import Pep440VersionFormatter, Version
from ..vcs import VcsProvider, VcsProviderAggregator
from .base import VersionConsumer, action


@final
@action
class CreateTagFromVersion(VersionConsumer, VcsProviderAggregator):
    name: str = "tag"
    description: str = "Create a VCS revision tag from the current version"

    def __init__(
        self, version: Version, vcs_provider: VcsProvider, **kwargs
    ) -> None:
        VersionConsumer.__init__(self, version, **kwargs)
        VcsProviderAggregator.__init__(self, vcs_provider, **kwargs)

    def run(self, dry_run: bool = False) -> None:
        if not dry_run:
            self.vcs_provider.create_tag_from_version(self.current_version)
        else:
            logger.info(
                "Would create tag v%s",
                Pep440VersionFormatter().format(self.current_version),
            )
