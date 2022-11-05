# pdm-bump

![PyPI](https://img.shields.io/pypi/v/pdm-bump?logo=python&logoColor=%23cccccc)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)

A small PEP440 compliant bump utility for the [Python development master](https://pdm.fming.dev/)

## Why ?

As of PEP621, the pyproject.toml supports project metadata including a project version. If you are using the PDM build backend (according to PEP517), you can also use a file provider that contains your version, which is often referred to as `dynamic` versions.

The project version itself must comply to PEP440, which tells us, that it must consist of

* an optional epoch
* a mandatory major version part
* a mandatory minor version part
* a mandatory micro version part
* an optional pre-release part supporting alpha, beta or release-candidate part.

Tools like bumpversion or bump2version use their own configuration an their own configuration and might not consider the PEP440 specifications.

## Installation

You can install it using either pip (`pip install [--user] pdm-bump`) or using the pdm cli (`pdm plugin add [--pip-args=--user] pdm-bump`).

## Usage

You can use it the following way:

```shell
$ grep version= pyproject.toml
version=0.1.0
$ pdm bump pre-release --pre alpha # creates 0.1.1a1
$ pdm bump pre-release --pre beta # creates 0.1.1.b1
$ pdm bump pre-release --pre release-candidate # creates 0.1.1rc1
$ pdm bump no-pre-release # creates 0.1.1
$ pdm bump micro # creates 0.1.2
$ pdm bump minor # creates 0.2.0
$ pdm bump major # creates 1.0.0
```

## VCS based actions

**NOTE**: Currently, only `git` is supported as VCS provider.

You can create tags based on your `pyproject.toml` version (or dynamic version) using the following command.

```shell
$ pdm bump tag # Creates a git tag with a leading v
```

## Contributing

Feel free to submit issues and pull requests. Contributions are welcome.

## Pre-checks

1. Tests: To run the tests for your current checks, run `pdm run pytest`.
2. Tox: If you are using `pyenv` you can use `pdm run tox` to run the tests for all supported python versions.
3. Code-Style: You can use `pdm check-style` to check code format.
4. Format: You can use `pdm format` to format your code.
5. Commit messages: You can run `pdm check-commits` to run `gitlint` across your commit messages.

Before opening a Pull Request, make sure, that the quality gates should succeed.
