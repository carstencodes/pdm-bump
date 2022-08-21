from abc import ABC, abstractmethod, abstractproperty
from dataclasses import asdict as dataclass_to_dict
from typing import Any, Dict, List, Tuple, Final, Union, Type, Callable, Set, cast

from .version import Pep440VersionFormatter, Version, NonNegativeInteger
from .logging import logger

_formatter = Pep440VersionFormatter()


class PreviewMismatchError(BaseException):
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


class _PreReleaseIncrementingVersionModified(VersionModifier):
    def __init__(self, version: Version, increment_micro: bool = True) -> None:
        super().__init__(version)
        self.__increment_micro = increment_micro

    def create_new_version(self) -> Version:
        letter: str
        name: str
        letter, name = self.pre_release_part
        pre: Tuple[str, NonNegativeInteger] = (letter, 1)
        if self.current_version.preview is not None:
            if not self._is_valid_preview_version():
                raise PreviewMismatchError(
                    f"{_formatter.format(self.current_version)} is not an {name} version."
                )
            pre = cast(Tuple[str, NonNegativeInteger], self.create_new_version.pre)
            pre = (pre[0], pre[1] + 1)

        return Version(
            self.current_version.epoch, self._get_next_release(), pre, None, None, None
        )

    @abstractproperty
    def pre_release_part(self) -> Tuple[str, str]:
        raise NotImplementedError()

    @abstractmethod
    def _is_valid_preview_version(self) -> bool:
        raise NotImplementedError()

    def _get_next_release(self) -> Tuple[NonNegativeInteger, ...]:
        micro = self.current_version.micro
        if self.__increment_micro:
            micro = micro + 1

        ret: List[NonNegativeInteger] = []
        for val in self.current_version.release:
            ret.append(val)

        while len(ret) < 3:
            ret.append(0)

        ret[2] = micro

        return tuple(ret)


class AlphaIncrementingVersionModifier(_PreReleaseIncrementingVersionModified):
    @property
    def pre_release_part(self) -> Tuple[str, str]:
        return ("a", "alpha")

    def _is_valid_preview_version(self) -> bool:
        return self.current_version.is_alpha


class BetaIncrementingVersionModifier(_PreReleaseIncrementingVersionModified):
    @property
    def pre_release_part(self) -> Tuple[str, str]:
        return ("b", "alpha or beta")

    def _is_valid_preview_version(self) -> bool:
        return self.current_version.is_alpha or self.current_version.is_beta


class ReleaseCandidateIncrementingVersionModifier(
    _PreReleaseIncrementingVersionModified
):
    @property
    def pre_release_part(self) -> Tuple[str, str]:
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
            "release": release,
            "preview": None,
            "post": None,
            "dev": None,
            "local": None,
        }


class _ReleaseVersionModifier(_NonFinalPartsRemovingVersionModifier):
    @abstractproperty
    def release_part(self) -> NonNegativeInteger:
        raise NotImplementedError()

    def create_new_version(self):
        construction_args: Dict[str, Any] = dataclass_to_dict(self.current_version)

        next_release: Tuple[
            NonNegativeInteger, ...
        ] = self._update_release_version_part(self.release_part)

        if self.remove_non_final_parts:
            construction_args = (
                _NonFinalPartsRemovingVersionModifier._create_new_constructional_args(
                    next_release, self.current_version.epoch
                )
            )
        else:
            construction_args["release"] = next_release

        return Version(**construction_args)

    def _update_release_version_part(
        self, part_id: NonNegativeInteger
    ) -> Tuple[NonNegativeInteger, ...]:
        release_part: List[NonNegativeInteger] = list(self.current_version.release)
        for i in range(len(release_part)):
            if i == part_id:
                release_part[i] = release_part[i] + 1
            elif i > part_id:
                release_part[i] = 0

        return tuple(release_part)


class FinalizingVersionModifier(_NonFinalPartsRemovingVersionModifier):
    def __init__(self, version: Version) -> None:
        super().__init__(version, True)

    def create_new_version(self) -> Version:
        constructional_args: Dict[
            str, Any
        ] = _NonFinalPartsRemovingVersionModifier._create_new_constructional_args(
            self.current_version.release, self.current_version.epoch
        )
        return Version(**constructional_args)


class MajorIncrementingVersionModifier(_ReleaseVersionModifier):
    __MAJOR_PART: Final[NonNegativeInteger] = 0

    @property
    def release_part(self) -> NonNegativeInteger:
        return self.__MAJOR_PART


class MinorIncrementingVersionModifier(_ReleaseVersionModifier):
    __MINOR_PART: Final[NonNegativeInteger] = 1

    @property
    def release_part(self) -> NonNegativeInteger:
        return self.__MINOR_PART


