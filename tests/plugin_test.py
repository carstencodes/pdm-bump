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

from typing import Optional
from collections.abc import Generator, Iterable
from argparse import ArgumentParser, Namespace, ArgumentError

from pdm.project.config import ConfigItem
from pdm.cli.commands.base import BaseCommand

from pdm_bump.cli import main
from pdm_bump.plugin import BumpCommand

import pytest

parametrize = pytest.mark.parametrize
assert_raises = pytest.raises
fixture = pytest.fixture


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
        _registered_configurations[name] = config_item

@fixture
def registrations() -> Generator:
    yield
    _registered_configurations.clear()

def test_registration_command_type(registrations) -> None:
    core: _CoreStub = _CoreStub()
    main(core)
    assert core.registered_command == BumpCommand, "The command is registered correctly"

def test_registration_command_name(registrations) -> None:
    core: _CoreStub = _CoreStub()
    main(core)
    assert core.registered_name is None, "No name has been supplied"

def test_registered_config_items(registrations) -> None:
    core: _CoreStub = _CoreStub()
    main(core)
    assert len(_registered_configurations) == 6, "Six config items have been registered"


SUB_TEST_PARAMS_WHAT_SUCCESS: Iterable[tuple[str, str]] = [
    ("major", "major"),
    ("minor", "minor"),
    ("micro", "micro"),
    ("patch", "patch"),
    ("pre-release", "pre-release"),
    ("no-pre-release", "no-pre-release"),
    ("post", "post"),
    ("dev", "dev"),
    ("prerelease", "prerelease"),
    ("premajor", "premajor"),
    ("preminor", "preminor"),
    ("prepatch", "prepatch"),
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

@parametrize(",".join(["msg", "what_success"]), SUB_TEST_PARAMS_WHAT_SUCCESS)
def test_parser_setup_what_success(msg, what_success) -> None:
    parser: ArgumentParser = ArgumentParser()
    _ = BumpCommand.init_parser(parser)

    options: Namespace = parser.parse_args([what_success])

    assert options.selected_command == what_success, "The first item is only matched"

@parametrize(",".join(["msg", "pre_success"]), SUB_TEST_PARAMS_PRE_SUCCESS)
def test_parser_setup_pre_success(msg, pre_success) -> None:
    parser: ArgumentParser = ArgumentParser()
    _ = BumpCommand.init_parser(parser)

    options: Namespace = parser.parse_args(
        ["pre-release", "--pre", pre_success]
    )

    assert options.pre_release_part == pre_success, "The second item is only matched"

@parametrize(",".join(["msg", "options"]), SUB_TEST_PARAMS_FAIL)
def test_parser_setup_fail(msg, options) -> None:
    parser: ArgumentParser = ArgumentParser(exit_on_error=False)
    _ = BumpCommand.init_parser(parser)

    with assert_raises(ArgumentError):
        parser.parse_args(options)
