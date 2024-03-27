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

from typing import Literal, Optional, final

from pdm_pfsc.logging import logger, traced_function

from ..core.version import Version
from .base import VersionModifier, action

# Comparable functions at poetry. Cf.
# https://python-poetry.org/docs/cli/#version


@final
@action
class PoetryLikePreMajorVersionModifier(VersionModifier):
    """"""

    name: str = "premajor"
    description: str = (
        "Prepares a new major version - like `poetry version premajor`"
    )

    @traced_function
    def create_new_version(self) -> Version:
        """"""
        if not self.current_version.is_final:
            logger.error(
                "Cannot create a new major pre-release "
                + "from non-final version %s",
                self.current_version,
            )
            raise ValueError(self.current_version)

        major_version = self.current_version.major + 1
        release_part = (major_version, 0, 0)
        alpha_part = 0

        next_version: Version = Version(
            epoch=self.current_version.epoch,
            release_tuple=release_part,
            preview=("a", alpha_part),
            dev=None,
            local=None,
            post=None,
        )

        return next_version


@final
@action
class PoetryLikePreMinorVersionModifier(VersionModifier):
    """"""

    name: str = "preminor"
    description: str = (
        "Prepares a new minor version - like `poetry version preminor`"
    )

    @traced_function
    def create_new_version(self) -> Version:
        """"""
        if not self.current_version.is_final:
            logger.error(
                "Cannot create a new minor pre-release "
                + "from non-final version %s",
                self.current_version,
            )
            raise ValueError(self.current_version)

        minor_version = self.current_version.minor + 1
        release_part = (self.current_version.major, minor_version, 0)
        alpha_part = 0

        next_version: Version = Version(
            epoch=self.current_version.epoch,
            release_tuple=release_part,
            preview=("a", alpha_part),
            dev=None,
            local=None,
            post=None,
        )

        return next_version


@final
@action
class PoetryLikePrePatchVersionModifier(VersionModifier):
    """"""

    name: str = "prepatch"
    description: str = (
        "Prepares a new patch (micro) version - like `poetry version prepatch`"
    )

    @traced_function
    def create_new_version(self) -> Version:
        """"""
        if not self.current_version.is_final:
            logger.error(
                "Cannot create a new patch pre-release "
                + "from non-final version %s",
                self.current_version,
            )
            raise ValueError(self.current_version)

        micro_version = self.current_version.micro + 1
        release_part = (
            self.current_version.major,
            self.current_version.minor,
            micro_version,
        )
        alpha_part = 0

        next_version: Version = Version(
            epoch=self.current_version.epoch,
            release_tuple=release_part,
            preview=("a", alpha_part),
            dev=None,
            local=None,
            post=None,
        )

        return next_version


@final
@action
class PoetryLikePreReleaseVersionModifier(VersionModifier):
    """"""

    name: str = "prerelease"
    description: str = (
        "Prepares a new release version - like `poetry version prerelease`"
    )

    @traced_function
    def create_new_version(self) -> Version:
        """"""
        release_part = (
            self.current_version.major,
            self.current_version.minor,
            self.current_version.micro,
        )
        preview_part: Optional[
            tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], int]
        ] = None

        if self.current_version.preview is not None:
            if self.current_version.is_alpha:
                preview_part = ("a", self.current_version.preview[1] + 1)
            elif self.current_version.is_beta:
                preview_part = ("b", self.current_version.preview[1] + 1)
            elif self.current_version.is_release_candidate:
                preview_part = ("rc", self.current_version.preview[1] + 1)
        else:
            preview_part = ("a", 0)
            release_part = (
                self.current_version.major,
                self.current_version.minor,
                self.current_version.micro + 1,
            )

        next_version: Version = Version(
            epoch=self.current_version.epoch,
            release_tuple=release_part,
            preview=preview_part,
            post=None,
            dev=None,
            local=None,
        )

        return next_version
