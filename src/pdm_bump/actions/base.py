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
from typing import Any, Callable, Optional, Protocol, cast

from ..core.logging import logger
from ..core.version import Pep440VersionFormatter, Version
from ..vcs.core import VcsProvider

_formatter = Pep440VersionFormatter()


# Justification: Just a protocol
class _HasAddSubParser(Protocol):  # pylint: disable=R0903
    """"""

    def add_parser(self, name, **kwargs) -> ArgumentParser:
        """

        Parameters
        ----------
        name :

        **kwargs :


        Returns
        -------

        """
        raise NotImplementedError()


# Justification: Just a protocol
class VersionPersister(Protocol):  # pylint: disable=R0903
    """"""

    def save_version(self, version: Version) -> None:
        """

        Parameters
        ----------
        version: Version :


        Returns
        -------

        """
        raise NotImplementedError()


class _ArgumentParserFactoryMixin:
    """"""

    name: str
    description: str

    @classmethod
    def _update_command(cls, sub_parser: ArgumentParser) -> None:
        """

        Parameters
        ----------
        sub_parser: ArgumentParser :


        Returns
        -------

        """
        # Justification: Zen of Python: Explicit is better than implicit
        # Must be implemented if necessary
        pass  # pylint: disable=W0107

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return set()

    @classmethod
    def create_command(
        cls, sub_parser_collection: _HasAddSubParser, **kwargs
    ) -> ArgumentParser:
        """

        Parameters
        ----------
        sub_parser_collection: _HasAddSubParser :

        **kwargs :


        Returns
        -------

        """
        aliases: list[str] = []

        if "aliases" in vars(cls):
            aliases = list(getattr(cls, "aliases"))

        exit_on_error = True
        if "exit_on_error" in kwargs:
            exit_on_error = bool(kwargs.pop("exit_on_error"))

        parser = sub_parser_collection.add_parser(
            cls.name,
            description=cls.description,
            aliases=aliases,
            exit_on_error=exit_on_error,
        )

        parser.add_argument(
            "--dry-run",
            "-n",
            action="store_true",
            dest="dry_run",
            help="Do not perform any action, just check if it would work.",
        )

        cls._update_command(parser)

        return parser


class _BeforeRunAction:
    def before_run(self, **kwargs) -> None:
        logger.debug("Called __before_run__", extra={"kwargs": kwargs})


class _AfterRunAction:
    def after_run(self, **kwargs) -> None:
        logger.debug("Called __after_run__", extra={"kwargs": kwargs})


class ActionBase(ABC, _ArgumentParserFactoryMixin):
    """"""

    def __init__(self, **kwargs) -> None:
        # Just to ignore key word arguments
        pass

    @abstractmethod
    def run(self, dry_run: bool = False) -> None:
        """

        Parameters
        ----------
        dry_run: bool :
             (Default value = False)

        Returns
        -------

        """
        raise NotImplementedError()

    @classmethod
    def create_from_command(cls, **kwargs) -> "ActionBase":
        """

        Parameters
        ----------
        **kwargs :


        Returns
        -------

        """
        instance: "ActionBase" = cls(**kwargs)

        return instance


