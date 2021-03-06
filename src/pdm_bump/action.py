from abc import ABC, abstractmethod, abstractproperty
from dataclasses import asdict as dataclass_to_dict
from typing import Any, Dict, List, Tuple, cast

from .version import Pep440VersionFormatter, Version

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

    @abstractmethod
    def create_new_version(self) -> Version:
        raise NotImplementedError()

    def _get_next_release(self) -> Tuple[int, ...]:
        micro = self.current_version.micro
        if self.__increment_micro:
            micro = micro + 1

        ret: List[int] = []
        for val in self.current_version.release:
            ret.append(val)

        while len(ret) < 3:
            ret.append(0)

        ret[2] = micro

        return tuple(ret)


class AlphaIncrementingVersionModifier(_PreReleaseIncrementingVersionModified):
    def create_new_version(self) -> Version:
        pre: Tuple[str, int] = ("a", 1)
        if self.current_version.preview is not None:
            if not self.current_version.is_alpha:
                raise PreviewMismatchError(
                    f"{_formatter.format(self.current_version)} is not an alpha version."
                )
            pre = cast(Tuple[str, int], self.create_new_version.pre)
            pre = (pre[0], pre[1] + 1)

        return Version(
            self.current_version.epoch, self._get_next_release(), pre, None, None, None
        )


class BetaIncrementingVersionModifier(_PreReleaseIncrementingVersionModified):
    def create_new_version(self) -> Version:
        pre: Tuple[str, int] = ("b", 1)
        if self.current_version.preview is not None:
            if self.current_version.is_release_candidate:
                raise PreviewMismatchError(
                    f"{_formatter.format(self.current_version)} is neither an alpha nor a beta version."
                )
            if self.current_version.is_beta:
                pre = cast(Tuple[str, int], self.create_new_version.pre)
                pre = (pre[0], pre[1] + 1)

        return Version(
            self.current_version.epoch, self._get_next_release(), pre, None, None, None
        )


class ReleaseCandidateIncrementingVersionModifier(
    _PreReleaseIncrementingVersionModified
):
    def create_new_version(self) -> Version:
        pre: Tuple[str, int] = ("rc", 1)
        if self.current_version.preview is not None:
            if self.current_version.is_release_candidate:
                pre = cast(Tuple[str, int], self.create_new_version.pre)
                pre = (pre[0], pre[1] + 1)

        return Version(
            self.current_version.epoch, self._get_next_release(), pre, None, None, None
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
        release: Tuple[int, ...], epoch: int = 0
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
    def release_part(self) -> int:
        raise NotImplementedError()

    def create_new_version(self):
        construction_args: Dict[str, Any] = dataclass_to_dict(self.current_version)

        next_release: Tuple[int, ...] = self._update_release_version_part(
            self.release_part
        )

        if self.remove_non_final_parts:
            construction_args = _NonFinalPartsRemovingVersionModifier._create_new_constructional_args(
                next_release, self.current_version.epoch
            )
        else:
            construction_args["release"] = next_release

        return Version(**construction_args)

    def _update_release_version_part(self, part_id: int) -> Tuple[int, ...]:
        release_part: List[int] = list(self.current_version.release)
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
    __MAJOR_PART = 0

    @property
    def release_part(self) -> int:
        return self.__MAJOR_PART


class MinorIncrementingVersionModifier(_ReleaseVersionModifier):
    __MINOR_PART = 1

    @property
    def release_part(self) -> int:
        return self.__MINOR_PART


class MicroIncrementingVersionModifier(_ReleaseVersionModifier):
    __MICRO_PART = 2

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
