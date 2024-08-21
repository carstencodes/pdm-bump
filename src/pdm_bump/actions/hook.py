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

from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, ClassVar, Protocol

from pdm_pfsc.config import MissingValue
from pdm_pfsc.hook import HookBase, HookExecutorBase
from pdm_pfsc.logging import logger, traced_function

from ..core.config import (
    ALLOW_DIRTY_DEFAULT,
    AUTO_TAG_DEFAULT,
    COMMIT_MESSAGE_TEMPLATE_DEFAULT,
    PERFORM_COMMIT_DEFAULT,
    TAG_ADD_PREFIX_DEFAULT,
)
from ..core.version import Pep440VersionFormatter, Version

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from ..vcs import HunkSource, VcsProvider


class _Executable(Protocol):  # pylint: disable=R0903
    # Justification: Just a protocol
    """"""

    def run(self, dry_run: bool = False) -> "Version":
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

    vcs_provider: "VcsProvider" = field()
    version: "Version" = field()

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

    vcs_provider: "VcsProvider" = field()
    hunk_source: "HunkSource" = field()
    version: "Version" = field()
    previous_version: "Version" = field()
    version_changed: bool = field()

    @cached_property
    def formatted_version(self) -> str:
        """

        Returns:
        --------
        """
        return Pep440VersionFormatter().format(self.version)

    @cached_property
    def formatted_previous_version(self) -> str:
        """

        Returns:
        --------
        """
        return Pep440VersionFormatter().format(self.previous_version)


class HookExecutor(HookExecutorBase[tuple[_Executable, Version]]):
    """"""

    def __init__(
        self, hunk_source: "HunkSource", vcs_provider: "VcsProvider"
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
        super().__init__()

    @traced_function
    def run(
        self,
        context: "tuple[_Executable, Version]",
        args: "Namespace",
        dry_run: bool = False,
    ) -> None:
        """

        Parameters:
        -----------
            context: tuple[_Executable, Version] :
            args: Namespace :
            dry_run: bool :

        Returns:
        --------

        """
        (executor, version) = context

        pre_call_ctx: "PreHookContext" = PreHookContext(
            self.__vcs_provider, version
        )
        for hook in self._hooks:
            hook.pre_action_hook(pre_call_ctx, args)

        old_version = version
        version = executor.run(dry_run)

        post_call_ctx: "PostHookContext" = PostHookContext(
            self.__vcs_provider,
            self.__hunk_source,
            version,
            old_version,
            old_version != version,
        )
        for hook in self._hooks:
            hook.post_action_hook(post_call_ctx, args)


class CommitChanges(HookBase):
    """"""

    default_commit_message: "ClassVar[str]" = COMMIT_MESSAGE_TEMPLATE_DEFAULT
    perform_commit: "ClassVar[bool]" = PERFORM_COMMIT_DEFAULT

    @traced_function
    def post_action_hook(
        self, context: "PostHookContext", args: "Namespace"
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
            logger.debug("Cannot commit changes. Nothing to commit")
            return
        kwargs = vars(args)
        if kwargs.pop("commit", False) and not kwargs.pop("dry_run", False):
            message: str = kwargs.pop(
                "commit_message", CommitChanges.default_commit_message
            )

            f_args: dict[str, str] = {
                "to": context.formatted_version,
                "from": context.formatted_previous_version,
            }

            message = message.format(**f_args)

            context.vcs_provider.check_in_deltas(message, context.hunk_source)

    @traced_function
    def pre_action_hook(
        self, context: "PreHookContext", args: "Namespace"
    ) -> None:
        """

        Parameters:
        -----------
            context: PreHookContext :
            args: Namespace :

        Returns:
        --------

        """
        return  # NOSONAR

    @classmethod
    @traced_function
    def configure(cls, parser: "ArgumentParser") -> None:
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
            default=MissingValue(CommitChanges.perform_commit),
            help="Commit changes to repository. Uses configuration value "
            "'perform_commit' to store default action.",
        )

        parser.add_argument(
            "--message",
            "-m",
            dest="commit_message",
            action="store",
            default=MissingValue(CommitChanges.default_commit_message),
            help="The commit message template. May contain "
            "{from} and {to} as format identifier. Uses configuration value "
            "'commit_msg_tmpl' as configured default value.",
        )


class TagChanges(HookBase):
    """"""

    do_tag: "ClassVar[bool]" = AUTO_TAG_DEFAULT
    allow_dirty: "ClassVar[bool]" = ALLOW_DIRTY_DEFAULT
    prepend_to_tag: "ClassVar[bool]" = TAG_ADD_PREFIX_DEFAULT

    @traced_function
    def post_action_hook(
        self, context: "PostHookContext", args: "Namespace"
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
            if not args.dirty and not context.vcs_provider.is_clean:
                raise RuntimeError(
                    "This should only take place, if "
                    "the git repository is clean"
                )
            context.vcs_provider.create_tag_from_version(
                context.version, kwargs.pop("prepend_letter_v", True)
            )

    @traced_function
    def pre_action_hook(
        self, context: "PreHookContext", args: "Namespace"
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
    @traced_function
    def configure(cls, parser: "ArgumentParser") -> None:
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
            default=MissingValue(TagChanges.do_tag),
            help="Create a tag after modifying the current version. Uses "
            "configuration value 'auto_tag' to store its default value.",
        )

        parser.add_argument(
            "--dirty",
            "-d",
            action="store_true",
            default=MissingValue(TagChanges.allow_dirty),
            help="Create a tag, even if the repository is dirty. Uses "
            "configuration value 'allow_dirty' to store its "
            "default value.",
        )

        parser.add_argument(
            "--no-prepend-v",
            dest="prepend_letter_v",
            action="store_false",
            default=MissingValue(TagChanges.prepend_to_tag),
            help="Do not prepend letter v for the tag. Uses "
            "configuration value 'tag_add_prefix' to store its "
            "default value.",
        )
