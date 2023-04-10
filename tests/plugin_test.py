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

from unittest import TestCase
from typing import Optional
from collections.abc import Iterable
from argparse import ArgumentParser, Namespace, ArgumentError

from pdm.project.config import ConfigItem
from pdm.cli.commands.base import BaseCommand

from pdm_bump.cli import main
from pdm_bump.plugin import BumpCommand


_registered_configurations: dict[str, ConfigItem] = {}


class _CoreStub:
    registered_command: Optional[type[BaseCommand]] = None
    registered_name: Optional[str] = None

    def register_command(
        self, command: type[BaseCommand], name: Optional[str] = None
    ) -> None:
        self.registered_command = command
        self.registered_name = name

    @staticmethod
    def add_config(name: str, config_item: ConfigItem) -> None:
        _registered_configurations[str] = config_item


class CliRegistrationTest(TestCase):
    def tearDown(self) -> None:
        _registered_configurations.clear()

    def test_registration_command_type(self) -> None:
        core: _CoreStub = _CoreStub()
        main(core)
        self.assertEqual(
            core.registered_command,
            BumpCommand,
            "The command is registered correctly",
        )

    def test_registration_command_name(self) -> None:
        core: _CoreStub = _CoreStub()
        main(core)
        self.assertIsNone(core.registered_name, "No name has been supplied")

    def test_registered_config_items(self) -> None:
        core: _CoreStub = _CoreStub()
        main(core)
        self.assertTrue(
            len(_registered_configurations) == 0,
            "No config item has been registered",
        )


class BumpVersionCommandParserTests(TestCase):
    SUB_TEST_PARAMS_WHAT_SUCCESS: Iterable[tuple[str, str]] = [
        ("major", "major"),
        ("minor", "minor"),
        ("micro", "micro"),
        ("patch", "patch"),
        ("pre-release", "pre-release"),
        ("no-pre-release", "no-pre-release"),
        ("post", "post"),
        ("dev", "dev"),
    ]
    SUB_TEST_PARAMS_PRE_SUCCESS: Iterable[tuple[str, str]] = [
        ("alpha", "alpha"),
        ("beta", "beta"),
        ("c", "c"),
        ("rc", "rc"),
    ]
    SUB_TEST_PARAMS_FAIL: Iterable[tuple[str, list[str]]] = [
        ("major", ["maj"]),
        ("minor", ["min"]),
        ("micro", ["mic"]),
        ("patch", ["pa"]),
        ("pre-release", ["pre"]),
        ("no-pre-release", ["no-pre"]),
        ("alpha", ["pre-release", "--pre", "a"]),
        ("beta", ["pre-release", "--pre", "b"]),
        ("c", ["pre-release", "--pre", "release"]),
        ("rc", ["pre-release", "--pre", "release-candidate"]),
    ]

    def test_parser_setup_what_success(self) -> None:
        parser: ArgumentParser = ArgumentParser()
        _ = BumpCommand(parser)

        for msg, what_success in self.SUB_TEST_PARAMS_WHAT_SUCCESS:
            with self.subTest(msg, what=what_success):
                options: Namespace = parser.parse_args([what_success])
                self.assertEqual(
                    options.selected_command,
                    what_success,
                    "The first item is only matched",
                )

    def test_parser_setup_pre_success(self) -> None:
        parser: ArgumentParser = ArgumentParser()
        _ = BumpCommand(parser)

        for msg, pre_success in self.SUB_TEST_PARAMS_PRE_SUCCESS:
            with self.subTest(msg, pre=pre_success):
                options: Namespace = parser.parse_args(
                    ["pre-release", "--pre", pre_success]
                )
                self.assertEqual(
                    options.pre_release_part, pre_success, "The second item is only matched"
                )

    def test_parser_setup_fail(self) -> None:
        parser: ArgumentParser = ArgumentParser(exit_on_error=False)
        _ = BumpCommand(parser)

        for msg, options in self.SUB_TEST_PARAMS_FAIL:
            with self.subTest(msg, options=options):
                call = lambda options=options: parser.parse_args(options)
                self.assertRaises(ArgumentError, call)
