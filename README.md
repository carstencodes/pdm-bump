# pdm-bump

![PyPI](https://img.shields.io/pypi/v/pdm-bump?logo=python&logoColor=%23cccccc)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)

A small PEP440 compliant bump utility for PDM, the [Python Development Master](https://pdm-project.org/).

## Why?

As of PEP621, the pyproject.toml supports project metadata including a project version. If you are using the PDM build backend (according to PEP517), you can also use a file provider that contains your version, which is often referred to as a `dynamic` version.

The project version itself must comply to PEP440, which tells us, that it must consist of

* an optional epoch
* a mandatory major version part
* a mandatory minor version part
* a mandatory micro version part
* an optional pre-release part supporting alpha, beta or release-candidate part.

Tools like `bumpversion` or `bump2version` use their own configuration and might not conform to the PEP440 specification.

## Installation

You can install it using either pip (`pip install [--user] pdm-bump`) or using the PDM CLI (`pdm self add [--pip-args=--user] pdm-bump`).

## Usage

You can use it the following way:

```shell
$ grep version= pyproject.toml
version=0.1.0
$ pdm bump pre-release --pre alpha # creates 0.1.1a1 from 0.1.0
$ pdm bump pre-release --pre beta # creates 0.1.1.b1 from 0.1.1a1
$ pdm bump pre-release --pre release-candidate # creates 0.1.1rc1 from 0.1.1b1
$ pdm bump no-pre-release # creates 0.1.1 from 0.1.1rc1
$ pdm bump micro # creates 0.1.2 from 0.1.1
$ pdm bump minor # creates 0.2.0 from 0.1.2
$ pdm bump major # creates 1.0.0 from 0.2.0
```

### Migrating from `poetry`

If you used to work with `poetry`, the `pdm` `bump` plugin will actually include all the commands
that you are used to work with in the `poetry` `version` [command](https://python-poetry.org/docs/cli/#version).

So you can actually use the following commands in the same way:

| `poetry version` | `pdm bump`       | Remarks                                        |
| ---------------- | ---------------- | ---------------------------------------------- |
| `major`          | `major`          | No 1:1 implementation, but compatible behavior |
| `minor`          | `minor`          | No 1:1 implementation, but compatible behavior |
| `patch`          | `patch`, `micro` | No 1:1 implementation, but compatible behavior |
| `premajor`       | `premajor`       | Implemented according to poetry documentation  |
| `preminor`       | `preminor`       | Implemented according to poetry documentation  |
| `prepatch`       | `prepatch`       | Implemented according to poetry documentation  |
| `prerelease`     | `prerelease`     | Implemented according to poetry documentation  |

Hence, replacing `poetry version` with `pdm bump` should be sufficient with pdm-bump v0.8.0 onwards.

## VCS based actions

**NOTE**: Currently, only `git` is supported as VCS provider. It requires git(.exe) to be available on your `PATH`.
Hence the configuration key `git-cli`.

You can create tags based on your `pyproject.toml` version (or dynamic version) using the following command.

```shell
$ pdm bump tag # creates a git tag with a leading v
```

### Semantic versioning and conventional commits

If you are using [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/), `pdm bump` can analyze your
commit history up to the most recent tag. This history will be categorized upon the commit subjects, i.e. the first
line of the commit. These categorized commits will then be handed over to a policy that will suggest a new version.

Currently, an approach for a [semantic version v2](https://semver.org/spec/v2.0.0.html) is implemented.

The implementation is as follows:
- Features, Performance Tweaks and Refactorings will trigger a minor upgrade
- Chore, Documentation and Bugfixes will trigger a micro (or patch) upgrade
- Any other commit will trigger a post upgrade
- Breaking changes will trigger a major upgrade

The highest rating will win.

```shell
$ grep version= pyproject.toml
version=0.1.0
$ git log $(git describe --tags --abbrev=0)..HEAD --format=%s
fix: Formatting is erroneous
$ pdm bump suggest
Would suggest a new version of 0.1.1
$ # some more commits
$ git log $(git describe --tags --abbrev=0)..HEAD --format=%s
fix: Formatting is erroneous
build: corrected PDM scripts
chore: Updated 3 dependencies
$ pdm bump suggest
Would suggest a new version of 0.1.1
$ # some more commits
$ git log $(git describe --tags --abbrev=0)..HEAD --format=%s
fix: Formatting is erroneous
build: corrected PDM scripts
chore: Updated 3 dependencies
feat: Added a new formatter
$ pdm bump suggest
Would suggest a new version of 0.2.0
$
```

If you agree with it, you can use `pdm bump auto` to set the new version. Add parameter `-c` to create a commit of
your version file automatically.

## Configuration

In your `pdm.toml`, you can add the following configuration values:

### Table plugins.bump

| Name           | Type | Description                                                 | ENV_VAR                       | CLI Parameter                                 | Default Value |
|----------------|------|-------------------------------------------------------------|-------------------------------|-----------------------------------------------|---------------|
| commit_msg_tpl | str  | The default commit message. Uses templates 'from' and 'to'. |                               | -m, --message                                 | _cf. below_   |
| perform_commit | bool | If set to true, commit the bumped changes automatically     |                               | -c, --commit                                  | False         |
| auto_tag       | bool | Create a tag after bumping and committing the changes       |                               | -t, --tag                                     | False         |
| tag_add_prefix | bool | Adds the prefix v to the version tag                        |                               | --no-prepend-v (Note: This inverts the logic) | True          |
| allow_dirty    | bool | Allows tagging the project, if it is dirty                  |                               | -d, --dirty                                   | False         |
| provider       | str  | "Configures the VCS Provider to use.                        | PDM_PLUGINS_BUMP_VCS_PROVIDER |                                               | git-cli       |

The default commit message template is set to:

```txt
chore: Bump version {from} to {to}

Created a commit with a new version {to}.
Previous version was {from}.
```

You can only use the variables `from` representing the previous version and `to`
representing the new version.

## Contributing

Feel free to submit issues and pull requests. Contributions are welcome.

## Pre-checks

1. Tests: To run the tests for your current checks, run `pdm run pytest`.
2. tox: If you are using `pyenv` you can use `pdm run tox` to run the tests for all supported Python versions.
3. Code Style: You can use `pdm check-style` to check code format.
4. Format: You can use `pdm format` to format your code.
5. Commit messages: You can run `pdm check-commits` to run `gitlint` on your commit messages.

Before opening a Pull Request make sure that the quality gates are passed.
