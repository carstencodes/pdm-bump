# pdm-bump

![PyPI](https://img.shields.io/pypi/v/pdm-bump?logo=python&logoColor=%23cccccc)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)

A small PEP440 compliant bump utility for the [Python development master](https://pdm.fming.dev/)

## Why ?

As of PEP621, the pyproject.toml supports project metadata including a project version.

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
