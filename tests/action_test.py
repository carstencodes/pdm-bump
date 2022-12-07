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

import unittest
from typing import List, Tuple, Callable

from pdm_bump.action import (
    PreviewMismatchError,
    VersionModifier,
    MajorIncrementingVersionModifier,
    MinorIncrementingVersionModifier,
    MicroIncrementingVersionModifier,
    AlphaIncrementingVersionModifier,
    BetaIncrementingVersionModifier,
    ReleaseCandidateIncrementingVersionModifier,
    FinalizingVersionModifier,
    EpochIncrementingVersionModifier,
    DevelopmentVersionIncrementingVersionModifier,
    PostVersionIncrementingVersionModifier,
)
from pdm_bump.version import Version

class ActionTest(unittest.TestCase):
    CREATE_NEXT_VERSION_PARAMS: List[Tuple[str, str, str, Callable[[Version], Version]]] = [
        ("Increment major parts with removing pre-parts and no pre-parts", "1.0.0", "2.0.0", lambda v: MajorIncrementingVersionModifier(v, True)),
        ("Increment major parts with removing pre-parts and alpha pre-parts", "1.0.0a1", "2.0.0", lambda v: MajorIncrementingVersionModifier(v, True)),
        ("Increment major parts with removing pre-parts and beta pre-parts", "1.0.0b1", "2.0.0", lambda v: MajorIncrementingVersionModifier(v, True)),
        ("Increment major parts with removing pre-parts and rc pre-parts", "1.0.0rc1", "2.0.0", lambda v: MajorIncrementingVersionModifier(v, True)),
        ("Increment major parts with removing pre-parts and dev parts", "1.0.0dev1", "2.0.0", lambda v: MajorIncrementingVersionModifier(v, True)),
        ("Increment major parts with removing pre-parts and post parts", "1.0.0post1", "2.0.0", lambda v: MajorIncrementingVersionModifier(v, True)),
        ("Increment major parts with removing pre-parts and local parts", "1.0.0+local", "2.0.0", lambda v: MajorIncrementingVersionModifier(v, True)),
        ("Increment major parts without removing pre-parts and no pre-parts", "1.0.0", "2.0.0", lambda v: MajorIncrementingVersionModifier(v, False)),
        ("Increment major parts without removing pre-parts and alpha pre-parts", "1.0.0a1", "2.0.0a1", lambda v: MajorIncrementingVersionModifier(v, False)),
        ("Increment major parts without removing pre-parts and beta pre-parts", "1.0.0b1", "2.0.0b1", lambda v: MajorIncrementingVersionModifier(v, False)),
        ("Increment major parts without removing pre-parts and rc pre-parts", "1.0.0rc1", "2.0.0rc1", lambda v: MajorIncrementingVersionModifier(v, False)),
        ("Increment major parts without removing pre-parts and dev parts", "1.0.0dev1", "2.0.0dev1", lambda v: MajorIncrementingVersionModifier(v, False)),
        ("Increment major parts without removing pre-parts and post parts", "1.0.0post1", "2.0.0post1", lambda v: MajorIncrementingVersionModifier(v, False)),
        ("Increment major parts without removing pre-parts and local parts", "1.0.0+local", "2.0.0+local", lambda v: MajorIncrementingVersionModifier(v, False)),

        ("Increment minor parts with removing pre-parts and no pre-parts", "1.0.0", "1.1.0", lambda v: MinorIncrementingVersionModifier(v, True)),
        ("Increment minor parts with removing pre-parts and alpha pre-parts", "1.0.0a1", "1.1.0", lambda v: MinorIncrementingVersionModifier(v, True)),
        ("Increment minor parts with removing pre-parts and beta pre-parts", "1.0.0b1", "1.1.0", lambda v: MinorIncrementingVersionModifier(v, True)),
        ("Increment minor parts with removing pre-parts and rc pre-parts", "1.0.0rc1", "1.1.0", lambda v: MinorIncrementingVersionModifier(v, True)),
        ("Increment minor parts with removing pre-parts and dev parts", "1.0.0dev1", "1.1.0", lambda v: MinorIncrementingVersionModifier(v, True)),
        ("Increment minor parts with removing pre-parts and post parts", "1.0.0post1", "1.1.0", lambda v: MinorIncrementingVersionModifier(v, True)),
        ("Increment minor parts with removing pre-parts and local parts", "1.0.0+local", "1.1.0", lambda v: MinorIncrementingVersionModifier(v, True)),
        ("Increment minor parts without removing pre-parts and no pre-parts", "1.0.0", "1.1.0", lambda v: MinorIncrementingVersionModifier(v, False)),
        ("Increment minor parts without removing pre-parts and alpha pre-parts", "1.0.0a1", "1.1.0a1", lambda v: MinorIncrementingVersionModifier(v, False)),
        ("Increment minor parts without removing pre-parts and beta pre-parts", "1.0.0b1", "1.1.0b1", lambda v: MinorIncrementingVersionModifier(v, False)),
        ("Increment minor parts without removing pre-parts and rc pre-parts", "1.0.0rc1", "1.1.0rc1", lambda v: MinorIncrementingVersionModifier(v, False)),
        ("Increment minor parts without removing pre-parts and dev parts", "1.0.0dev1", "1.1.0dev1", lambda v: MinorIncrementingVersionModifier(v, False)),
        ("Increment minor parts without removing pre-parts and post parts", "1.0.0post1", "1.1.0post1", lambda v: MinorIncrementingVersionModifier(v, False)),
        ("Increment minor parts without removing pre-parts and local parts", "1.0.0+local", "1.1.0+local", lambda v: MinorIncrementingVersionModifier(v, False)),

        ("Increment micro parts with removing pre-parts and no pre-parts", "1.0.0", "1.0.1", lambda v: MicroIncrementingVersionModifier(v, True)),
        ("Increment micro parts with removing pre-parts and alpha pre-parts", "1.0.0a1", "1.0.1", lambda v: MicroIncrementingVersionModifier(v, True)),
        ("Increment micro parts with removing pre-parts and beta pre-parts", "1.0.0b1", "1.0.1", lambda v: MicroIncrementingVersionModifier(v, True)),
        ("Increment micro parts with removing pre-parts and rc pre-parts", "1.0.0rc1", "1.0.1", lambda v: MicroIncrementingVersionModifier(v, True)),
        ("Increment micro parts with removing pre-parts and dev parts", "1.0.0dev1", "1.0.1", lambda v: MicroIncrementingVersionModifier(v, True)),
        ("Increment micro parts with removing pre-parts and post parts", "1.0.0post1", "1.0.1", lambda v: MicroIncrementingVersionModifier(v, True)),
        ("Increment micro parts with removing pre-parts and local parts", "1.0.0+local", "1.0.1", lambda v: MicroIncrementingVersionModifier(v, True)),
        ("Increment micro parts without removing pre-parts and no pre-parts", "1.0.0", "1.0.1", lambda v: MicroIncrementingVersionModifier(v, False)),
        ("Increment micro parts without removing pre-parts and alpha pre-parts", "1.0.0a1", "1.0.1a1", lambda v: MicroIncrementingVersionModifier(v, False)),
        ("Increment micro parts without removing pre-parts and beta pre-parts", "1.0.0b1", "1.0.1b1", lambda v: MicroIncrementingVersionModifier(v, False)),
        ("Increment micro parts without removing pre-parts and rc pre-parts", "1.0.0rc1", "1.0.1rc1", lambda v: MicroIncrementingVersionModifier(v, False)),
        ("Increment micro parts without removing pre-parts and dev parts", "1.0.0dev1", "1.0.1dev1", lambda v: MicroIncrementingVersionModifier(v, False)),
        ("Increment micro parts without removing pre-parts and post parts", "1.0.0post1", "1.0.1post1", lambda v: MicroIncrementingVersionModifier(v, False)),
        ("Increment micro parts without removing pre-parts and local parts", "1.0.0+local", "1.0.1+local", lambda v: MicroIncrementingVersionModifier(v, False)),

        ("Increment alpha parts without incrementing micro and providing no pre-release part", "1.0.0", "1.0.0a1", lambda v: AlphaIncrementingVersionModifier(v, False)),
        ("Increment alpha parts without incrementing micro and providing a pre-release part", "1.0.0a1", "1.0.0a2", lambda v: AlphaIncrementingVersionModifier(v, False)),
        ("Increment alpha parts with incrementing micro and providing no pre-release part", "1.0.0", "1.0.1a1", lambda v: AlphaIncrementingVersionModifier(v, True)),
        ("Increment alpha parts with incrementing micro and providing a pre-release part", "1.0.0a1", "1.0.0a2", lambda v: AlphaIncrementingVersionModifier(v, True)),

        ("Increment beta parts without incrementing micro and providing no pre-release part", "1.0.0", "1.0.0b1", lambda v: BetaIncrementingVersionModifier(v, False)),
        ("Increment beta parts without incrementing micro and providing a pre-release part", "1.0.0b1", "1.0.0b2", lambda v: BetaIncrementingVersionModifier(v, False)),
        ("Increment beta parts without incrementing micro and providing a pre-release part", "1.0.0a2", "1.0.0b1", lambda v: BetaIncrementingVersionModifier(v, False)),
        ("Increment beta parts with incrementing micro and providing no pre-release part", "1.0.0", "1.0.1b1", lambda v: BetaIncrementingVersionModifier(v, True)),
        ("Increment beta parts with incrementing micro and providing a pre-release part", "1.0.0b1", "1.0.0b2", lambda v: BetaIncrementingVersionModifier(v, True)),
        ("Increment beta parts with incrementing micro and providing no pre-release part", "1.0.0a2", "1.0.0b1", lambda v: BetaIncrementingVersionModifier(v, True)),

        ("Increment rc parts without incrementing micro and providing no pre-release part", "1.0.0", "1.0.0rc1", lambda v: ReleaseCandidateIncrementingVersionModifier(v, False)),
        ("Increment rc parts without incrementing micro and providing a pre-release part", "1.0.0rc1", "1.0.0rc2", lambda v: ReleaseCandidateIncrementingVersionModifier(v, False)),
        ("Increment rc parts without incrementing micro and providing no pre-release part", "1.0.0a2", "1.0.0rc1", lambda v: ReleaseCandidateIncrementingVersionModifier(v, False)),
        ("Increment rc parts without incrementing micro and providing no pre-release part", "1.0.0b2", "1.0.0rc1", lambda v: ReleaseCandidateIncrementingVersionModifier(v, False)),
        ("Increment rc parts with incrementing micro and providing no pre-release part", "1.0.0", "1.0.1rc1", lambda v: ReleaseCandidateIncrementingVersionModifier(v, True)),
        ("Increment rc parts with incrementing micro and providing a pre-release part", "1.0.0rc1", "1.0.0rc2", lambda v: ReleaseCandidateIncrementingVersionModifier(v, True)),
        ("Increment rc parts with incrementing micro and providing no pre-release part", "1.0.0a2", "1.0.0rc1", lambda v: ReleaseCandidateIncrementingVersionModifier(v, True)),
        ("Increment rc parts with incrementing micro and providing a pre-release part", "1.0.0b2", "1.0.0rc1", lambda v: ReleaseCandidateIncrementingVersionModifier(v, True)),

        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, False, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3a4", "1!1.2.3a4", lambda v: EpochIncrementingVersionModifier(v, False, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3b4", "1!1.2.3b4", lambda v: EpochIncrementingVersionModifier(v, False, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3rc4", "1!1.2.3rc4", lambda v: EpochIncrementingVersionModifier(v, False, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3dev5", "1!1.2.3dev5", lambda v: EpochIncrementingVersionModifier(v, False, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3post6", "1!1.2.3post6", lambda v: EpochIncrementingVersionModifier(v, False, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3+local7", "1!1.2.3+local7", lambda v: EpochIncrementingVersionModifier(v, False, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3b4post3dev6+local7", "1!1.2.3b4post3dev6+local7", lambda v: EpochIncrementingVersionModifier(v, False, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, True, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3a4", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, True, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3b4", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, True, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3rc4", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, True, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3dev5", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, True, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3post6", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, True, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3+local7", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, True, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3b4post3dev6+local7", "1!1.2.3", lambda v: EpochIncrementingVersionModifier(v, True, False)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, False, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3a4", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, False, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3b4", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, False, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3rc4", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, False, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3dev5", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, False, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3post6", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, False, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3+local7", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, False, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3b4post3dev6+local7", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, False, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, True, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3a4", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, True, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3b4", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, True, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3rc4", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, True, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3dev5", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, True, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3post6", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, True, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3+local7", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, True, True)),
        ("Increment epoch without an epoch and without resetting version or removing any version part", "1.2.3b4post3dev6+local7", "1!1.0.0", lambda v: EpochIncrementingVersionModifier(v, True, True)),

        ("Remove non-final parts", "1.2.3", "1.2.3", lambda v: FinalizingVersionModifier(v)),
        ("Remove non-final parts", "1.2.3a1", "1.2.3", lambda v: FinalizingVersionModifier(v)),
        ("Remove non-final parts", "1.2.3b2", "1.2.3", lambda v: FinalizingVersionModifier(v)),
        ("Remove non-final parts", "1.2.3rc3", "1.2.3", lambda v: FinalizingVersionModifier(v)),
        ("Remove non-final parts", "1.2.3-dev1", "1.2.3", lambda v: FinalizingVersionModifier(v)),
        ("Remove non-final parts", "1.2.3-post4", "1.2.3", lambda v: FinalizingVersionModifier(v)),
        ("Remove non-final parts", "1.2.3+local8", "1.2.3", lambda v: FinalizingVersionModifier(v)),
        ("Remove non-final parts", "1.2.3-b4-post6-dev8+local9", "1.2.3", lambda v: FinalizingVersionModifier(v)),
    ]  # TODO Test Dev and Post Incrementing modifier
    CREATE_NEXT_VERSION_ERROR_PARAMS: List[Tuple[str, str, Callable[[Version], VersionModifier]]] = [
        ("Increment alpha version if beta is present", "1.2.3b1", lambda v: AlphaIncrementingVersionModifier(v, False)),
        ("Increment alpha version if beta is present", "1.2.3b1", lambda v: AlphaIncrementingVersionModifier(v, True)),
        ("Increment alpha version if rc is present", "1.2.3rc1", lambda v: AlphaIncrementingVersionModifier(v, False)),
        ("Increment alpha version if rc is present", "1.2.3rc1", lambda v: AlphaIncrementingVersionModifier(v, True)),
        ("Increment beta version if rc is present", "1.2.3rc1", lambda v: BetaIncrementingVersionModifier(v, False)),
        ("Increment beta version if rc is present", "1.2.3rc1", lambda v: BetaIncrementingVersionModifier(v, True)),
    ]

    def test_create_next_version_success(self) -> None:
        for message, current_version_str, expected_version_str, factory in self.CREATE_NEXT_VERSION_PARAMS:
            with self.subTest(message, current=current_version_str, expected=expected_version_str):
                current: Version = Version.from_string(current_version_str)
                expected: Version = Version.from_string(expected_version_str)

                command: VersionModifier = factory(current)

                modified: Version = command.create_new_version()
                self.assertEqual(modified, expected)

    def test_create_next_version_fail(self) -> None:
        for message, current_version_str, factory in self.CREATE_NEXT_VERSION_ERROR_PARAMS:
            with self.subTest(message, current=current_version_str):
                current: Version = Version.from_string(current_version_str)

                command: VersionModifier = factory(current)

                self.assertRaises(PreviewMismatchError, command.create_new_version)
