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

from typing import Callable

from pdm_bump.actions import (
    VersionModifier,
)
from pdm_bump.actions.increment import (
    MajorIncrementingVersionModifier,
    MinorIncrementingVersionModifier,
    MicroIncrementingVersionModifier,
    FinalizingVersionModifier,
    EpochIncrementingVersionModifier,
    DevelopmentVersionIncrementingVersionModifier,
    PostVersionIncrementingVersionModifier,
)
from pdm_bump.actions.preview import (
    PreviewMismatchError,
    AlphaIncrementingVersionModifier,
    BetaIncrementingVersionModifier,
    ReleaseCandidateIncrementingVersionModifier,
)
from pdm_bump.actions.poetry_like import (
    PoetryLikePreReleaseVersionModifier,
    PoetryLikePreMajorVersionModifier,
    PoetryLikePreMinorVersionModifier,
    PoetryLikePrePatchVersionModifier,
)

from pdm_bump.core.version import Version

import pytest

parametrize = pytest.mark.parametrize
assert_raises = pytest.raises


class _UnitTestPersister:
    def save_version(self, version: Version) -> None:
        # Just for testing
        pass

_unit_test_persister = _UnitTestPersister()

_CREATE_NEXT_VERSION_PARAMS: list[
    tuple[str, str, str, Callable[[Version], Version]]
] = [
    (
        "Increment major parts with removing pre-parts and no pre-parts",
        "1.0.0",
        "2.0.0",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment major parts with removing pre-parts and alpha pre-parts",
        "1.0.0a1",
        "2.0.0",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment major parts with removing pre-parts and beta pre-parts",
        "1.0.0b1",
        "2.0.0",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment major parts with removing pre-parts and rc pre-parts",
        "1.0.0rc1",
        "2.0.0",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment major parts with removing pre-parts and dev parts",
        "1.0.0dev1",
        "2.0.0",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment major parts with removing pre-parts and post parts",
        "1.0.0post1",
        "2.0.0",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment major parts with removing pre-parts and local parts",
        "1.0.0+local",
        "2.0.0",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment major parts without removing pre-parts and no pre-parts",
        "1.0.0",
        "2.0.0",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment major parts without removing pre-parts and alpha pre-parts",
        "1.0.0a1",
        "2.0.0a1",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment major parts without removing pre-parts and beta pre-parts",
        "1.0.0b1",
        "2.0.0b1",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment major parts without removing pre-parts and rc pre-parts",
        "1.0.0rc1",
        "2.0.0rc1",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment major parts without removing pre-parts and dev parts",
        "1.0.0dev1",
        "2.0.0dev1",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment major parts without removing pre-parts and post parts",
        "1.0.0post1",
        "2.0.0post1",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment major parts without removing pre-parts and local parts",
        "1.0.0+local",
        "2.0.0+local",
        lambda v: MajorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment minor parts with removing pre-parts and no pre-parts",
        "1.0.0",
        "1.1.0",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment minor parts with removing pre-parts and alpha pre-parts",
        "1.0.0a1",
        "1.1.0",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment minor parts with removing pre-parts and beta pre-parts",
        "1.0.0b1",
        "1.1.0",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment minor parts with removing pre-parts and rc pre-parts",
        "1.0.0rc1",
        "1.1.0",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment minor parts with removing pre-parts and dev parts",
        "1.0.0dev1",
        "1.1.0",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment minor parts with removing pre-parts and post parts",
        "1.0.0post1",
        "1.1.0",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment minor parts with removing pre-parts and local parts",
        "1.0.0+local",
        "1.1.0",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment minor parts without removing pre-parts and no pre-parts",
        "1.0.0",
        "1.1.0",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment minor parts without removing pre-parts and alpha pre-parts",
        "1.0.0a1",
        "1.1.0a1",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment minor parVersionModifierts without removing pre-parts and beta pre-parts",
        "1.0.0b1",
        "1.1.0b1",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment minor parts without removing pre-parts and rc pre-parts",
        "1.0.0rc1",
        "1.1.0rc1",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment minor parts without removing pre-parts and dev parts",
        "1.0.0dev1",
        "1.1.0dev1",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment minor parts without removing pre-parts and post parts",
        "1.0.0post1",
        "1.1.0post1",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment minor parts without removing pre-parts and local parts",
        "1.0.0+local",
        "1.1.0+local",
        lambda v: MinorIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment micro parts with removing pre-parts and no pre-parts",
        "1.0.0",
        "1.0.1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment micro parts with removing pre-parts and alpha pre-parts",
        "1.0.0a1",
        "1.0.1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment micro parts with removing pre-parts and beta pre-parts",
        "1.0.0b1",
        "1.0.1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment micro parts with removing pre-parts and rc pre-parts",
        "1.0.0rc1",
        "1.0.1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment micro parts with removing pre-parts and dev parts",
        "1.0.0dev1",
        "1.0.1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment micro parts with removing pre-parts and post parts",
        "1.0.0post1",
        "1.0.1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment micro parts with removing pre-parts and local parts",
        "1.0.0+local",
        "1.0.1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment micro parts without removing pre-parts and no pre-parts",
        "1.0.0",
        "1.0.1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment micro parts without removing pre-parts and alpha pre-parts",
        "1.0.0a1",
        "1.0.1a1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment micro parts without removing pre-parts and beta pre-parts",
        "1.0.0b1",
        "1.0.1b1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment micro parts without removing pre-parts and rc pre-parts",
        "1.0.0rc1",
        "1.0.1rc1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment micro parts without removing pre-parts and dev parts",
        "1.0.0dev1",
        "1.0.1dev1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment micro parts without removing pre-parts and post parts",
        "1.0.0post1",
        "1.0.1post1",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment micro parts without removing pre-parts and local parts",
        "1.0.0+local",
        "1.0.1+local",
        lambda v: MicroIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment alpha parts without incrementing micro and providing no pre-release part",
        "1.0.0",
        "1.0.0a1",
        lambda v: AlphaIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment alpha parts without incrementing micro and providing a pre-release part",
        "1.0.0a1",
        "1.0.0a2",
        lambda v: AlphaIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment alpha parts with incrementing micro and providing no pre-release part",
        "1.0.0",
        "1.0.1a1",
        lambda v: AlphaIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment alpha parts with incrementing micro and providing a pre-release part",
        "1.0.0a1",
        "1.0.0a2",
        lambda v: AlphaIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment beta parts without incrementing micro and providing no pre-release part",
        "1.0.0",
        "1.0.0b1",
        lambda v: BetaIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment beta parts without incrementing micro and providing a pre-release part",
        "1.0.0b1",
        "1.0.0b2",
        lambda v: BetaIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment beta parts without incrementing micro and providing a pre-release part",
        "1.0.0a2",
        "1.0.0b1",
        lambda v: BetaIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment beta parts with incrementing micro and providing no pre-release part",
        "1.0.0",
        "1.0.1b1",
        lambda v: BetaIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment beta parts with incrementing micro and providing a pre-release part",
        "1.0.0b1",
        "1.0.0b2",
        lambda v: BetaIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment beta parts with incrementing micro and providing no pre-release part",
        "1.0.0a2",
        "1.0.0b1",
        lambda v: BetaIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment rc parts without incrementing micro and providing no pre-release part",
        "1.0.0",
        "1.0.0rc1",
        lambda v: ReleaseCandidateIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment rc parts without incrementing micro and providing a pre-release part",
        "1.0.0rc1",
        "1.0.0rc2",
        lambda v: ReleaseCandidateIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment rc parts without incrementing micro and providing no pre-release part",
        "1.0.0a2",
        "1.0.0rc1",
        lambda v: ReleaseCandidateIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment rc parts without incrementing micro and providing no pre-release part",
        "1.0.0b2",
        "1.0.0rc1",
        lambda v: ReleaseCandidateIncrementingVersionModifier(v, _unit_test_persister, False),
    ),
    (
        "Increment rc parts with incrementing micro and providing no pre-release part",
        "1.0.0",
        "1.0.1rc1",
        lambda v: ReleaseCandidateIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment rc parts with incrementing micro and providing a pre-release part",
        "1.0.0rc1",
        "1.0.0rc2",
        lambda v: ReleaseCandidateIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment rc parts with incrementing micro and providing no pre-release part",
        "1.0.0a2",
        "1.0.0rc1",
        lambda v: ReleaseCandidateIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment rc parts with incrementing micro and providing a pre-release part",
        "1.0.0b2",
        "1.0.0rc1",
        lambda v: ReleaseCandidateIncrementingVersionModifier(v, _unit_test_persister, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3a4",
        "1!1.2.3a4",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3b4",
        "1!1.2.3b4",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3rc4",
        "1!1.2.3rc4",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3dev5",
        "1!1.2.3dev5",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3post6",
        "1!1.2.3post6",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3+local7",
        "1!1.2.3+local7",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3b4post3dev6+local7",
        "1!1.2.3b4post3dev6+local7",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3a4",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3b4",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3rc4",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3dev5",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3post6",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3+local7",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3b4post3dev6+local7",
        "1!1.2.3",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, False),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3a4",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3b4",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3rc4",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3dev5",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3post6",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3+local7",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3b4post3dev6+local7",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, False, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3a4",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3b4",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3rc4",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3dev5",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3post6",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3+local7",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, True),
    ),
    (
        "Increment epoch without an epoch and without resetting version or removing any version part",
        "1.2.3b4post3dev6+local7",
        "1!1.0.0",
        lambda v: EpochIncrementingVersionModifier(v, _unit_test_persister, True, True),
    ),
    (
        "Remove non-final parts",
        "1.2.3",
        "1.2.3",
        lambda v: FinalizingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Remove non-final parts",
        "1.2.3a1",
        "1.2.3",
        lambda v: FinalizingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Remove non-final parts",
        "1.2.3b2",
        "1.2.3",
        lambda v: FinalizingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Remove non-final parts",
        "1.2.3rc3",
        "1.2.3",
        lambda v: FinalizingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Remove non-final parts",
        "1.2.3-dev1",
        "1.2.3",
        lambda v: FinalizingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Remove non-final parts",
        "1.2.3-post4",
        "1.2.3",
        lambda v: FinalizingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Remove non-final parts",
        "1.2.3+local8",
        "1.2.3",
        lambda v: FinalizingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Remove non-final parts",
        "1.2.3-b4-post6-dev8+local9",
        "1.2.3",
        lambda v: FinalizingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing development version",
        "1.2.3-dev1",
        "1.2.3-dev2",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing development version",
        "1.2.0a1",
        "1.2.0a2-dev1",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing development version",
        "1.2.0a1-dev2",
        "1.2.0a1-dev3",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing development version",
        "1.2.0b2",
        "1.2.0b3-dev1",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing development version",
        "1.2.0b2-dev1",
        "1.2.0b2-dev2",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing development version",
        "1.2.0rc1",
        "1.2.0rc2-dev1",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing development version",
        "1.2.0rc1-dev1",
        "1.2.0rc1-dev2",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of non-existing development version",
        "1.2.3",
        "1.2.4-dev1",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing post and non-existing development version",
        "1.2.3-post6",
        "1.2.4-dev1",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing post and existing development version",
        "1.2.3-post6-dev1",
        "1.2.3-post6-dev2",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing post and existing development version with local revision",
        "1.2.3-post6-dev1+local9",
        "1.2.3-post6-dev2+local9",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing development version with local revision",
        "1.2.3-dev1+local9",
        "1.2.3-dev2+local9",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment development part of existing post and non-existing development version with local revision",
        "1.2.3-post1+local9",
        "1.2.4-dev1+local9",
        lambda v: DevelopmentVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment post part of a non-existing post part",
        "1.2.3",
        "1.2.3-post1",
        lambda v: PostVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment post part of an existing post part",
        "1.2.3-post1",
        "1.2.3-post2",
        lambda v: PostVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment post part of a non-existing post part, but dev exists",
        "1.2.3-dev3",
        "1.2.3-post1",
        lambda v: PostVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment post part of an existing post part, but dev exists",
        "1.2.3-post1-dev3",
        "1.2.3-post2",
        lambda v: PostVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment post part of a non-existing post part, but local exists",
        "1.2.3+local1",
        "1.2.3-post1+local1",
        lambda v: PostVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Increment post part of a non-existing post part, but dev and local exist",
        "1.2.3-dev1+local1",
        "1.2.3-post1+local1",
        lambda v: PostVersionIncrementingVersionModifier(v, _unit_test_persister),
    ),
    (
        "Run premajor from poetry version commands (demo from https://python-poetry.org/docs/cli/#version)",
        "1.0.2",
        "2.0.0a0",
        lambda v: PoetryLikePreMajorVersionModifier(v, _unit_test_persister),
    ),
    (
        "Run preminor from poetry version commands (demo from https://python-poetry.org/docs/cli/#version)",
        "1.0.2",
        "1.1.0a0",
        lambda v: PoetryLikePreMinorVersionModifier(v, _unit_test_persister),
    ),
    (
        "Run prepatch from poetry version commands (demo from https://python-poetry.org/docs/cli/#version)",
        "1.0.2",
        "1.0.3a0",
        lambda v: PoetryLikePrePatchVersionModifier(v, _unit_test_persister),
    ),
    (
        "Run prerelease from poetry version commands (demo from https://python-poetry.org/docs/cli/#version)",
        "1.0.2",
        "1.0.3a0",
        lambda v: PoetryLikePreReleaseVersionModifier(v, _unit_test_persister),
    ),
    (
        "Run prerelease from poetry version commands (demo from https://python-poetry.org/docs/cli/#version)",
        "1.0.3a0",
        "1.0.3a1",
        lambda v: PoetryLikePreReleaseVersionModifier(v, _unit_test_persister),
    ),
    (
        "Run prerelease from poetry version commands (demo from https://python-poetry.org/docs/cli/#version)",
        "1.0.3b0",
        "1.0.3b1",
        lambda v: PoetryLikePreReleaseVersionModifier(v, _unit_test_persister),
    ),
    (
        "Run prerelease from poetry version commands (demo from https://python-poetry.org/docs/cli/#version)",
        "1.0.3rc0",
        "1.0.3rc1",
        lambda v: PoetryLikePreReleaseVersionModifier(v, _unit_test_persister),
    ),
]
_CREATE_NEXT_VERSION_ERROR_PARAMS: list[
    tuple[str, str, Callable[[Version], VersionModifier]]
] = [
    (
        "Increment alpha version if beta is present",
        "1.2.3b1",
        lambda v: AlphaIncrementingVersionModifier(v, _unit_test_persister, False),
        PreviewMismatchError,
    ),
    (
        "Increment alpha version if beta is present",
        "1.2.3b1",
        lambda v: AlphaIncrementingVersionModifier(v, _unit_test_persister, True),
        PreviewMismatchError,
    ),
    (
        "Increment alpha version if rc is present",
        "1.2.3rc1",
        lambda v: AlphaIncrementingVersionModifier(v, _unit_test_persister, False),
        PreviewMismatchError,
    ),
    (
        "Increment alpha version if rc is present",
        "1.2.3rc1",
        lambda v: AlphaIncrementingVersionModifier(v, _unit_test_persister, True),
        PreviewMismatchError,
    ),
    (
        "Increment beta version if rc is present",
        "1.2.3rc1",
        lambda v: BetaIncrementingVersionModifier(v, _unit_test_persister, False),
        PreviewMismatchError,
    ),
    (
        "Increment beta version if rc is present",
        "1.2.3rc1",
        lambda v: BetaIncrementingVersionModifier(v, _unit_test_persister, True),
        PreviewMismatchError,
    ),
    (
        "Pre-Major if version is dev version",
        "1.2.3-dev1",
        lambda v: PoetryLikePreMajorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Major if version is local version",
        "1.2.3+local17",
        lambda v: PoetryLikePreMajorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Major if version is post version",
        "1.2.3-post12",
        lambda v: PoetryLikePreMajorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Major if version is alpha version",
        "1.2.3a23",
        lambda v: PoetryLikePreMajorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Major if version is beta version",
        "1.2.3b23",
        lambda v: PoetryLikePreMajorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Major if version is release candidate",
        "1.2.3rc23",
        lambda v: PoetryLikePreMajorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Minor if version is dev version",
        "1.2.3-dev1",
        lambda v: PoetryLikePreMinorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Minor if version is local version",
        "1.2.3+local17",
        lambda v: PoetryLikePreMinorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Minor if version is post version",
        "1.2.3-post12",
        lambda v: PoetryLikePreMinorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Minor if version is alpha version",
        "1.2.3a23",
        lambda v: PoetryLikePreMinorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Minor if version is beta version",
        "1.2.3b23",
        lambda v: PoetryLikePreMinorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Minor if version is release candidate",
        "1.2.3rc23",
        lambda v: PoetryLikePreMinorVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Patch if version is dev version",
        "1.2.3-dev1",
        lambda v: PoetryLikePrePatchVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Patch if version is local version",
        "1.2.3+local17",
        lambda v: PoetryLikePrePatchVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Patch if version is post version",
        "1.2.3-post12",
        lambda v: PoetryLikePrePatchVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Patch if version is alpha version",
        "1.2.3a23",
        lambda v: PoetryLikePrePatchVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Patch if version is beta version",
        "1.2.3b23",
        lambda v: PoetryLikePrePatchVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
    (
        "Pre-Patch if version is release candidate",
        "1.2.3rc23",
        lambda v: PoetryLikePrePatchVersionModifier(v, _unit_test_persister),
        ValueError,
    ),
]

@parametrize(",".join(["message", "current_version_str", "expected_version_str", "factory"]), _CREATE_NEXT_VERSION_PARAMS)
def test_create_next_version_success(message, current_version_str, expected_version_str, factory) -> None:
    current: Version = Version.from_string(current_version_str)
    expected: Version = Version.from_string(expected_version_str)

    command: VersionModifier = factory(current)

    modified: Version = command.create_new_version()
    assert modified == expected

@parametrize(",".join(["message", "current_version_str", "factory", "exception_type"]), _CREATE_NEXT_VERSION_ERROR_PARAMS)
def test_create_next_version_fail(message, current_version_str, factory, exception_type) -> None:
    current: Version = Version.from_string(current_version_str)

    command: VersionModifier = factory(current)

    with assert_raises(exception_type):
        _ = command.create_new_version()
