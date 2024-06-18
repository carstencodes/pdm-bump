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


import sys
from abc import abstractmethod
from dataclasses import asdict as dataclass_to_dict
from typing import TYPE_CHECKING, Any, Final, final

from pdm_pfsc.logging import logger, traced_function

from ..core.version import NonNegativeInteger, Pep440VersionFormatter, Version
from .base import VersionModifier, VersionPersister, action

if TYPE_CHECKING:
    from argparse import ArgumentParser

    if sys.version_info >= (3, 10, 0):
        # suspicious mypy behavior
        from typing import TypeAlias  # type: ignore
    else:
        from typing_extensions import TypeAlias

_formatter = Pep440VersionFormatter()


class _NonFinalPartsRemovingVersionModifier(VersionModifier):
    """"""

    def __init__(
        self,
        version: "Version",
        persister: "VersionPersister",
        remove_parts: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(version, persister, **kwargs)
        self.__remove_parts = remove_parts

    @property
    def remove_non_final_parts(self) -> bool:
        """"""
        return self.__remove_parts

    @abstractmethod
    def create_new_version(self) -> "Version":
        """"""
        raise NotImplementedError()

    @staticmethod
    def _create_new_constructional_args(
        release: "tuple[NonNegativeInteger, ...]",
        epoch: "NonNegativeInteger" = 0,
    ) -> dict[str, Any]:
        """

        Parameters
        ----------
        release: tuple[NonNegativeInteger, ...] :

        epoch: NonNegativeInteger :
             (Default value = 0)

        Returns
        -------

        """
        return {
            "epoch": epoch,
            "release_tuple": release,
            "preview": None,
            "post": None,
            "dev": None,
            "local": None,
        }

    @classmethod
    def _update_command(cls, sub_parser: "ArgumentParser") -> None:
        """

        Parameters
        ----------
        sub_parser: ArgumentParser :


        Returns
        -------

        """
        sub_parser.add_argument(
            "--no-remove",
            action="store_false",
            dest="remove_parts",
            help="When incrementing major, minor, micro or epoch, "
            + "do not remove all pre-release parts.",
        )

        VersionModifier._update_command(sub_parser)


_NFPR: "TypeAlias" = _NonFinalPartsRemovingVersionModifier


class _ReleaseVersionModifier(_NonFinalPartsRemovingVersionModifier):
    """"""

    @property
    @abstractmethod
    def release_part(self) -> "NonNegativeInteger":
        """"""
        raise NotImplementedError()

    @traced_function
    def create_new_version(self) -> "Version":
        """"""
        construction_args: "dict[str, Any]" = dataclass_to_dict(
            self.current_version
        )

        next_release: "tuple[NonNegativeInteger, ...]" = (
            self._update_release_version_part(self.release_part)
        )

        if self.remove_non_final_parts:
            logger.debug("Removing non-final parts of version")
            # Using type alias due to line length enforced by black
            construction_args = _NFPR._create_new_constructional_args(  # noqa: E501 pylint: disable=W0212
                next_release, self.current_version.epoch
            )
        else:
            construction_args["release_tuple"] = next_release

        next_version: "Version" = Version(**construction_args)
        self._report_new_version(next_version)

        return next_version

    def _update_release_version_part(
        self, part_id: "NonNegativeInteger"
    ) -> "tuple[NonNegativeInteger, ...]":
        """

        Parameters
        ----------
        part_id: NonNegativeInteger :


        Returns
        -------

        """
        release_part: "list[NonNegativeInteger]" = list(
            self.current_version.release
        )

        for i in range(len(release_part)):  # pylint: disable=C0200
            logger.debug("Checking if version part at %d must be modified", i)
            if i == part_id:
                logger.debug("Incrementing version part at position %d.", i)
                release_part[i] = release_part[i] + 1
            elif i > part_id:
                logger.debug("Resetting version part at position %d", i)
                release_part[i] = 0

        return tuple(release_part)


@final
@action
class ResetNonSemanticPartsModifier(VersionModifier):
    """"""

    name: str = "reset-locals"
    description: str = (
        "Remove all non-semantiv parts (dev, post, local) from the version"
    )

    @traced_function
    def create_new_version(self) -> "Version":
        """"""
        next_version: Version = Version(
            epoch=self.current_version.epoch,
            release_tuple=self.current_version.release_tuple,
            preview=self.current_version.preview,
        )
        self._report_new_version(next_version)

        return next_version


@final
@action
class FinalizingVersionModifier(_NonFinalPartsRemovingVersionModifier):
    """"""

    name: str = "no-pre-release"
    description: str = "Remove all pre-release parts from the version"

    def __init__(
        self, version: "Version", persister: "VersionPersister", **kwargs
    ) -> None:
        super().__init__(version, persister, **kwargs)

    @traced_function
    def create_new_version(self) -> "Version":
        """"""
        constructional_args: dict[
            str,
            Any,
            # Using type alias due to line length enforced by black
        ] = _NFPR._create_new_constructional_args(  # noqa: E501 pylint: disable=W0212
            self.current_version.release, self.current_version.epoch
        )

        next_version: Version = Version(**constructional_args)
        self._report_new_version(next_version)

        return next_version


@final
@action
class MajorIncrementingVersionModifier(_ReleaseVersionModifier):
    """"""

    name: str = "major"
    description: str = "Increment the major part of the version"

    __MAJOR_PART: "Final[NonNegativeInteger]" = 0

    @property
    def release_part(self) -> "NonNegativeInteger":
        """"""
        return self.__MAJOR_PART


@final
@action
class MinorIncrementingVersionModifier(_ReleaseVersionModifier):
    """"""

    name: str = "minor"
    description: str = "Increment the minor part of the version"

    __MINOR_PART: "Final[NonNegativeInteger]" = 1

    @property
    def release_part(self) -> "NonNegativeInteger":
        """"""
        return self.__MINOR_PART


@final
@action
class MicroIncrementingVersionModifier(_ReleaseVersionModifier):
    """"""

    name: str = "micro"
    description: str = "Increment the micro (or patch) part of the version"
    aliases: tuple[str] = ("patch",)

    __MICRO_PART: "Final[NonNegativeInteger]" = 2

    @property
    def release_part(self) -> int:
        """"""
        return self.__MICRO_PART


@final
@action
class EpochIncrementingVersionModifier(_NonFinalPartsRemovingVersionModifier):
    """"""

    name: str = "epoch"
    description: str = "Increment the epoch of the version"

    def __init__(
        self,
        version: "Version",
        persister: "VersionPersister",
        remove_parts: bool = True,
        reset_version: bool = True,
    ):
        super().__init__(version, persister, remove_parts)
        self.__reset_version = reset_version

    @traced_function
    def create_new_version(self) -> "Version":
        """"""
        constructional_args: dict[str, Any] = dataclass_to_dict(
            self.current_version
        )

        if self.__reset_version or self.remove_non_final_parts:
            constructional_args = dataclass_to_dict(Version.default())
            if not self.__reset_version:
                logger.debug("Current version tuple shall not be reset")
                constructional_args["release_tuple"] = (
                    self.current_version.release
                )

        logger.debug("Incrementing Epoch of version")
        constructional_args["epoch"] = self.current_version.epoch + 1

        next_version: "Version" = Version(**constructional_args)
        self._report_new_version(next_version)
        return next_version

    @classmethod
    def _update_command(cls, sub_parser: "ArgumentParser") -> None:
        """

        Parameters
        ----------
        sub_parser: ArgumentParser :


        Returns
        -------

        """
        sub_parser.add_argument(
            "--reset",
            action="store_true",
            dest="reset_version",
            help="Reset version to 1.0.0 on epoch increment",
        )

        # Justification: Call protected method of parent class
        _NFPR._update_command(sub_parser)  # pylint: disable=W0212


@final
@action
class DevelopmentVersionIncrementingVersionModifier(VersionModifier):
    """"""

    name: str = "dev"
    description: str = "Increment the local development part"

    @traced_function
    def create_new_version(self) -> "Version":
        """"""
        dev_version: "NonNegativeInteger" = 1
        micro_version = self.current_version.micro
        pre = None
        if self.current_version.dev is not None:
            _, dev_version = self.current_version.dev
            logger.debug("Incrementing development version part by one")
            dev_version = dev_version + 1
        elif self.current_version.preview is not None:
            logger.debug("Incrementing preview version as this is a preview")
            pre = (
                self.current_version.preview[0],
                self.current_version.preview[1] + 1,
            )
        else:
            logger.debug(
                "Incrementing micro version as it is no dev version yet"
            )
            micro_version = micro_version + 1

        constructional_args: dict[str, Any] = dataclass_to_dict(
            self.current_version
        )
        constructional_args["dev"] = ("dev", dev_version)
        constructional_args["release_tuple"] = (
            self.current_version.major,
            self.current_version.minor,
            micro_version,
        )
        if pre is not None:
            constructional_args["preview"] = pre

        if (
            self.current_version.is_post_release
            and not self.current_version.is_development_version
        ):
            logger.debug("Resetting post version to zero")
            constructional_args["post"] = None

        next_version: Version = Version(**constructional_args)
        self._report_new_version(next_version)

        return next_version


@final
@action
class PostVersionIncrementingVersionModifier(VersionModifier):
    """"""

    name: str = "post"
    description: str = "Increment the post version part"

    @traced_function
    def create_new_version(self) -> "Version":
        """"""
        post_version: "NonNegativeInteger" = 1
        if self.current_version.post is not None:
            _, post_version = self.current_version.post
            logger.debug("Incrementing post version part by one")
            post_version = post_version + 1

        constructional_args: dict[str, Any] = dataclass_to_dict(
            self.current_version
        )
        constructional_args["post"] = ("post", post_version)
        if self.current_version.is_development_version:
            constructional_args["dev"] = None

        next_version: "Version" = Version(**constructional_args)
        self._report_new_version(next_version)

        return next_version
