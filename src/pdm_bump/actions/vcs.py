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


from typing import Optional, final

from ..core.logging import logger, silenced
from ..core.version import Pep440VersionFormatter, Version
from ..vcs import (
    CommitStatistics,
    CommitType,
    History,
    VcsProvider,
    VcsProviderAggregator,
)
from .base import VersionConsumer, VersionModifier, VersionPersister, action
from .increment import (
    DevelopmentVersionIncrementingVersionModifier,
    MajorIncrementingVersionModifier,
    MicroIncrementingVersionModifier,
    MinorIncrementingVersionModifier,
    PostVersionIncrementingVersionModifier,
)


@final
@action
class CreateTagFromVersion(VersionConsumer, VcsProviderAggregator):
    """"""

    name: str = "tag"
    description: str = "Create a VCS revision tag from the current version"

    def __init__(
        self, version: Version, vcs_provider: VcsProvider, **kwargs
    ) -> None:
        VersionConsumer.__init__(self, version, **kwargs)
        VcsProviderAggregator.__init__(self, vcs_provider, **kwargs)

    def run(self, dry_run: bool = False) -> None:
        """

        Parameters
        ----------
        dry_run: bool :
             (Default value = False)

        Returns
        -------

        """
        if not dry_run:
            self.vcs_provider.create_tag_from_version(self.current_version)
        else:
            logger.info(
                "Would create tag v%s",
                Pep440VersionFormatter().format(self.current_version),
            )

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return set(["vcs_provider"]).union(
            VersionConsumer.get_allowed_arguments()
        )


class _VcsVersionDerivatingVersionConsumer(
    VersionConsumer, VcsProviderAggregator
):
    """"""

    def __init__(
        self, version: Version, vcs_provider: VcsProvider, **kwargs
    ) -> None:
        """"""
        VersionConsumer.__init__(self, version, **kwargs)
        VcsProviderAggregator.__init__(self, vcs_provider, **kwargs)

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return set(["vcs_provider"]).union(
            VersionConsumer.get_allowed_arguments()
        )

    def save_version(self, _: Version) -> None:
        """"""
        # This does not persist anything
        pass  # pylint: disable=W0107

        # This must be refactored - Refactor! TODO  # pylint: disable=W0511

    def derive_next_version(self) -> Optional[Version]:  # pylint:disable=R0914
        """"""
        history: History = self.vcs_provider.get_history()
        stats: CommitStatistics = history.get_commit_stats

        keys: frozenset[CommitType] = frozenset(stats.commit_type_count.keys())

        if len(keys) == 0:
            logger.info("History clean. No need to update version")
            return None

        has_features: bool = CommitType.Feature in keys
        has_bugfixes: bool = CommitType.Bugfix in keys
        has_chores: bool = CommitType.Chore in keys
        has_documentation: bool = CommitType.Documentation in keys
        has_quality_assurance: bool = CommitType.QualityAssurance in keys
        has_build: bool = CommitType.Build in keys
        has_ci: bool = CommitType.ContinuousIntegration in keys
        has_code_style: bool = CommitType.CodeStyle in keys
        has_refactoring: bool = CommitType.Refactoring in keys
        has_performance: bool = CommitType.Performance in keys
        has_test: bool = CommitType.Test in keys
        has_undefined: bool = CommitType.Undefined in keys

        modifier: VersionModifier
        if stats.contains_breaking_changes:
            logger.info("History contains breaking changes.")
            modifier = MajorIncrementingVersionModifier(
                self.current_version, self, True
            )
        elif has_features or has_performance or has_refactoring:
            logger.info("History contains non-breaking feature commits")
            modifier = MinorIncrementingVersionModifier(
                self.current_version, self, True
            )
        elif has_bugfixes or has_documentation or has_chores:
            logger.info("History only contains minor fixes in commits")
            modifier = MicroIncrementingVersionModifier(
                self.current_version, self, True
            )
        elif (
            has_quality_assurance
            or has_test
            or has_code_style
            or has_build
            or has_ci
        ):
            logger.info(
                "History does not contain functional or relevant changes"
            )
            modifier = PostVersionIncrementingVersionModifier(
                self.current_version, self
            )
        elif has_undefined or not self.vcs_provider.is_clean:
            logger.info("History contains no relevant changes.")
            modifier = DevelopmentVersionIncrementingVersionModifier(
                self.current_version, self
            )
        else:
            logger.info("Nothing to do")
            return None

        with silenced(logger):
            new_version: Version = modifier.create_new_version()
            return new_version


@final
@action
class SuggestNewVersion(_VcsVersionDerivatingVersionConsumer):
    """"""

    name: str = "suggest"
    description: str = "Suggests a new version from the VCS"

    def run(self, dry_run: bool = False) -> None:
        """"""
        logger.debug("Ignoring dry run parameter set to %s", dry_run)
        new_version: Optional[Version] = self.derive_next_version()
        if new_version is not None:
            next_version: str = Pep440VersionFormatter().format(new_version)
            logger.info("Would suggest new version: %s", next_version)


@final
@action
class AutoSelectVersionModifier(
    VersionModifier, _VcsVersionDerivatingVersionConsumer
):
    """"""

    name: str = "auto"
    description: str = "Create a new version from the VCS"

    def __init__(
        self,
        version: Version,
        persister: VersionPersister,
        vcs_provider: VcsProvider,
        **kwargs,
    ) -> None:
        """"""
        VersionModifier.__init__(self, version, persister, **kwargs)
        _VcsVersionDerivatingVersionConsumer.__init__(
            self, version, vcs_provider, **kwargs
        )

    def create_new_version(self) -> Version:
        """"""
        raise NotImplementedError
