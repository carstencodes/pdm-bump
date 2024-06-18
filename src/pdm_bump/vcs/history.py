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
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from enum import Enum, auto
from functools import cached_property
from re import Match, Pattern, compile
from typing import TYPE_CHECKING, Callable, Final, Optional

from pdm_pfsc.logging import logger

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from ..core.version import NonNegativeInteger

""""""


class _StrEnum(str, Enum):
    pass


class CommitType(_StrEnum):
    """"""

    Undefined = auto()
    Feature = "feat"
    Bugfix = "fix"
    Chore = "chore"
    QualityAssurance = "qa"
    Documentation = "docs"
    Build = "build"
    ContinuousIntegration = "ci"
    CodeStyle = "style"
    Refactoring = "refactor"
    Performance = "perf"
    Test = "test"

    @classmethod
    def _missing_(cls, value: object) -> "Enum":
        return CommitType.Undefined

    @classmethod
    def all_values(cls) -> "Mapping[CommitType, str]":
        mapping: "dict[CommitType, str]" = {}
        base_items: list[str] = dir(_StrEnum)
        for key in dir(cls):
            if (
                not key.startswith("_")
                and key != "all_values"
                and key not in base_items
            ):
                mapping[cls[key]] = str(cls[key].value)

        return mapping


class CommitParser(ABC):
    """"""

    @abstractmethod
    def is_breaking_change(self, commit: "Commit") -> bool:
        """"""
        raise NotImplementedError()

    @abstractmethod
    def parse_commit_type(self, commit: "Commit") -> "CommitType":
        """"""
        raise NotImplementedError()


_DEFAULT_MAPPINGS: "Mapping[CommitType, str]" = CommitType.all_values()


class ConventionalCommitParser(CommitParser):
    """"""

    def __init__(
        self, prefix_mappings: "Mapping[CommitType, str]" = _DEFAULT_MAPPINGS
    ) -> None:
        self.__line_parser: "Pattern" = compile(r"^([^:!]+!?):\s.*", flags=0)
        self.__prefix_mappings: "Mapping[CommitType, str]" = prefix_mappings

    def is_breaking_change(self, commit: "Commit") -> bool:
        """"""
        breaking_change_suffix = "!"

        prefix: "Optional[str]" = self.__get_conventional_commit_prefix(commit)
        if prefix is not None:
            return prefix.endswith(breaking_change_suffix)

        return False

    def parse_commit_type(self, commit: "Commit") -> "CommitType":
        """"""
        prefix: "Optional[str]" = self.__get_conventional_commit_prefix(commit)
        if prefix is not None:
            for prefix_to_commit_type in self.__prefix_mappings.items():
                commit_type, configured_prefix = prefix_to_commit_type
                if prefix.startswith(configured_prefix):
                    return commit_type

        return CommitType.Undefined

    def __get_conventional_commit_prefix(
        self, commit: "Commit"
    ) -> "Optional[str]":
        _match: "Optional[Match[str]]" = self.__line_parser.match(
            commit.header
        )
        if _match is not None:
            for group in _match.groups():
                logger.debug(
                    "Found prefix string '%s' for commit '%s'",
                    group,
                    commit.header,
                )
                return group

        return None


@dataclass(init=True, eq=True, order=True, repr=True)
class Commit:
    """"""

    header: "Final[str]" = field(init=True, repr=True, hash=True, compare=True)
    _commit_parser: "CommitParser" = field(
        init=False, compare=False, hash=False, repr=True
    )
    commit_parser_factory: InitVar[Optional[Callable[[], "CommitParser"]]] = (
        None  # NOSONAR
    )

    def __post_init__(
        self,
        commit_parser_factory: Optional[Callable[[], "CommitParser"]] = None,
    ) -> None:
        """"""
        # Justification: False positive
        self._commit_parser = (
            commit_parser_factory()
            if commit_parser_factory is not None
            else ConventionalCommitParser()
        )

    @cached_property
    def commit_type(self) -> "CommitType":
        """"""
        return self._commit_parser.parse_commit_type(self)

    @cached_property
    def is_breaking_change(self) -> bool:
        """"""
        return self._commit_parser.is_breaking_change(self)


@dataclass(frozen=True, repr=True)
class CommitStatistics:
    """"""

    commit_type_count: "Mapping[CommitType, NonNegativeInteger]" = field(
        init=True, default_factory=dict
    )
    contains_breaking_changes: bool = field(init=True, default=False)


@dataclass(init=True, eq=True, order=True, repr=True, frozen=True)
class History:
    """"""

    commits: "Iterable[Commit]" = field(init=True, default_factory=list)

    @cached_property
    def get_commit_stats(self) -> "CommitStatistics":
        """"""
        items: "dict[CommitType, NonNegativeInteger]" = {}

        breaking_changes = False
        for commit in self.commits:
            logger.debug(
                "Commit '%s' is of type %s",
                commit.header,
                commit.commit_type.name,
            )
            commit_type: "CommitType" = commit.commit_type
            items[commit_type] = (
                1 if commit_type not in items else items[commit_type] + 1
            )
            breaking_changes = breaking_changes or commit.is_breaking_change
            if commit.is_breaking_change:
                logger.debug("Commit '%s' is breaking change", commit.header)

        logger.debug(
            "Found the following commit history: \n%s",
            self.__format_for_debug(),
        )

        return CommitStatistics(
            commit_type_count=items, contains_breaking_changes=breaking_changes
        )

    def __format_for_debug(self) -> str:
        """"""
        lines = [
            "[B] | Type      | Commit     ",
            "-----------------------------",
        ]

        for commit in self.commits:
            b = " X " if commit.is_breaking_change else "   "
            c_t = commit.commit_type.value
            lines.append(f"{b} | {c_t: <9} | {commit.header} ")

        return "\n".join(lines)
