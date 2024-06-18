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


from abc import abstractmethod
from typing import TYPE_CHECKING

from .core import VcsFileSystemIdentifier, VcsProvider, VcsProviderFactory

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class GitCommonVcsProviderFactory(VcsProviderFactory):
    """"""

    __git_dir_provider = VcsFileSystemIdentifier(
        file_name=None, dir_name=".git"
    )
    __git_wt_file_provider = VcsFileSystemIdentifier(
        file_name=".git", dir_name=None
    )

    @abstractmethod
    def _create_provider(self, path: "Path") -> "VcsProvider":
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        raise NotImplementedError()

    @property
    def vcs_fs_root(self) -> "Iterator[VcsFileSystemIdentifier]":
        """"""
        yield self.__git_dir_provider
        yield self.__git_wt_file_provider
