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


from abc import abstractmethod
from functools import cached_property
from typing import Optional, final

from pdm_pfsc.logging import logger, silenced

from ..core.version import Pep440VersionFormatter, Version
from ..vcs import (
    CommitStatistics,
    CommitType,
    History,
    VcsProvider,
    VcsProviderAggregator,
)
from .base import VersionConsumer, VersionModifier, VersionPersister, action
from .version_providers import SemanticVersionPolicy, VersionPolicy


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

    def run(self, dry_run: bool = False) -> Version:
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

        return self.current_version

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return {"vcs_provider"}.union(VersionConsumer.get_allowed_arguments())


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
        return {"vcs_provider"}.union(VersionConsumer.get_allowed_arguments())

    def save_version(self, _: Version) -> None:
        """"""
        # This does not persist anything
        pass  # pylint: disable=W0107

    def derive_next_version(self) -> Optional[Version]:
        """"""
        history: History = self.vcs_provider.get_history()
        stats: CommitStatistics = history.get_commit_stats

        keys: frozenset[CommitType] = frozenset(stats.commit_type_count.keys())

        if len(keys) == 0:
            logger.info("History clean. No need to update version")
            return None

        modifier: VersionModifier = self._version_policy.get_modifier(
            stats, self.vcs_provider.is_clean
        )

        with silenced(logger):
            new_version: Version = modifier.create_new_version()
            return new_version

    @property
    @abstractmethod
    def _version_policy(self) -> VersionPolicy:
        """"""
        raise NotImplementedError()


@final
@action
class SuggestNewVersion(_VcsVersionDerivatingVersionConsumer):
    """"""

    name: str = "suggest"
    description: str = "Suggests a new version from the VCS"

    def run(self, dry_run: bool = False) -> Version:
        """"""
        logger.debug("Ignoring dry run parameter set to %s", dry_run)
        new_version: Optional[Version] = self.derive_next_version()
        if new_version is not None:
            next_version: str = Pep440VersionFormatter().format(new_version)
            logger.info("Would suggest new version: %s", next_version)

        return new_version or self.current_version

    @cached_property
    def _version_policy(self) -> VersionPolicy:
        return SemanticVersionPolicy(self.current_version)


@final
@action
class AutoSelectVersionModifier(
    VersionModifier, _VcsVersionDerivatingVersionConsumer
):
    """"""

    name: str = "auto"
    description: str = "Automatically create a new "
    "version for the project based on recent history."

    def __init__(
        self,
        version: Version,
        persister: VersionPersister,
        vcs_provider: VcsProvider,
        **kwargs,
    ) -> None:
        """"""
        # For unknown reasons, the modifier complains
        # about a missing vcs_provider argument
        VersionModifier.__init__(
            self, version, persister, vcs_provider=vcs_provider, **kwargs
        )
        _VcsVersionDerivatingVersionConsumer.__init__(
            self, version, vcs_provider, **kwargs
        )

    def create_new_version(self) -> Version:
        """"""
        new_version: Optional[Version] = self.derive_next_version()

        return new_version or self.current_version

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return {"vcs_provider"}.union(VersionModifier.get_allowed_arguments())

    @cached_property
    def _version_policy(self) -> VersionPolicy:
        return SemanticVersionPolicy(self.current_version)
