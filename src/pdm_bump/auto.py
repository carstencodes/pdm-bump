#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#

from typing import Final, FrozenSet

from .action import ActionCollection, VersionModifier
from .vcs import VcsProvider
from .version import Version


class _VcsSupportedVersionModifier(VersionModifier):
    def __init__(self, version: Version, vcs_provider: VcsProvider) -> None:
        super().__init__(version)
        self._vcs_provider = vcs_provider

    def create_new_version(self) -> Version:
        self._run_action()

        return self._suggest_new_version()

    def _run_action(self) -> None:
        # Empty implementation used in sub-classes
        pass

    def _suggest_new_version(self) -> Version:
        return self.current_version


class CreateTagFromVersion(_VcsSupportedVersionModifier):
    def _run_action(self) -> None:
        self._vcs_provider.create_tag_from_version(self.current_version)


COMMAND_NAME_CREATE_TAG: Final[str] = "tag"

COMMAND_NAMES: Final[FrozenSet[str]] = frozenset(
    [
        COMMAND_NAME_CREATE_TAG,
    ]
)


def apply_vcs_based_actions(
    actions: ActionCollection,
    vcs_provider: VcsProvider
) -> None:
    actions[COMMAND_NAME_CREATE_TAG] = lambda v: CreateTagFromVersion(
        v, vcs_provider)
