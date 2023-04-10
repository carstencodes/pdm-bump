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

from abc import abstractmethod
from argparse import ArgumentParser
from typing import Literal, cast, final

from ..core.logging import logger, traced_function
from ..core.version import NonNegativeInteger, Pep440VersionFormatter, Version
from .base import VersionModifier, VersionPersister, action

_formatter = Pep440VersionFormatter()


class PreviewMismatchError(Exception):
    pass


# Justification fulfills a protocol
class _DummyPersister:  # pylint: disable=R0903
    def save_version(self, version: Version) -> None:
        # This must not be implemented as it is only a dummy.
        pass


class _PreReleaseIncrementingVersionModified(VersionModifier):
    def __init__(
        self,
        version: Version,
        persister: VersionPersister,
        increment_micro: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(version, persister, **kwargs)
        self.__increment_micro = increment_micro

    @classmethod
    def _update_command(cls, sub_parser: ArgumentParser) -> None:
        sub_parser.add_argument(
            "--micro",
            action="store_true",
            dest="increment_micro",
            help="When setting pre-release, specifies "
            + "whether micro version shall "
            + "be incremented as well",
        )

        VersionModifier._update_command(sub_parser)

    @traced_function
    def create_new_version(self) -> Version:
        letter: Literal["a", "b", "c", "alpha", "beta", "rc"]
        name: str
        letter, name = self.pre_release_part
        pre: tuple[
            Literal["a", "b", "c", "alpha", "beta", "rc"], NonNegativeInteger
        ] = (letter, 1)

        logger.debug(
            "Incrementing %s part of current version %s",
            name,
            _formatter.format(self.current_version),
        )

        if self.current_version.preview is not None:
            if not self._is_valid_preview_version():
                raise PreviewMismatchError(
                    f"{_formatter.format(self.current_version)} "
                    # Weird behavior of sonarlint, pylint and flake8
                    # Variable is declared as unused, if used only in
                    # formatted string
                    + "is not an "
                    + name
                    + " version."
                )
            pre = cast(
                tuple[
                    Literal["a", "b", "c", "alpha", "beta", "rc"],
                    NonNegativeInteger,
                ],
                self.current_version.preview,
            )
            number = pre[1] + 1 if letter == pre[0] else 1

            pre = (letter, number)

        result: Version = Version(
            self.current_version.epoch,
            self._get_next_release(),
            pre,
            None,
            None,
            None,
        )

        self._report_new_version(result)

        return result

    @property
    @abstractmethod
    def pre_release_part(
        self,
    ) -> tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        raise NotImplementedError()

    @abstractmethod
    def _is_valid_preview_version(self) -> bool:
        raise NotImplementedError()

    def _get_next_release(self) -> tuple[NonNegativeInteger, ...]:
        micro = self.current_version.micro
        if self.__increment_micro and self.current_version.preview is None:
            micro = micro + 1

        ret: list[NonNegativeInteger] = []
        for val in self.current_version.release:
            ret.append(val)

        while len(ret) < 3:
            ret.append(0)

        ret[2] = micro

        return tuple(ret)


@final
@action
class PreReleaseIncrementingVersionModifier(VersionModifier):
    name: str = "pre-release"
    description: str = (
        "Increment a pre-release part (alpha, beta, release-candidate)"
    )

    def __init__(
        self,
        version: Version,
        persister: VersionPersister,
        pre_release_part: str,
        increment_micro: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(version, persister, **kwargs)
        self.__sub_modifier: VersionModifier
        if pre_release_part in (AlphaIncrementingVersionModifier.name,):
            self.__sub_modifier = AlphaIncrementingVersionModifier(
                version, _DummyPersister(), increment_micro
            )
        elif pre_release_part in (BetaIncrementingVersionModifier.name,):
            self.__sub_modifier = BetaIncrementingVersionModifier(
                version, _DummyPersister(), increment_micro
            )
        elif (
            pre_release_part
            in (ReleaseCandidateIncrementingVersionModifier.name,)
            or pre_release_part
            in ReleaseCandidateIncrementingVersionModifier.aliases
        ):
            self.__sub_modifier = ReleaseCandidateIncrementingVersionModifier(
                version, _DummyPersister(), increment_micro
            )
        else:
            raise ValueError(
                f"{pre_release_part} is not a valid pre-release part"
            )

    @traced_function
    def create_new_version(self) -> Version:
        return self.__sub_modifier.create_new_version()

    @classmethod
    def _update_command(cls, sub_parser: ArgumentParser) -> None:
        valid_values = []
        valid_values.append(AlphaIncrementingVersionModifier.name)
        valid_values.append(BetaIncrementingVersionModifier.name)
        valid_values.append(ReleaseCandidateIncrementingVersionModifier.name)
        valid_values.extend(
            ReleaseCandidateIncrementingVersionModifier.aliases
        )

        sub_parser.add_argument(
            "--pre",
            action="store",
            type=str,
            default=None,
            choices=valid_values,
            dest="pre_release_part",
            help="Sets a pre-release on the current version."
            + " If a pre-release is set, it can be removed "
            + "using the 'final' option. A new pre-release "
            + "must be greater than the current version."
            + " See PEP440 for details.",
        )

        VersionModifier._update_command(sub_parser)
        # Justification: Class is a mixin
        # pylint: disable=W0212
        _PreReleaseIncrementingVersionModified._update_command(sub_parser)


@final
class AlphaIncrementingVersionModifier(_PreReleaseIncrementingVersionModified):
    name: str = "alpha"
    description: str = "Increment the alpha pre-release version part"

    @property
    def pre_release_part(
        self,
    ) -> tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        return ("a", "alpha")

    def _is_valid_preview_version(self) -> bool:
        return self.current_version.is_alpha


@final
class BetaIncrementingVersionModifier(_PreReleaseIncrementingVersionModified):
    name: str = "beta"
    description: str = "Increment the beta pre-release version part"

    @property
    def pre_release_part(
        self,
    ) -> tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        return ("b", "alpha or beta")

    def _is_valid_preview_version(self) -> bool:
        return self.current_version.is_alpha or self.current_version.is_beta


@final
class ReleaseCandidateIncrementingVersionModifier(
    _PreReleaseIncrementingVersionModified
):
    name: str = "rc"
    description: str = (
        "Increment the release-candidate pre-release version part"
    )
    aliases: tuple[str] = ("c",)

    @property
    def pre_release_part(
        self,
    ) -> tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        return ("rc", "pre-release")

    def _is_valid_preview_version(self) -> bool:
        return (
            self.current_version.is_alpha
            or self.current_version.is_beta
            or self.current_version.is_release_candidate
        )
