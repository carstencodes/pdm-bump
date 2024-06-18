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


# Implementation of the PEP 440 version.
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Annotated, Any, Final, Literal, Optional, cast, final

from annotated_types import Ge
from packaging.version import InvalidVersion
from packaging.version import Version as BaseVersion
from pdm_pfsc.logging import traced_function


@final
class VersionParserError(ValueError):
    """"""

    # Justification: Zen of python: Explicit is better than implicit
    pass  # pylint: disable=W0107


NonNegative = Ge(0)

NonNegativeInteger = Annotated[int, NonNegative]


@final
@dataclass(eq=False, order=False, frozen=True)
@total_ordering
class Version:
    """"""

    epoch: "NonNegativeInteger" = field(
        default=0, repr=True, hash=True, compare=True
    )
    release_tuple: "tuple[NonNegativeInteger, ...]" = field(default=(1, 0, 0))
    preview: Optional[
        tuple[
            Literal["a", "b", "c", "alpha", "beta", "rc"], NonNegativeInteger
        ]
    ] = field(default=None, repr=True, hash=True, compare=True)
    post: 'Optional[tuple[Literal["post"], NonNegativeInteger]]' = field(
        default=None, repr=True, hash=True, compare=True
    )
    dev: 'Optional[tuple[Literal["dev"], NonNegativeInteger]]' = field(
        default=None, repr=True, hash=True, compare=True
    )
    local: "Optional[str]" = field(
        default=None, repr=True, hash=True, compare=True
    )

    def __post_init__(self):
        if self.is_pre_release and not self.is_development_version:
            if self.preview[0] not in ["a", "b", "c", "alpha", "beta", "rc"]:
                raise ValueError(
                    f"Invalid pre-release identifier {self.preview[0]}"
                )

    @property
    def major(self) -> "NonNegativeInteger":
        """"""
        return self.release_tuple[0] if len(self.release_tuple) >= 1 else 0

    @property
    def minor(self) -> "NonNegativeInteger":
        """"""
        return self.release_tuple[1] if len(self.release_tuple) >= 2 else 0

    @property
    def micro(self) -> "NonNegativeInteger":
        """"""
        return self.release_tuple[2] if len(self.release_tuple) >= 3 else 0

    @property
    def release(
        self,
    ) -> "tuple[NonNegativeInteger, NonNegativeInteger, NonNegativeInteger]":
        """"""
        return (
            self.major,
            self.minor,
            self.micro,
        )

    @property
    def is_pre_release(self) -> bool:
        """"""
        return self.preview is not None or self.is_development_version

    @property
    def is_development_version(self) -> bool:
        """"""
        return self.dev is not None

    @property
    def is_post_release(self) -> bool:
        """"""
        return self.post is not None

    @property
    def is_local_version(self) -> bool:
        """"""
        return self.local is not None

    @property
    def is_alpha(self) -> bool:
        """"""
        alpha_part: Final[tuple[str, ...]] = ("a", "alpha")
        return self.preview is not None and self.__compare_preview(alpha_part)

    @property
    def is_beta(self) -> bool:
        """"""
        beta_part: Final[tuple[str, ...]] = ("b", "beta")
        return self.preview is not None and self.__compare_preview(beta_part)

    @property
    def is_release_candidate(self) -> bool:
        """"""
        rc_part: Final[tuple[str, ...]] = ("c", "rc")
        return self.preview is not None and self.__compare_preview(rc_part)

    @property
    def is_final(self) -> bool:
        """"""
        return (
            not self.preview
            and not self.is_local_version
            and not self.is_post_release
            and not self.is_development_version
        )

    def __compare_preview(self, valid_parts: tuple[str, ...]) -> bool:
        if self.preview is not None:
            pre: tuple[str, int] = cast("tuple[str, int]", self.preview)
            return pre[0] in valid_parts
        return False

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise ValueError(f"{other} must be an instance of Version")
        other_version: Version = cast("Version", other)
        return (
            self.epoch == other.epoch
            and self.release == other_version.release
            and self.preview == other_version.preview
            and self.post == other_version.post
            and self.dev == other_version.dev
            and self.local == other_version.local
        )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise ValueError(f"{other} must be an instance of Version")
        other_version: Version = cast("Version", other)
        my_data = (
            self.epoch,
            self.release,
            self.preview,
            self.post,
            self.dev,
            self.local,
        )
        other_data = (
            other_version.epoch,
            other_version.release,
            other_version.preview,
            other_version.post,
            other_version.dev,
            other_version.local,
        )
        return my_data < other_data

    def __str__(self) -> str:
        return Pep440VersionFormatter().format(self)

    @staticmethod
    def default() -> "Version":
        """"""
        return Version(0, (1,), None, None, None, None)

    @staticmethod
    def from_string(version: str) -> "Version":
        """

        Parameters
        ----------
        version: str :


        Returns
        -------

        """
        try:
            _version: "BaseVersion" = BaseVersion(version)

            return Version(
                _version.epoch,
                _version.release,
                cast(
                    "Optional["
                    "tuple["
                    "Literal['a', 'b', 'c', 'alpha', 'beta', 'rc'], int"
                    "]"
                    "]",
                    _version.pre,
                ),
                ("post", _version.post) if _version.post is not None else None,
                ("dev", _version.dev) if _version.dev is not None else None,
                _version.local,
            )
        except InvalidVersion as error:
            raise VersionParserError(
                f"{version} is not a valid version according to PEP 440."
            ) from error

    @staticmethod
    def can_parse_to_version(version: str) -> bool:
        """

        Parameters
        ----------
        version: str :


        Returns
        -------

        """
        try:
            _ = Version.from_string(version)
            return True
        except VersionParserError:
            return False


@final
# Justification: Only method to provide
class Pep440VersionFormatter:  # pylint: disable=R0903
    """"""

    @traced_function
    def format(self, version: "Version") -> str:
        """

        Parameters
        ----------
        version: Version :


        Returns
        -------

        """
        parts: list[str] = []

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
