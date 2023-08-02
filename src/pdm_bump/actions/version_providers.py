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

from abc import ABC, abstractmethod
from enum import IntEnum
from functools import cached_property
from typing import Union, cast

from ..core.logging import logger
from ..core.version import Pep440VersionFormatter, Version
from ..vcs import CommitStatistics, CommitType
from .base import VersionModifier
from .increment import (
    DevelopmentVersionIncrementingVersionModifier,
    EpochIncrementingVersionModifier,
    MajorIncrementingVersionModifier,
    MicroIncrementingVersionModifier,
    MinorIncrementingVersionModifier,
    PostVersionIncrementingVersionModifier,
)
from .poetry_like import PoetryLikePreReleaseVersionModifier


class _NoopVersionModifier(VersionModifier):
    def create_new_version(self) -> Version:
        return self.current_version


class Rating(IntEnum):
    """"""

    UNDEFINED = (0,)
    NOOP = (10,)
    LOCAL = (20,)
    DEVELOPMENT = 30
    POST = (40,)
    PRERELEASE = 50
    MICRO = 60
    MINOR = 70
    MAJOR = 80
    EPOCH = 90


class VersionPolicy(ABC):
    """"""

    def __init__(self, version: Version) -> None:
        """"""
        self.__version = version

    @abstractmethod
    def get_modifier(
        self, statistics: CommitStatistics, is_clean_repository: bool = True
    ) -> VersionModifier:
        """"""
        raise NotImplementedError()

    def save_version(self, version: Version) -> None:
        """"""
        version_formatted: str = Pep440VersionFormatter().format(version)
        logger.debug("Would save version %s", version_formatted)

    @property
    def _version(self) -> Version:
        return self.__version


class RatingBasedVersionPolicy(VersionPolicy):
    """"""

    def __init__(self, version: Version) -> None:
        """"""
        super().__init__(version)
        self.__version = version

    def get_modifier(
        self, statistics: CommitStatistics, is_clean_repository: bool = True
    ) -> VersionModifier:
        """"""
        if len(statistics.commit_type_count) == 0:
            return _NoopVersionModifier(self.__version, self)

        max_rating = self._get_max_rating(statistics, is_clean_repository)
        logger.debug(
            "Running with a version rating for the history of %s", max_rating
        )

        modifier: VersionModifier = _NoopVersionModifier(self.__version, self)

        if max_rating >= Rating.EPOCH:
            modifier = EpochIncrementingVersionModifier(self.__version, self)
        elif max_rating >= Rating.MAJOR:
            modifier = MajorIncrementingVersionModifier(self.__version, self)
        elif max_rating >= Rating.MINOR:
            modifier = MinorIncrementingVersionModifier(self.__version, self)
        elif max_rating >= Rating.MICRO:
            modifier = MicroIncrementingVersionModifier(self.__version, self)
        elif max_rating >= Rating.PRERELEASE:
            modifier = PoetryLikePreReleaseVersionModifier(
                self.__version, self
            )
        elif max_rating >= Rating.POST:
            modifier = PostVersionIncrementingVersionModifier(
                self.__version, self
            )
        elif max_rating >= Rating.DEVELOPMENT:
            modifier = DevelopmentVersionIncrementingVersionModifier(
                self.__version, self
            )
        elif max_rating >= Rating.LOCAL:
            raise NotImplementedError()

        logger.debug("Returning modifier %s", modifier)
        return modifier

    def _get_max_rating(self, statistics, is_clean_repository) -> int:
        """"""
        max_rating: int = -1
        current_rating: Union[Rating, int]
        for commit_type, count in statistics.commit_type_count.items():
            current_rating = self._rate_commit_type(commit_type)
            logger.debug(
                "Found %i commit(s) of type %s rated as %s",
                count,
                commit_type.name,
                current_rating,
            )

            if isinstance(current_rating, Rating):
                current_rating = current_rating.value
            current_rating = cast(int, current_rating)
            max_rating = max(max_rating, current_rating)

        logger.debug(
            "After evaluating all commits, the rating is set to %i", max_rating
        )

        if statistics.contains_breaking_changes:
            current_rating = self._rate_breaking_change()
            logger.debug(
                "Found at least one breaking change rated as %s",
                current_rating,
            )
            if isinstance(current_rating, Rating):
                current_rating = current_rating.value
            current_rating = cast(int, current_rating)
            max_rating = max(max_rating, current_rating)

        if not is_clean_repository:
            current_rating = self._rate_dirty_repository()
            logger.debug(
                "Running on a dirty repository rated as %s", current_rating
            )
            if isinstance(current_rating, Rating):
                current_rating = current_rating.value
            current_rating = cast(int, current_rating)
            max_rating = max(max_rating, current_rating)

        logger.debug("Rating set to %i", max_rating)
        return max_rating

    @abstractmethod
    def _rate_commit_type(self, c_type: CommitType) -> Union[Rating, int]:
        """"""
        raise NotImplementedError()

    def _rate_breaking_change(self) -> Union[Rating, int]:
        """"""
        return Rating.MAJOR

    def _rate_dirty_repository(self) -> Union[Rating, int]:
        """"""
        return Rating.LOCAL


class SetBasedVersionPolicy(RatingBasedVersionPolicy):
    """"""

    @property
    @abstractmethod
    def epoch_increments(self) -> frozenset[CommitType]:
        """"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def major_increments(self) -> frozenset[CommitType]:
        """"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def minor_increments(self) -> frozenset[CommitType]:
        """"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def micro_increments(self) -> frozenset[CommitType]:
        """"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def post_increments(self) -> frozenset[CommitType]:
        """"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def dev_increments(self) -> frozenset[CommitType]:
        """"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def local_increments(self) -> frozenset[CommitType]:
        """"""
        raise NotImplementedError()

    def _rate_commit_type(self, c_type: CommitType) -> Union[Rating, int]:
        rating: Rating = Rating.NOOP

        if c_type in self.epoch_increments:
            rating = Rating.EPOCH
        elif c_type in self.major_increments:
            rating = Rating.MAJOR
        elif c_type in self.minor_increments:
            rating = Rating.MINOR
        elif c_type in self.micro_increments:
            rating = Rating.MICRO
        elif c_type in self.post_increments:
            rating = Rating.POST
        elif c_type in self.dev_increments:
            rating = Rating.DEVELOPMENT
        elif c_type in self.local_increments:
            rating = Rating.LOCAL

        return rating


class SemanticVersionPolicy(SetBasedVersionPolicy):
    """"""

    @cached_property
    def epoch_increments(self) -> frozenset[CommitType]:
        """"""
        return frozenset()

    @cached_property
    def major_increments(self) -> frozenset[CommitType]:
        """"""
        return frozenset()

    @cached_property
    def minor_increments(self) -> frozenset[CommitType]:
        """"""
        return frozenset(
            (
                CommitType.Feature,
                CommitType.Performance,
                CommitType.Refactoring,
            )
        )

    @cached_property
    def micro_increments(self) -> frozenset[CommitType]:
        """"""
        return frozenset(
            (CommitType.Bugfix, CommitType.Chore, CommitType.Documentation)
        )

    @cached_property
    def post_increments(self) -> frozenset[CommitType]:
        """"""
        return frozenset(
            (
                CommitType.Build,
                CommitType.CodeStyle,
                CommitType.ContinuousIntegration,
                CommitType.Test,
            )
        )

    @cached_property
    def dev_increments(self) -> frozenset[CommitType]:
        """"""
        return frozenset((CommitType.Undefined,))

    @cached_property
    def local_increments(self) -> frozenset[CommitType]:
        """"""
        return frozenset()
