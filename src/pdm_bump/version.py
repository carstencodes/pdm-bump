# Implementation of the PEP 440 version.
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, cast

from packaging.version import InvalidVersion
from packaging.version import Version as BaseVersion

from .logging import logger


class VersionParserError(ValueError):
    pass


__ALPHA_PART: Tuple[str, ...] = ("a", "alpha")
__BETA_PART: Tuple[str, ...] = ("b", "beta")
__RC_PART: Tuple[str, ...] = ("c", "rc")


@dataclass
class Version:
    epoch: int = field()
    release: Tuple[int, ...] = field()
    preview: Optional[Tuple[str, int]] = field()
    post: Optional[Tuple[str, int]] = field()
    dev: Optional[Tuple[str, int]] = field()
    local: Optional[str] = field()

    @property
    def major(self) -> int:
        return self.release[0] if len(self.release) >= 1 else 0

    @property
    def minor(self) -> int:
        return self.release[1] if len(self.release) >= 2 else 0

    @property
    def micro(self) -> int:
        return self.release[2] if len(self.release) >= 3 else 0

    @property
    def is_pre_release(self) -> bool:
        return self.preview is not None or self.is_development_version

    @property
    def is_development_version(self) -> bool:
        return self.dev is not None

    @property
    def is_post_release(self) -> bool:
        return self.post is not None

    @property
    def is_local_version(self) -> bool:
        return self.local is not None

    @property
    def is_alpha(self) -> bool:
        return self.preview is not None and self.__compare_preview(__ALPHA_PART)

    @property
    def is_beta(self) -> bool:
        return self.preview is not None and self.__compare_preview(__BETA_PART)

    @property
    def is_release_candidate(self) -> bool:
        return self.preview is not None and self.__compare_preview(__RC_PART)

    def __compare_preview(self, valid_parts: Tuple[str, ...]) -> bool:
        if self.preview is not None:
            pre: Tuple[str, int] = cast(Tuple[str, int], self.preview)
            return pre[0] in valid_parts
        return False

    @staticmethod
    def default() -> "Version":
        return Version(0, (1,), None, None, None, None)

    @staticmethod
    def from_string(version: str) -> "Version":
        try:
            version: BaseVersion = BaseVersion(version)

            return Version(
                version.epoch,
                version.release,
                version.pre,
                version.post,
                version.dev,
                version.local,
            )
        except InvalidVersion as error:
            raise VersionParserError(
                f"{version} is not a valid version according to PEP 440."
            ) from error

    @staticmethod
    def can_parse_to_version(version: str) -> bool:
        try:
            _ = Version.from_string(version)
            return True
        except VersionParserError:
            return False


class Pep440VersionFormatter:
    def format(self, version: Version) -> str:
        parts: List[str] = []

        if version.epoch > 0:
            parts.append(f"{version.epoch}!")

        parts.append(".".join(str(part) for part in version.release))

        if version.preview is not None:
            parts.append(str(part) for part in version.preview)

        if version.is_post_release:
            parts.append(f".post{version.post}")

        if version.is_development_version:
            parts.append(f".dev{version.dev}")

        if version.is_local_version:
            parts.append(f"+{version.local}")

        return "".join(parts)
