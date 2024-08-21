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
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, cast

from pdm_pfsc.actions import ActionBase, ActionRegistry
from pdm_pfsc.hook import HookGenerator, HookInfo
from pdm_pfsc.logging import logger

from ..core.version import Pep440VersionFormatter, Version
from .hook import CommitChanges, HookExecutor, TagChanges

_formatter = Pep440VersionFormatter()

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Generator

    from ..core.config import PdmBumpConfig
    from ..vcs.core import HunkSource, VcsProvider


# Justification: Just a protocol
class VersionPersister(Protocol):  # pylint: disable=R0903
    """"""

    def save_version(self, version: "Version") -> None:
        """

        Parameters
        ----------
        version: Version :


        Returns
        -------

        """
        raise NotImplementedError()


class VersionConsumer(ActionBase[Version]):
    """"""

    def __init__(self, version: "Version", **kwargs) -> None:
        super().__init__(**kwargs)
        self.__version = version

    @property
    def current_version(self) -> "Version":
        """"""
        return self.__version

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return {"version"}.union(ActionBase.get_allowed_arguments())


class VersionModifier(VersionConsumer):
    """"""

    def __init__(
        self, version: "Version", persister: "VersionPersister", **kwargs
    ) -> None:
        super().__init__(version, **kwargs)
        self.__persister = persister

    @abstractmethod
    def create_new_version(self) -> "Version":
        """"""
        raise NotImplementedError()

    @classmethod
    def generate_hook_infos(cls) -> "Generator[HookInfo, None, None]":
        """

        Returns:
        --------
        """
        yield HookInfo(CommitChanges)
        yield HookInfo(TagChanges)

    def _report_new_version(self, next_version: "Version") -> None:
        """

        Parameters
        ----------
        next_version: Version :


        Returns
        -------

        """
        logger.info(
            "Performing increment of version: %s -> %s",
            _formatter.format(self.current_version),
            _formatter.format(next_version),
        )

    def run(self, dry_run: bool = False) -> "Version":
        """

        Parameters
        ----------
        dry_run: bool :
             (Default value = False)

        Returns
        -------

        """
        next_version: "Version" = self.create_new_version()
        if next_version is self.current_version:
            return next_version

        if not dry_run:
            self.__persister.save_version(next_version)
        else:
            logger.info("Would write new version %s", next_version)

        return next_version

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return {"persister"}.union(VersionConsumer.get_allowed_arguments())

    def __str__(self) -> str:
        return self.__class__.__name__.replace(VersionModifier.__name__, "")


@dataclass(frozen=True)
class ExecutionContext:
    """"""

    version: "Version" = field()
    persister: "VersionPersister" = field()
    vcs_provider: "VcsProvider" = field()
    hunk_source: "HunkSource" = field()
    config: "PdmBumpConfig" = field()


class _VersionActions(ActionRegistry[ExecutionContext]):
    def execute(  # pylint: disable=R0913,R0914
        self,
        /,
        args: "Namespace",
        context: "ExecutionContext",
    ) -> None:
        """

        Parameters
        ----------
        / :

        args: Namespace :

        context: ExecutionContext :


        Returns
        -------

        """
        kwargs: dict = {}

        known_aliases: dict = {}
        for key, value in self._items.items():
            if "aliases" in vars(value):
                aliases = list(getattr(value, "aliases", []))
                known_aliases.update({a: key for a in aliases})

        kwargs.update(vars(args))

        kwargs = {
            key: value
            for key, value in kwargs.items()
            if not key.startswith("_")
        }

        dry_run: bool = kwargs.pop("dry_run", False)

        selected_command: str = kwargs.pop("selected_command")
        selected_command = known_aliases.get(
            selected_command, selected_command
        )

        if selected_command not in self._items:
            raise ValueError(
                f"Failed to get command {selected_command}. "
                + f"Valid values are {', '.join(self._items.keys())}."
            )

        clazz: type[ActionBase] = self._items[selected_command]

        allowed_args: set[str] = clazz.get_allowed_arguments()
        allowed_kwargs: dict[str, Any] = {
            "version": context.version,
            "persister": context.persister,
            "vcs_provider": context.vcs_provider,
        }

        allowed_kwargs = {
            key: value
            for key, value in allowed_kwargs.items()
            if key in allowed_args
        }

        kwargs.update(allowed_kwargs)

        command: "ActionBase" = clazz.create_from_command(**kwargs)
        args = context.config.add_values_missing_in_cli(args)

        executor: HookExecutor = HookExecutor(
            context.hunk_source, context.vcs_provider
        )
        if issubclass(clazz, HookGenerator):
            hook_generator: type[HookGenerator] = cast(
                "type[HookGenerator]", clazz
            )
            for hook_info in hook_generator.generate_hook_infos():
                executor.register(hook_info.create_hook())

        executor.run((command, context.version), args, dry_run=dry_run)


actions = _VersionActions()
action = actions.register()
