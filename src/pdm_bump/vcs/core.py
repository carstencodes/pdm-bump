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
from collections.abc import Iterator
from pathlib import Path
from typing import AnyStr, Callable, Final, NamedTuple, Optional, Union, cast

from ..core.version import Pep440VersionFormatter, Version
from .history import History

_Pathlike = Union[Path, AnyStr]


class _PathLikeConverter(ABC):
    """"""

    @staticmethod
    def _pathlike_to_path(path: _Pathlike) -> Path:
        """

        Parameters
        ----------
        path: _Pathlike :


        Returns
        -------

        """
        if isinstance(path, Path):
            return cast(Path, path)
        if isinstance(path, str):
            return Path(path)
        if isinstance(path, bytes):
            return Path(cast(bytes, path).decode("utf-8"))

        raise ValueError(
            f"'{path}' must be a valid path, string or bytes instance"
        )


class VcsFileSystemIdentifier(NamedTuple):
    """"""

    file_name: Optional[str]
    dir_name: Optional[str]


class VcsProvider(_PathLikeConverter, ABC):
    """"""

    def __init__(self, path: _Pathlike) -> None:
        self.__path = _PathLikeConverter._pathlike_to_path(path)

    @property
    def is_available(self) -> bool:
        """"""
        return False

    @property
    def current_path(self) -> Path:
        """"""
        return self.__path

    @property
    @abstractmethod
    def is_clean(self) -> bool:
        """"""
        raise NotImplementedError()

    @abstractmethod
    def check_in_items(self, message: str, *files: tuple[Path, ...]) -> None:
        """

        Parameters
        ----------
        message: str :

        *files: tuple[Path, ...] :


        Returns
        -------

        """
        raise NotImplementedError()

    def create_tag_from_version(
        self, version: Version, prepend_letter_v: bool = True
    ) -> None:
        """

        Parameters
        ----------
        version: Version :

        prepend_letter_v: bool :
             (Default value = True)

        Returns
        -------

        """
        version_formatted: str = Pep440VersionFormatter().format(version)
        if prepend_letter_v:
            version_formatted = "v" + version_formatted
        self.create_tag_from_string(version_formatted)

    @abstractmethod
    def create_tag_from_string(self, version_formatted: str) -> None:
        """

        Parameters
        ----------
        version_formatted: str :


        Returns
        -------

        """
        raise NotImplementedError()

    @abstractmethod
    def get_most_recent_tag(self) -> Optional[Version]:
        """"""
        raise NotImplementedError()

    @abstractmethod
    def get_number_of_changes_since_last_release(self) -> int:
        """"""
        raise NotImplementedError()

    @abstractmethod
    def get_changes_not_checked_in(self) -> int:
        """"""
        raise NotImplementedError()

    @abstractmethod
    def get_history(self, since_last_tag: bool = True) -> History:
        """"""
        raise NotImplementedError()


class VcsProviderAggregator:
    """"""

    def __init__(self, vcs_provider: VcsProvider, **kwargs) -> None:
        self.__vcs_provider: VcsProvider = vcs_provider

    @property
    def vcs_provider(self) -> VcsProvider:
        """"""
        return self.__vcs_provider