class VersionConsumer(ActionBase):
    """"""

    def __init__(self, version: Version, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__version = version

    @property
    def current_version(self) -> Version:
        """"""
        return self.__version

    def _overwrite_current_version(self, version: Version) -> None:
        self.__version = version

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return {"version"}.union(ActionBase.get_allowed_arguments())


class VersionModifier(VersionConsumer, _AfterRunAction, _BeforeRunAction):
    """"""

    def __init__(
        self, version: Version, persister: VersionPersister, **kwargs
    ) -> None:
        super().__init__(version, **kwargs)
        self.__persister = persister
        self.__has_new_version = False

    @abstractmethod
    def create_new_version(self) -> Version:
        """"""
        raise NotImplementedError()

    def _report_new_version(self, next_version: Version) -> None:
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

    def run(self, dry_run: bool = False) -> None:
        """

        Parameters
        ----------
        dry_run: bool :
             (Default value = False)

        Returns
        -------

        """
        next_version: Version = self.create_new_version()
        if next_version is self.current_version:
            # Intentionally removed
            return

        if not dry_run:
            self.__persister.save_version(next_version)
            self._overwrite_current_version(next_version)
        else:
            logger.info("Would write new version %s", next_version)

    @classmethod
    def get_allowed_arguments(cls) -> set[str]:
        """"""
        return {"persister"}.union(VersionConsumer.get_allowed_arguments())

    def _overwrite_current_version(self, version: Version) -> None:
        super()._overwrite_current_version(version)
        self.__has_new_version = True

    @classmethod
    def _update_command(cls, sub_parser: ArgumentParser) -> None:
        _ArgumentParserFactoryMixin._update_command(sub_parser)
        sub_parser.add_argument(
            "--tag",
            "-t",
            action="store_true",
            default=False,
            help="Create a tag after modifying the current version",
        )

        sub_parser.add_argument(
            "--no-prepend-v",
            dest="prepend_letter_v",
            action="store_false",
            default=True,
            help="Do not prepend letter v for the tag",
        )

    def after_run(self, **kwargs) -> None:
        tag: bool = kwargs.pop("tag", False)
        dry_run: bool = kwargs.pop("dry_run", True)
        if self.__has_new_version and tag and not dry_run:
            vcs_provider: Optional[VcsProvider] = kwargs.pop(
                "vcs_provider", None
            )
            if vcs_provider is None:
                raise ValueError("No VCS provider applied to this action")
            vcs_provider = cast(VcsProvider, vcs_provider)
            vcs_provider.create_tag_from_version(
                self.current_version, kwargs.pop("prepend_letter_v", True)
            )

    def __str__(self) -> str:
        return self.__class__.__name__.replace(VersionModifier.__name__, "")


class ActionRegistry:
    """"""

    def __init__(self) -> None:
        self.__items: dict[str, type[ActionBase]] = {}

    def register(self) -> Callable:
        """"""

        def decorator(clazz: type[ActionBase]):
            """

            Parameters
            ----------
            clazz: type[ActionBase] :


            Returns
            -------

            """
            if not issubclass(clazz, ActionBase):
                raise ValueError(
                    f"{clazz.__name__} is not an sub-type of "
                    f"{ActionBase.__name__}"
                )
            self.__items[clazz.name] = clazz

            return clazz

        return decorator

    def update_parser(self, parser: ArgumentParser) -> None:
        """

        Parameters
        ----------
        parser: ArgumentParser :


        Returns
        -------

        """
        parsers: _HasAddSubParser = parser.add_subparsers(  # type: ignore
            dest="selected_command",
            description="Either the part of the version to bump "
            + "according to PEP 440:"
            + " major.minor.micro, "
            + "or VCS based actions to take.",
            required=True,
        )
        parser.add_help = True
        keys = list(self.__items.keys())
        keys.sort()
        exit_on_error = False
        if "exit_on_error" in vars(parser):
            exit_on_error = getattr(parser, "exit_on_error")

        for key in keys:
            clazz = self.__items[key]
            clazz.create_command(parsers, exit_on_error=exit_on_error)

    def execute(
        self,
        /,
        args: Namespace,
        *,
        version: Version,
        persister: VersionPersister,
        vcs_provider: VcsProvider,
    ) -> None:
        """

        Parameters
        ----------
        / :

        args: Namespace :

        * :

        version: Version :

        persister: VersionPersister :

        vcs_provider: VcsProvider :


        Returns
        -------

        """
        kwargs: dict = {}

        kwargs.update(vars(args))

        kwargs = {
            key: value
            for key, value in kwargs.items()
            if not key.startswith("_")
        }

        dry_run = False
        if "dry_run" in kwargs:
            dry_run = bool(kwargs.pop("dry_run"))

        selected_command: str = kwargs.pop("selected_command")

        if selected_command not in self.__items:
            raise ValueError(
                f"Failed to get command {selected_command}. "
                + f"Valid values are {', '.join(self.__items.keys())}."
            )

        clazz: type[ActionBase] = self.__items[selected_command]

        allowed_args: set[str] = clazz.get_allowed_arguments()
        allowed_kwargs: dict[str, Any] = {
            "version": version,
            "persister": persister,
            "vcs_provider": vcs_provider,
        }

        allowed_kwargs = {
            key: value
            for key, value in allowed_kwargs.items()
            if key in allowed_args
        }

        kwargs.update(allowed_kwargs)

        command: "ActionBase" = clazz.create_from_command(**kwargs)

        hook_args: dict = {}
        hook_args.update(vars(args))
        hook_args.update({"vcs_provider": vcs_provider})

        if isinstance(command, _BeforeRunAction):
            pre_hook: _BeforeRunAction = cast(_BeforeRunAction, command)
            pre_hook.before_run(**hook_args)
        command.run(dry_run=dry_run)

        if isinstance(command, _AfterRunAction):
            post_hook: _AfterRunAction = cast(_AfterRunAction, command)
            post_hook.after_run(**hook_args)


actions = ActionRegistry()
action = actions.register()