class MicroIncrementingVersionModifier(_ReleaseVersionModifier):
    __MICRO_PART: Final[NonNegativeInteger] = 2

    @property
    def release_part(self) -> int:
        return self.__MICRO_PART


class EpochIncrementingVersionModifier(_NonFinalPartsRemovingVersionModifier):
    def __init__(
        self, version: Version, remove_parts: bool = True, reset_version: bool = True
    ):
        super().__init__(version, remove_parts)
        self.__reset_version = reset_version

    def create_new_version(self) -> Version:
        constructional_args: Dict[str, Any] = dataclass_to_dict(self.current_version)

        if self.__reset_version or self.remove_non_final_parts:
            constructional_args = dataclass_to_dict(Version.default())
            if not self.__reset_version:
                constructional_args["release"] = self.current_version.release

        constructional_args["epoch"] = self.current_version.epoch + 1

        return Version(**constructional_args)


class DevelopmentVersionIncrementingVersionModifier(VersionModifier):
    def create_new_version(self) -> Version:
        dev_version: NonNegativeInteger = 1
        if self.current_version.is_development_version:
            _, dev_version = self.current_version.dev
            dev_version = dev_version + 1

        constructional_args: Dict[str, Any] = dataclass_to_dict(self.current_version)
        constructional_args["dev"] = ("dev", dev_version)

        return Version(**constructional_args)


class PostVersionIncrementingVersionModifier(VersionModifier):
    def create_new_version(self) -> Version:
        post_version: NonNegativeInteger = 1
        if self.current_version.is_post_release:
            _, post_version = self.current_version.post
            post_version = post_version + 1

        constructional_args: Dict[str, Any] = dataclass_to_dict(self.current_version)
        constructional_args["post"] = ("post", post_version)

        return Version(**constructional_args)


VersionModifierFactory: Type = Callable[[Version], VersionModifier]
_NestedMappingTable: Type = Dict[str, VersionModifierFactory]
ActionChoice: Type = Union[_NestedMappingTable, VersionModifierFactory]


class ActionCollection(Dict[str, ActionChoice]):
    def get_action(self, action: str) -> VersionModifierFactory:
        if action in self.keys():
            choice: ActionChoice = self[action]
            if not isinstance(choice, str):
                return cast(VersionModifierFactory, choice)

        raise ValueError(f"{action} is not a valid command")

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


def create_actions(
    *,
    remove_parts: bool = True,
    reset_version: bool = True,
    increment_micro: bool = False,
) -> ActionCollection:
    return ActionCollection(
        {
            COMMAND_NAME_MAJOR_INCREMENT: lambda v: MajorIncrementingVersionModifier(
                v, remove_parts
            ),
            COMMAND_NAME_MINOR_INCREMENT: lambda v: MinorIncrementingVersionModifier(
                v, remove_parts
            ),
            COMMAND_NAME_MICRO_INCREMENT: lambda v: MicroIncrementingVersionModifier(
                v, remove_parts
            ),
            COMMAND_NAME_PATCH_INCREMENT: lambda v: MicroIncrementingVersionModifier(
                v, remove_parts
            ),
            COMMAND_NAME_PRERELEASE: {
                PRE_RELEASE_OPTION_ALPHA: lambda v: AlphaIncrementingVersionModifier(
                    v, increment_micro
                ),
                PRE_RELEASE_OPTION_BETA: lambda v: BetaIncrementingVersionModifier(
                    v, increment_micro
                ),
                PRE_RELEASE_OPTION_RC: lambda v: ReleaseCandidateIncrementingVersionModifier(
                    v, increment_micro
                ),
                PRE_RELEASE_OPTION_RC_ALT: lambda v: ReleaseCandidateIncrementingVersionModifier(
                    v, increment_micro
                ),
            },
            COMMAND_NAME_NO_PRERELEASE: lambda v: FinalizingVersionModifier(v),
            COMMAND_NAME_EPOCH_INCREMENT: lambda v: EpochIncrementingVersionModifier(
                v, remove_parts, reset_version
            ),
            COMMAND_NAME_DEV_INCREMENT: lambda v: DevelopmentVersionIncrementingVersionModifier(
                v
            ),
            COMMAND_NAME_POST_INCREMENT: lambda v: PostVersionIncrementingVersionModifier(
                v
            ),
        }
    )


COMMAND_NAMES: Final[Set[str]] = frozenset(
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

PRERELEASE_OPTIONS: Final[Set[str]] = frozenset(
    [
        PRE_RELEASE_OPTION_ALPHA,
        PRE_RELEASE_OPTION_BETA,
        PRE_RELEASE_OPTION_RC,
        PRE_RELEASE_OPTION_RC_ALT,
    ]
)