class VcsProviderFactory(_PathLikeConverter, ABC):
    """"""

    def force_create_provider(self, path: Path) -> VcsProvider:
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        return self._create_provider(path)

    @abstractmethod
    def _create_provider(self, path: Path) -> VcsProvider:
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def vcs_fs_root(self) -> Iterator[VcsFileSystemIdentifier]:
        """"""
        raise NotImplementedError()

    def find_repository_root(self, path: _Pathlike) -> Optional[VcsProvider]:
        """

        Parameters
        ----------
        path: _Pathlike :


        Returns
        -------

        """
        real_path: Path = _PathLikeConverter._pathlike_to_path(path)
        return self.find_repository_root_from_path(real_path)

    def find_repository_root_from_path(
        self, path: Path
    ) -> Optional[VcsProvider]:
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        if not path.is_dir():
            raise ValueError(f"{path} must refer to a directory.")

        cur_path: Path = path
        while len(cur_path.parts) > 1:  # First part refers to root level
            if self._is_valid_root(cur_path):
                return self._create_provider(cur_path)
            cur_path = cur_path.parent

        return None

    def _is_valid_fs_root_file(self, path: Path) -> bool:
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        return path is not None and path.exists() and path.is_file()

    def _is_valid_fs_root_dir(self, path: Path) -> bool:
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        return path is not None and path.exists() and path.is_dir()

    def _directory_exists(self, path: Path, directory_name: str) -> bool:
        """

        Parameters
        ----------
        path: Path :

        directory_name: str :


        Returns
        -------

        """
        dir_path: Path = path / directory_name
        return self._is_valid_fs_root_dir(dir_path)

    def _file_exists(self, path: Path, file_name: str) -> bool:
        """

        Parameters
        ----------
        path: Path :

        file_name: str :


        Returns
        -------

        """
        file_path: Path = path / file_name
        return self._is_valid_fs_root_file(file_path)

    def _is_valid_root(self, path: Path) -> bool:
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        is_repository_root = False
        for fs_root in self.vcs_fs_root:
            is_valid_root_by_file: bool = (
                fs_root.file_name is None
                or self._file_exists(path, fs_root.file_name)
            )
            is_valid_root_by_dir: bool = (
                fs_root.dir_name is None
                or self._directory_exists(path, fs_root.dir_name)
            )
            is_repository_root = is_repository_root or (
                is_valid_root_by_dir and is_valid_root_by_file
            )

        return is_repository_root


class VcsProviderRegistry(
    dict[str, Callable[..., VcsProviderFactory]], _PathLikeConverter
):
    """"""

    def find_repository_root(self, path: _Pathlike) -> Optional[VcsProvider]:
        """

        Parameters
        ----------
        path: _Pathlike :


        Returns
        -------

        """
        real_path: Path = _PathLikeConverter._pathlike_to_path(path)
        return self.find_repository_root_by_path(real_path)

    def find_repository_root_by_path(
        self, path: Path
    ) -> Optional[VcsProvider]:
        """

        Parameters
        ----------
        path: Path :


        Returns
        -------

        """
        for _, value in self.items():
            factory: VcsProviderFactory = value()
            result: Optional[
                VcsProvider
            ] = factory.find_repository_root_from_path(path)
            if result is not None:
                return result

        return None

    def register(self, name: str) -> Callable:
        """

        Parameters
        ----------
        name: str :


        Returns
        -------

        """

        def decorator(clazz: type[VcsProvider]):
            """

            Parameters
            ----------
            clazz: type[VcsProvider] :


            Returns
            -------

            """
            if not issubclass(clazz, VcsProviderFactory):
                raise ValueError(
                    f"{clazz.__name__} is not an sub-type of "
                    f"{VcsProviderFactory.__name__}"
                )

            self[name] = clazz

        return decorator

    def __missing__(
        self, key: str
    ) -> Optional[Callable[..., VcsProviderFactory]]:
        return None


vcs_providers: Final[VcsProviderRegistry] = VcsProviderRegistry()

vcs_provider: Final[Callable[[str], Callable]] = vcs_providers.register


class DefaultVcsProvider(VcsProvider):
    """"""

    @property
    def is_available(self) -> bool:
        """"""
        return True

    @property
    def is_clean(self) -> bool:
        """"""
        return True

    def check_in_items(self, message: str, *files: tuple[Path, ...]) -> None:
        """

        Parameters
        ----------
        message: str :

        *files: tuple[Path, ...] :


        Returns
        -------

        """
        # Must not be provided
        pass

    def create_tag_from_string(self, version_formatted: str) -> None:
        """

        Parameters
        ----------
        version_formatted: str :


        Returns
        -------

        """
        # Must not be provided
        pass

    def get_most_recent_tag(self) -> Optional[Version]:
        """"""
        # Cannot be provided
        return None

    def get_number_of_changes_since_last_release(self) -> int:
        """"""
        # Cannot be provided
        return 0

    def get_changes_not_checked_in(self) -> int:
        """"""
        # Cannot be provided
        return 0

    def get_history(self, since_last_tag: bool = True) -> History:
        return History([])


class VcsProviderError(Exception):
    """"""

    pass
