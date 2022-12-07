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
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict as dataclass_to_dict
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    FrozenSet,
    List,
    Literal,
    Tuple,
    Union,
    cast,
    final,
)

from .logging import logger, traced_function
from .version import NonNegativeInteger, Pep440VersionFormatter, Version

if sys.version_info >= (3, 10, 0):
    # suspicious mypy behavior
    from typing import TypeAlias  # type: ignore
else:
    from typing_extensions import TypeAlias

_formatter = Pep440VersionFormatter()


class PreviewMismatchError(Exception):
    pass


class VersionModifier(ABC):
    def __init__(self, version: Version) -> None:
        self.__version = version

    @property
    def current_version(self) -> Version:
        return self.__version

    @abstractmethod
    def create_new_version(self) -> Version:
        raise NotImplementedError()

    def _report_new_version(self, next_version: Version) -> None:
        logger.info(
            "Performing increment of version: %s -> %s",
            _formatter.format(self.current_version),
            _formatter.format(next_version),
        )


class _PreReleaseIncrementingVersionModified(VersionModifier):
    def __init__(self, version: Version, increment_micro: bool = True) -> None:
        super().__init__(version)
        self.__increment_micro = increment_micro

    @traced_function
    def create_new_version(self) -> Version:
        letter: Literal["a", "b", "c", "alpha", "beta", "rc"]
        name: str
        letter, name = self.pre_release_part
        pre: Tuple[
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
                Tuple[
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
    ) -> Tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        raise NotImplementedError()

    @abstractmethod
    def _is_valid_preview_version(self) -> bool:
        raise NotImplementedError()

    def _get_next_release(self) -> Tuple[NonNegativeInteger, ...]:
        micro = self.current_version.micro
        if self.__increment_micro and self.current_version.preview is None:
            micro = micro + 1

        ret: List[NonNegativeInteger] = []
        for val in self.current_version.release:
            ret.append(val)

        while len(ret) < 3:
            ret.append(0)

        ret[2] = micro

        return tuple(ret)


@final
class AlphaIncrementingVersionModifier(_PreReleaseIncrementingVersionModified):
    @property
    def pre_release_part(
        self,
    ) -> Tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        return ("a", "alpha")

    def _is_valid_preview_version(self) -> bool:
        return self.current_version.is_alpha


@final
class BetaIncrementingVersionModifier(_PreReleaseIncrementingVersionModified):
    @property
    def pre_release_part(
        self,
    ) -> Tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        return ("b", "alpha or beta")

    def _is_valid_preview_version(self) -> bool:
        return self.current_version.is_alpha or self.current_version.is_beta


@final
class ReleaseCandidateIncrementingVersionModifier(
    _PreReleaseIncrementingVersionModified
):
    @property
    def pre_release_part(
        self,
    ) -> Tuple[Literal["a", "b", "c", "alpha", "beta", "rc"], str]:
        return ("rc", "pre-release")

    def _is_valid_preview_version(self) -> bool:
        return (
            self.current_version.is_alpha
            or self.current_version.is_beta
            or self.current_version.is_release_candidate
        )


class _NonFinalPartsRemovingVersionModifier(VersionModifier):
    def __init__(self, version: Version, remove_parts: bool = True) -> None:
        super().__init__(version)
        self.__remove_parts = remove_parts

    @property
    def remove_non_final_parts(self) -> bool:
        return self.__remove_parts

    @abstractmethod
    def create_new_version(self) -> Version:
        raise NotImplementedError()

    @staticmethod
    def _create_new_constructional_args(
        release: Tuple[NonNegativeInteger, ...], epoch: NonNegativeInteger = 0
    ) -> Dict[str, Any]:
        return {
            "epoch": epoch,
            "release_tuple": release,
            "preview": None,
            "post": None,
            "dev": None,
            "local": None,
        }


_NFPR: TypeAlias = _NonFinalPartsRemovingVersionModifier


class _ReleaseVersionModifier(_NonFinalPartsRemovingVersionModifier):
    @property
    @abstractmethod
    def release_part(self) -> NonNegativeInteger:
        raise NotImplementedError()

    @traced_function
    def create_new_version(self):
        construction_args: Dict[str, Any] = dataclass_to_dict(
            self.current_version
        )

        next_release: Tuple[
            NonNegativeInteger, ...
        ] = self._update_release_version_part(self.release_part)

        if self.remove_non_final_parts:
            logger.debug("Removing non-final parts of version")
            # Using type alias due to line length enforced by black
            construction_args = _NFPR._create_new_constructional_args(  # noqa: E501 pylint: disable=W0212
                next_release, self.current_version.epoch
            )
        else:
            construction_args["release_tuple"] = next_release

        next_version: Version = Version(**construction_args)
        self._report_new_version(next_version)

        return next_version

    def _update_release_version_part(
        self, part_id: NonNegativeInteger
    ) -> Tuple[NonNegativeInteger, ...]:
        release_part: List[NonNegativeInteger] = list(
            self.current_version.release
        )

        for i in range(len(release_part)):  # pylint: disable=C0200
            logger.debug("Checking if version part at %d must be modified", i)
            if i == part_id:
                logger.debug("Incrementing version part at position %d.", i)
                release_part[i] = release_part[i] + 1
            elif i > part_id:
                logger.debug("Resetting version part at position %d", i)
                release_part[i] = 0

        return tuple(release_part)


@final
class FinalizingVersionModifier(_NonFinalPartsRemovingVersionModifier):
    def __init__(self, version: Version) -> None:
        super().__init__(version, True)

    @traced_function
    def create_new_version(self) -> Version:
        constructional_args: Dict[
            str,
            Any
            # Using type alias due to line length enforced by black
        ] = _NFPR._create_new_constructional_args(  # noqa: E501 pylint: disable=W0212
            self.current_version.release, self.current_version.epoch
        )

        next_version: Version = Version(**constructional_args)
        self._report_new_version(next_version)

        return next_version


@final
class MajorIncrementingVersionModifier(_ReleaseVersionModifier):
    __MAJOR_PART: Final[NonNegativeInteger] = 0

    @property
    def release_part(self) -> NonNegativeInteger:
        return self.__MAJOR_PART


@final
class MinorIncrementingVersionModifier(_ReleaseVersionModifier):
    __MINOR_PART: Final[NonNegativeInteger] = 1

    @property
    def release_part(self) -> NonNegativeInteger:
        return self.__MINOR_PART


@final
class MicroIncrementingVersionModifier(_ReleaseVersionModifier):
    __MICRO_PART: Final[NonNegativeInteger] = 2

    @property
    def release_part(self) -> int:
        return self.__MICRO_PART


@final
class EpochIncrementingVersionModifier(_NonFinalPartsRemovingVersionModifier):
    def __init__(
        self,
        version: Version,
        remove_parts: bool = True,
        reset_version: bool = True,
    ):
        super().__init__(version, remove_parts)
        self.__reset_version = reset_version

    @traced_function
    def create_new_version(self) -> Version:
        constructional_args: Dict[str, Any] = dataclass_to_dict(
            self.current_version
        )

        if self.__reset_version or self.remove_non_final_parts:
            constructional_args = dataclass_to_dict(Version.default())
            if not self.__reset_version:
                logger.debug("Current version tuple shall not be reset")
                constructional_args[
                    "release_tuple"
                ] = self.current_version.release

        logger.debug("Incrementing Epoch of version")
        constructional_args["epoch"] = self.current_version.epoch + 1

        next_version: Version = Version(**constructional_args)
        self._report_new_version(next_version)
        return next_version


@final
class DevelopmentVersionIncrementingVersionModifier(VersionModifier):
    @traced_function
    def create_new_version(self) -> Version:
        dev_version: NonNegativeInteger = 1
        if self.current_version.dev is not None:
            _, dev_version = self.current_version.dev
            logger.debug("Incrementing development version part by one")
            dev_version = dev_version + 1

        constructional_args: Dict[str, Any] = dataclass_to_dict(
            self.current_version
        )
        constructional_args["dev"] = ("dev", dev_version)

        next_version: Version = Version(**constructional_args)
        self._report_new_version(next_version)

        return next_version


@final
class PostVersionIncrementingVersionModifier(VersionModifier):
    @traced_function
    def create_new_version(self) -> Version:
        post_version: NonNegativeInteger = 1
        if self.current_version.post is not None:
            _, post_version = self.current_version.post
            logger.debug("Incrementing post version part by one")
            post_version = post_version + 1

        constructional_args: Dict[str, Any] = dataclass_to_dict(
            self.current_version
        )
        constructional_args["post"] = ("post", post_version)

        next_version: Version = Version(**constructional_args)
        self._report_new_version(next_version)

        return next_version


VersionModifierFactory: TypeAlias = Callable[[Version], VersionModifier]
_NestedMappingTable: TypeAlias = Dict[str, VersionModifierFactory]
ActionChoice: TypeAlias = Union[_NestedMappingTable, VersionModifierFactory]


@final
class ActionCollection(Dict[str, ActionChoice]):
    @traced_function
    def get_action(self, action: str) -> VersionModifierFactory:
        if action in self.keys():
            choice: ActionChoice = self[action]
            if not isinstance(choice, str):
                return cast(VersionModifierFactory, choice)

        raise ValueError(f"{action} is not a valid command")

    @traced_function
    def get_action_with_option(
        self, action: str, option: str
    ) -> VersionModifierFactory:
        if action in self.keys():
            choice: ActionChoice = self[action]
            if not isinstance(choice, str):
                table: _NestedMappingTable = cast(_NestedMappingTable, choice)
                if option in table.keys():
                    choice = table[option]
                    return cast(VersionModifierFactory, choice)

                raise ValueError(f"{option} is not a valid option")

        raise ValueError(f"{action} is not a valid command")


COMMAND_NAME_MAJOR_INCREMENT: Final[str] = "major"
COMMAND_NAME_MINOR_INCREMENT: Final[str] = "minor"
COMMAND_NAME_MICRO_INCREMENT: Final[str] = "micro"
COMMAND_NAME_PATCH_INCREMENT: Final[str] = "patch"
COMMAND_NAME_EPOCH_INCREMENT: Final[str] = "epoch"
COMMAND_NAME_NO_PRERELEASE: Final[str] = "no-pre-release"
COMMAND_NAME_PRERELEASE: Final[str] = "pre-release"
COMMAND_NAME_DEV_INCREMENT: Final[str] = "dev"
COMMAND_NAME_POST_INCREMENT: Final[str] = "post"

PRE_RELEASE_OPTION_ALPHA: Final[str] = "alpha"
PRE_RELEASE_OPTION_BETA: Final[str] = "beta"
PRE_RELEASE_OPTION_RC: Final[str] = "rc"
PRE_RELEASE_OPTION_RC_ALT: Final[str] = "c"

_next_major: TypeAlias = MajorIncrementingVersionModifier
_next_minor: TypeAlias = MinorIncrementingVersionModifier
_next_micro: TypeAlias = MicroIncrementingVersionModifier
_next_alpha: TypeAlias = AlphaIncrementingVersionModifier
_next_beta: TypeAlias = BetaIncrementingVersionModifier
_next_rc: TypeAlias = ReleaseCandidateIncrementingVersionModifier
_no_pre: TypeAlias = FinalizingVersionModifier
_next_dev: TypeAlias = DevelopmentVersionIncrementingVersionModifier
_next_post: TypeAlias = PostVersionIncrementingVersionModifier
_next_epoch: TypeAlias = EpochIncrementingVersionModifier


def create_actions(
    *,
    remove_parts: bool = True,
    reset_version: bool = True,
    increment_micro: bool = False,
) -> ActionCollection:
    return ActionCollection(
        {
            COMMAND_NAME_MAJOR_INCREMENT: lambda v: _next_major(
                v, remove_parts
            ),
            COMMAND_NAME_MINOR_INCREMENT: lambda v: _next_minor(
                v, remove_parts
            ),
            COMMAND_NAME_MICRO_INCREMENT: lambda v: _next_micro(
                v, remove_parts
            ),
            COMMAND_NAME_PATCH_INCREMENT: lambda v: _next_micro(
                v, remove_parts
            ),
            COMMAND_NAME_PRERELEASE: {
                PRE_RELEASE_OPTION_ALPHA: lambda v: _next_alpha(
                    v, increment_micro
                ),
                PRE_RELEASE_OPTION_BETA: lambda v: _next_beta(
                    v, increment_micro
                ),
                PRE_RELEASE_OPTION_RC: lambda v: _next_rc(v, increment_micro),
                PRE_RELEASE_OPTION_RC_ALT: lambda v: _next_rc(
                    v, increment_micro
                ),
            },
            # Justifications: Explicit call of type, line too long due to noqa
            COMMAND_NAME_NO_PRERELEASE: lambda v: _no_pre(  # noqa: E501 pylint: disable=W0108
                v
            ),
            COMMAND_NAME_EPOCH_INCREMENT: lambda v: _next_epoch(
                v, remove_parts, reset_version
            ),
            # Justifications: Explicit call of type, line too long due to noqa
            COMMAND_NAME_DEV_INCREMENT: lambda v: _next_dev(  # noqa: E501 pylint: disable=W0108
                v
            ),
            # Justifications: Explicit call of type, line too long due to noqa
            COMMAND_NAME_POST_INCREMENT: lambda v: _next_post(  # noqa: E501 pylint: disable=W0108
                v
            ),
        }
    )


COMMAND_NAMES: Final[FrozenSet[str]] = frozenset(
    [
        COMMAND_NAME_MAJOR_INCREMENT,
        COMMAND_NAME_MINOR_INCREMENT,
        COMMAND_NAME_MICRO_INCREMENT,
        COMMAND_NAME_PATCH_INCREMENT,
        COMMAND_NAME_PRERELEASE,
        COMMAND_NAME_NO_PRERELEASE,
        COMMAND_NAME_EPOCH_INCREMENT,
        COMMAND_NAME_DEV_INCREMENT,
        COMMAND_NAME_POST_INCREMENT,
    ]
)

PRERELEASE_OPTIONS: Final[FrozenSet[str]] = frozenset(
    [
        PRE_RELEASE_OPTION_ALPHA,
        PRE_RELEASE_OPTION_BETA,
        PRE_RELEASE_OPTION_RC,
        PRE_RELEASE_OPTION_RC_ALT,
    ]
)
