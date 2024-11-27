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
from typing import TYPE_CHECKING, Literal, Optional, cast, final

from pdm_pfsc.logging import logger, traced_function

from ..core.version import NonNegativeInteger, Pep440VersionFormatter, Version
from .base import VersionModifier, VersionPersister, action

if TYPE_CHECKING:
    from argparse import ArgumentParser

_formatter = Pep440VersionFormatter()


class PreviewMismatchError(Exception):
    """"""

    # Justification: Zen of Python: Explicit is better than implicit
    pass  # pylint: disable=W0107


# Justification fulfills a protocol
class _DummyPersister:  # pylint: disable=R0903
    """"""

    def save_version(self, version: "Version") -> None:
        """

        Parameters
        ----------
        version: Version :


        Returns
        -------

        """
        # This must not be implemented as it is only a dummy.
        raise NotImplementedError()


class _PreReleaseIncrementingVersionModifier(VersionModifier):
    """"""

    def __init__(
        self,
        version: "Version",
        persister: "VersionPersister",
        increment_micro: bool,
        **kwargs,
    ) -> None:
        super().__init__(version, persister, **kwargs)
        self.__increment_micro = increment_micro

    @classmethod
    def _update_command(cls, sub_parser: "ArgumentParser") -> None:
        """

        Parameters
        ----------
        sub_parser: ArgumentParser :


        Returns
        -------

        """
        grp = sub_parser.add_mutually_exclusive_group(required=False)
        grp.add_argument(
            "--micro",
            action="store_true",
            dest="increment_micro",
            help="If set, the micro version will be incremented. This is the "
            "default, if you are not incrementing a version that is a pre-"
            "release yet. Cannot be mixed with --no-micro.",
        )

        grp.add_argument(
            "--no-micro",
            action="store_true",
            dest="no_increment_micro",
            help="If set, do not increment the micro version, even it would"
            "apply as it is no pre-release version yet. Cannot be mixed "
            "with --micro.",
        )

        VersionModifier._update_command(sub_parser)

    @traced_function
    def create_new_version(self) -> "Version":
        """"""
        letter: 'Literal["a", "b", "c", "alpha", "beta", "rc"]'
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
                "tuple["
                "Literal['a', 'b', 'c', "
                "'alpha', 'beta', 'rc'],"
                "NonNegativeInteger,"
                "]",
                self.current_version.preview,
            )
            number = pre[1] + 1 if letter == pre[0] else 1

            pre = (letter, number)

        result: "Version" = Version(
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
        """"""
        raise NotImplementedError()

    @abstractmethod
    def _is_valid_preview_version(self) -> bool:
        """"""
        raise NotImplementedError()

    def _get_next_release(self) -> "tuple[NonNegativeInteger, ...]":
        """"""
        micro = self.current_version.micro
        if self.__increment_micro and self.current_version.preview is None:
            micro = micro + 1

        ret: "list[NonNegativeInteger]" = []
        for val in self.current_version.release:
            ret.append(val)

        while len(ret) < 3:
            ret.append(0)

        ret[2] = micro

        return tuple(ret)


@final
@action
class PreReleaseIncrementingVersionModifier(VersionModifier):
    """"""

    name: str = "pre-release"
    description: str = (
        "Increment a pre-release part (alpha, beta, release-candidate)"
    )

    # Justification: self and kwargs should not count, both boolean
    #                arguments must be applied due to arg-parse implementation
    def __init__(  # pylint: disable=R0913,R0917
        self,
        version: "Version",
        persister: "VersionPersister",
        pre_release_part: "Optional[str]",
        increment_micro: bool,
        no_increment_micro: bool,
        **kwargs,
    ) -> None:
        super().__init__(version, persister, **kwargs)

        do_increment_micro: bool = (
            increment_micro
            or not no_increment_micro
            or not version.is_pre_release
        )

        if pre_release_part is None:
            pre_release_part = (
                version.preview[0]
                if version.preview is not None
                else AlphaIncrementingVersionModifier.name
            )

        self.__sub_modifier: VersionModifier
        if (
            pre_release_part in (AlphaIncrementingVersionModifier.name,)
            or pre_release_part in AlphaIncrementingVersionModifier.aliases
        ):
            self.__sub_modifier = AlphaIncrementingVersionModifier(
                version, _DummyPersister(), do_increment_micro
            )
        elif (
            pre_release_part in (BetaIncrementingVersionModifier.name,)
            or pre_release_part in BetaIncrementingVersionModifier.aliases
        ):
            self.__sub_modifier = BetaIncrementingVersionModifier(
                version, _DummyPersister(), do_increment_micro
            )
        elif (
            pre_release_part
            in (ReleaseCandidateIncrementingVersionModifier.name,)
            or pre_release_part
            in ReleaseCandidateIncrementingVersionModifier.aliases
        ):
            self.__sub_modifier = ReleaseCandidateIncrementingVersionModifier(
                version, _DummyPersister(), do_increment_micro
            )
        else:
            raise ValueError(
                f"{pre_release_part} is not a valid pre-release part"
            )

    @traced_function
    def create_new_version(self) -> "Version":
        """"""
        return self.__sub_modifier.create_new_version()

    @classmethod
    def _update_command(cls, sub_parser: "ArgumentParser") -> None:
        """

        Parameters
        ----------
        sub_parser: ArgumentParser :


        Returns
        -------

        """
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

        # Justification: Invoke overridden method.
        # pylint: disable=W0212
        _PreReleaseIncrementingVersionModifier._update_command(sub_parser)


@final
class AlphaIncrementingVersionModifier(_PreReleaseIncrementingVersionModifier):
    """"""

    name: str = "alpha"
    aliases: tuple[str] = ("a",)
    description: str = "Increment the alpha pre-release version part"

    @property
    def pre_release_part(
        self,
    ) -> tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        """"""
        return ("a", "alpha")

    def _is_valid_preview_version(self) -> bool:
        """"""
        return self.current_version.is_alpha


@final
class BetaIncrementingVersionModifier(_PreReleaseIncrementingVersionModifier):
    """"""

    name: str = "beta"
    aliases: tuple[str] = ("b",)
    description: str = "Increment the beta pre-release version part"

    @property
    def pre_release_part(
        self,
    ) -> tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        """"""
        return ("b", "alpha or beta")

    def _is_valid_preview_version(self) -> bool:
        """"""
        return self.current_version.is_alpha or self.current_version.is_beta


@final
class ReleaseCandidateIncrementingVersionModifier(
    _PreReleaseIncrementingVersionModifier
):
    """"""

    name: str = "rc"
    description: str = (
        "Increment the release-candidate pre-release version part"
    )
    aliases: tuple[str] = ("c",)

    @property
    def pre_release_part(
        self,
    ) -> tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        """"""
        return ("rc", "pre-release")

    def _is_valid_preview_version(self) -> bool:
        """"""
        return (
            self.current_version.is_alpha
            or self.current_version.is_beta
            or self.current_version.is_release_candidate
        )
