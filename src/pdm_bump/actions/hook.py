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

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cached_property
from typing import Protocol, runtime_checkable

from ..core.version import Pep440VersionFormatter, Version
from ..vcs import HunkSource, VcsProvider


class _Executable(Protocol):  # pylint: disable=R0903
    # Justification: Just a protocol
    """"""

    def run(self, dry_run: bool = False) -> Version:
        """

        Parameters
        ----------
            dry_run :


        Returns
        -------

        """
        raise NotImplementedError()


@dataclass(frozen=True)
class PreHookContext:
    """"""

    vcs_provider: VcsProvider = field()
    version: Version = field()

    @cached_property
    def formatted_version(self) -> str:
        """

        Returns:
        --------
        """
        return Pep440VersionFormatter().format(self.version)


@dataclass(frozen=True)
class PostHookContext:
    """"""

    vcs_provider: VcsProvider = field()
    hunk_source: HunkSource = field()
    version: Version = field()
    version_changed: bool = field()

    @cached_property
    def formatted_version(self) -> str:
        """

        Returns:
        --------
        """
        return Pep440VersionFormatter().format(self.version)


class Hook(ABC):
    """"""

    @abstractmethod
    def pre_action_hook(
        self, context: PreHookContext, args: Namespace
    ) -> None:
        """

        Parameters
        ----------
            context :

            args :


        Returns
        -------

        """
        raise NotImplementedError()

    @abstractmethod
    def post_action_hook(
        self, context: PostHookContext, args: Namespace
    ) -> None:
        """

        Parameters
        ----------
            context :

            args :

        Returns
        -------

        """
        raise NotImplementedError()

    @classmethod
    # Justification: Protocol definition
    # pylint: disable=W0613
    def configure(cls, parser: ArgumentParser) -> None:
        """

        Parameters
        ----------
            parser:

        Returns
        -------

        """
        return  # NOSONAR


@dataclass(frozen=True)
class HookInfo:
    """"""

    hook_type: type[Hook] = field()

    def update_parser(self, parser: ArgumentParser) -> None:
        """

        Parameters:
        -----------
            parser: ArgumentParser :

        Returns:
        --------
        """
        self.hook_type.configure(parser)

    def create_hook(self) -> Hook:
        """

        Returns:
        --------
        """
        return self.hook_type()


@runtime_checkable
class HookGenerator(Protocol):  # pylint: disable=R0903
    # Justification: Just a protocol
    """"""

    @classmethod
    def generate_hook_infos(cls) -> Generator[HookInfo, None, None]:
        """

        Returns:
        --------

        """
        raise NotImplementedError()


class HookExecutor:
    """"""

    def __init__(
        self, hunk_source: HunkSource, vcs_provider: VcsProvider
    ) -> None:
        """

        Parameters:
        -----------
            hunk_source: HunkSource :
            vcs_provider: VcsProvider :

        Returns:
        --------

        """
        self.__hunk_source = hunk_source
        self.__vcs_provider = vcs_provider
        self.__hooks: list[Hook] = []

    def run(
        self,
        executor: _Executable,
        version: Version,
        args: Namespace,
        dry_run: bool = False,
    ) -> None:
        """

        Parameters:
        -----------
            executor: _Executable :
            version: Version :
            args: Namespace :
            dry_run: bool :

        Returns:
        --------

        """
        pre_call_ctx: PreHookContext = PreHookContext(
            self.__vcs_provider, version
        )
        for hook in self.__hooks:
            hook.pre_action_hook(pre_call_ctx, args)

        old_version = version
        version = executor.run(dry_run)

        post_call_ctx: PostHookContext = PostHookContext(
            self.__vcs_provider,
            self.__hunk_source,
            version,
            old_version == version,
        )
        for hook in self.__hooks:
            hook.post_action_hook(post_call_ctx, args)

    def register(self, hook: Hook) -> None:
        """

        Parameters:
        -----------
            hook: Hook :

        Returns:
        --------

        """
        self.__hooks.append(hook)


class CommitChanges(Hook):
    """"""

    __default_commit_message: str = (
        "chore: Bump version to {version}\n\n"
        "Created a commit with a new version"
    )

    def post_action_hook(
        self, context: PostHookContext, args: Namespace
    ) -> None:
        """

        Parameters:
        -----------
            context: PostHookContext :
            args: Namespace :

        Returns:
        --------

        """
        if not context.version_changed:
            return
        kwargs = vars(args)
        if kwargs.pop("commit", False) and not kwargs.pop("dry_run", False):
            message: str = kwargs.pop(
                "commit_message", CommitChanges.__default_commit_message
            )
            message = message.format(version=context.formatted_version)
            context.vcs_provider.check_in_deltas(message, context.hunk_source)

    def pre_action_hook(
        self, context: PreHookContext, args: Namespace
    ) -> None:
        """

        Parameters:
        -----------
            context: PreHookContext :
            args: Namespace :

        Returns:
        --------

        """
        return

    @classmethod
    def configure(cls, parser: ArgumentParser) -> None:
        """

        Parameters:
        -----------

        parser: ArgumentParser :

        Returns:
        --------

        """
        parser.add_argument(
            "--commit",
            "-c",
            action="store_true",
            default=False,
            help="Commit changes to repository",
        )

        parser.add_argument(
            "--message",
            "-m",
            dest="commit_message",
            action="store",
            default=CommitChanges.__default_commit_message,
            help="The commit message template. May contain "
            "{version} as format identifier",
        )


class TagChanges(Hook):
    """"""

    def post_action_hook(
        self, context: PostHookContext, args: Namespace
    ) -> None:
        """

        Parameters:
        -----------

            context: PostHookContext :

            args: Namespace :

        Returns:
        --------

        """
        if not context.version_changed:
            return
        kwargs = vars(args)
        if not kwargs.pop("dry_run", False) and kwargs.pop("tag", False):
            if not context.vcs_provider.is_clean:
                raise RuntimeError(
                    "This should only take place, if "
                    "the git repository is clean"
                )
            context.vcs_provider.create_tag_from_version(
                context.version, kwargs.pop("prepend_letter_v", True)
            )

    def pre_action_hook(
        self, context: PreHookContext, args: Namespace
    ) -> None:
        """

        Parameters:
        -----------

            context: PreHookContext :

            args: Namespace :

        Returns:
        --------

        """
        kwargs = vars(args)
        if (
            not context.vcs_provider.is_clean
            and not kwargs.pop("dry_run", False)
            and kwargs.pop("tag", False)
        ):
            raise RuntimeError("Repository root is not clean")

    @classmethod
    def configure(cls, parser: ArgumentParser) -> None:
        """
        Parameters:
        -----------
            parser: ArgumentParser :

        Returns:
        --------

        """
        parser.add_argument(
            "--tag",
            "-t",
            action="store_true",
            default=False,
            help="Create a tag after modifying the current version",
        )

        parser.add_argument(
            "--no-prepend-v",
            dest="prepend_letter_v",
            action="store_false",
            default=True,
            help="Do not prepend letter v for the tag",
        )
