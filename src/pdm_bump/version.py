#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#

# Implementation of the PEP 440 version.
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Annotated, Any, List, Literal, Optional, Tuple, cast

from annotated_types import Ge
from packaging.version import InvalidVersion
from packaging.version import Version as BaseVersion

from .logging import traced_function


class VersionParserError(ValueError):
    pass


__ALPHA_PART: Tuple[str, ...] = ("a", "alpha")
__BETA_PART: Tuple[str, ...] = ("b", "beta")
__RC_PART: Tuple[str, ...] = ("c", "rc")

NonNegative = Ge(0)

NonNegativeInteger = Annotated[int, NonNegative]


@dataclass(eq=False, order=False, frozen=True)
@total_ordering
class Version:
    epoch: NonNegativeInteger = field()
    release: Tuple[NonNegativeInteger, ...] = field()
    preview: Optional[
        Tuple[
            Literal["a", "b", "c", "alpha", "beta", "rc"], NonNegativeInteger
        ]
    ] = field()
    post: Optional[Tuple[Literal["post"], NonNegativeInteger]] = field()
    dev: Optional[Tuple[Literal["dev"], NonNegativeInteger]] = field()
    local: Optional[str] = field()

    @property
    def major(self) -> NonNegativeInteger:
        return self.release[0] if len(self.release) >= 1 else 0

    @property
    def minor(self) -> NonNegativeInteger:
        return self.release[1] if len(self.release) >= 2 else 0

    @property
    def micro(self) -> NonNegativeInteger:
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
        return self.preview is not None and self.__compare_preview(
            __ALPHA_PART
        )

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

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise ValueError(f"{other} must be an instance of Version")
        other_version: Version = cast(Version, other)
        return (
            self.release == other_version.release
            and self.preview == other_version.preview
            and self.post == other_version.dev
            and self.dev == other_version.dev
            and self.local == other_version.local
        )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise ValueError(f"{other} must be an instance of Version")
        other_version: Version = cast(Version, other)
        my_data = (self.release, self.preview, self.post, self.dev, self.local)
        other_data = (
            other_version.release,
            other_version.preview,
            other_version.post,
            other_version.dev,
            other_version.local,
        )
        return my_data < other_data

    @staticmethod
    def default() -> "Version":
        return Version(0, (1,), None, None, None, None)

    @staticmethod
    def from_string(version: str) -> "Version":
        try:
            _version: BaseVersion = BaseVersion(version)

            return Version(
                _version.epoch,
                _version.release,
                cast(
                    Optional[
                        Tuple[
                            Literal["a", "b", "c", "alpha", "beta", "rc"], int
                        ]
                    ],
                    _version.pre,
                ),
                ("post", _version.post[1])
                if _version.post is not None
                else None,
                ("dev", _version.dev[1]) if _version.dev is not None else None,
                _version.local,
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


# Justification: Only method to provide
class Pep440VersionFormatter:  # pylint: disable=R0903
    @traced_function
    def format(self, version: Version) -> str:
        parts: List[str] = []

        if version.epoch > 0:
            parts.append(f"{version.epoch}!")

        parts.append(".".join(str(part) for part in version.release))

        if version.preview is not None:
            parts.extend(str(part) for part in version.preview)

        if version.post is not None:
            parts.append(f".post{list(version.post)[1]}")

        if version.dev is not None:
            parts.append(f".dev{list(version.dev)[1]}")

        if version.is_local_version:
            parts.append(f"+{version.local}")

        return "".join(parts)
