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
from argparse import ArgumentParser, Namespace
from typing import Callable, Protocol

from ..core.logging import logger
from ..core.version import Pep440VersionFormatter, Version

_formatter = Pep440VersionFormatter()


class _HasAddSubParser(Protocol):
    def add_parser(self, name, **kwargs) -> ArgumentParser:
        raise NotImplementedError()


class VersionPersister(Protocol):
    def save_version(self, version: Version) -> None:
        raise NotImplementedError()


class ActionBase(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, dry_run: bool = False) -> None:
        raise NotImplementedError()

    @classmethod
    def create_from_command(cls, args: Namespace, **kwargs) -> "ActionBase":
        command_line: dict = vars(args)
        kwargs.update(command_line)
        instance: "ActionBase" = cls(**kwargs)

        return instance

    @classmethod
    def _update_command(cls, sub_parser: ArgumentParser) -> None:
        # Must be implemented if necessary
        pass

    @classmethod
    def create_command(
        cls, sub_parser_collection: _HasAddSubParser, **kwargs
    ) -> ArgumentParser:
        aliases: list[str] = []

        if "aliases" in vars(cls):
            aliases = list(cls.aliases)

        exit_on_error = True
        if "exit_on_error" in kwargs:
            exit_on_error = bool(kwargs.pop("exit_on_error"))

        parser = sub_parser_collection.add_parser(
            cls.name, description=cls.description, aliases=aliases, exit_on_error=exit_on_error
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


class VersionModifier(ActionBase):
    def __init__(self, version: Version, persister: VersionPersister) -> None:
        self.__version = version
        self.__persister = persister

    @property
    def current_version(self) -> Version:
        return self.__version

    @abstractmethod
    def create_new_version(self) -> Version:
        raise NotImplementedError()

    def _report_new_version(self, next_version: Version) -> None:
        logger.info(
            "Performing increment of version: %s -> %s",
            _formatter.format(self.current_version),
            _formatter.format(next_version),
        )

    def run(self, dry_run: bool = False) -> None:
        next_version: Version = self.create_new_version()
        if not dry_run:
            self.__persister.save_version(next_version)
        else:
            logger.info("Would write new version %s", next_version)


class ActionRegistry:
    def __init__(self) -> None:
        self.__items: dict[str, type[ActionBase]] = dict()

    def register(self) -> Callable:
        def decorator(clazz: type[ActionBase]):
            if not issubclass(clazz, ActionBase):
                raise ValueError(
                    f"{clazz.__name__} is not an sub-type of "
                    f"{ActionBase.__name__}"
                )
            self.__items[clazz.name] = clazz

        return decorator

    def update_parser(self, parser: ArgumentParser) -> None:
        parsers: _HasAddSubParser = parser.add_subparsers(
            dest="selected_command",
            description="Either the part of the version to bump according to PEP 440:"
            + " major.minor.micro, "
            + "or VCS based actions to take.",
            required=True,
        )
        parser.add_help = True
        keys = list(self.__items.keys())
        keys.sort()
        for key in keys:
            clazz = self.__items[key]
            clazz.create_command(parsers, exit_on_error = parser.exit_on_error)

    def execute(
        self, args: Namespace, version: Version, persister: VersionPersister
    ) -> None:
        kwargs: dict = {}

        kwargs["version"] = version

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
                f"Failed to get command {selected_command}. Valid values are {', '.join(self.__items.keys())}."
            )

        clazz: type[ActionBase] = self.__items[selected_command]

        if issubclass(clazz, VersionModifier):
            kwargs["persister"] = persister

        command: "ActionBase" = clazz.create_from_command(args, **kwargs)
        command.run(dry_run=dry_run)


actions = ActionRegistry()
action = actions.register()