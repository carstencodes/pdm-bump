#
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    AnyStr,
    Callable,
    Dict,
    Final,
    Iterator,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

from ..version import Pep440VersionFormatter, Version

_Pathlike = Union[Path, AnyStr]


class _PathLikeConverter(ABC):
    @staticmethod
    def _pathlike_to_path(path: _Pathlike) -> Path:
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
    file_name: Optional[str]
    dir_name: Optional[str]


class VcsProvider(_PathLikeConverter, ABC):
    def __init__(self, path: _Pathlike) -> None:
        self.__path = _PathLikeConverter._pathlike_to_path(path)

    @property
    def is_available(self) -> bool:
        return False

    @property
    def current_path(self) -> Path:
        return self.__path

    @property
    @abstractmethod
    def is_clean(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def check_in_items(self, message: str, *files: Tuple[Path, ...]) -> None:
        raise NotImplementedError()

    def create_tag_from_version(
        self, version: Version, prepend_letter_v: bool = True
    ) -> None:
        version_formatted: str = Pep440VersionFormatter().format(version)
        if prepend_letter_v:
            version_formatted = "v" + version_formatted
        self.create_tag_from_string(version_formatted)

    @abstractmethod
    def create_tag_from_string(self, version_formatted: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_most_recent_tag(self) -> Optional[Version]:
        raise NotImplementedError()

    @abstractmethod
    def get_number_of_changes_since_last_release(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def get_changes_not_checked_in(self) -> int:
        raise NotImplementedError()


class VcsProviderFactory(_PathLikeConverter, ABC):
    def force_create_provider(self, path: Path) -> VcsProvider:
        return self._create_provider(path)

    @abstractmethod
    def _create_provider(self, path: Path) -> VcsProvider:
        raise NotImplementedError()

    @property
    @abstractmethod
    def vcs_fs_root(self) -> Iterator[VcsFileSystemIdentifier]:
        raise NotImplementedError()

    def find_repository_root(self, path: _Pathlike) -> Optional[VcsProvider]:
        real_path: Path = _PathLikeConverter._pathlike_to_path(path)
        return self.find_repository_root_from_path(real_path)

    def find_repository_root_from_path(
        self, path: Path
    ) -> Optional[VcsProvider]:
        if not path.is_dir():
            raise ValueError(f"{path} must refer to a directory.")

        cur_path: Path = path
        while len(cur_path.parts) > 1:  # First part refers to root level
            if self._is_valid_root(cur_path):
                return self._create_provider(cur_path)
            cur_path = cur_path.parent

        return None

    def _is_valid_fs_root_file(self, path: Path) -> bool:
        return path is not None and path.exists() and path.is_file()

    def _is_valid_fs_root_dir(self, path: Path) -> bool:
        return path is not None and path.exists() and path.is_dir()

    def _directory_exists(self, path: Path, directory_name: str) -> bool:
        dir_path: Path = path / directory_name
        return self._is_valid_fs_root_dir(dir_path)

    def _file_exists(self, path: Path, file_name: str) -> bool:
        file_path: Path = path / file_name
        return self._is_valid_fs_root_file(file_path)

    def _is_valid_root(self, path: Path) -> bool:
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
    Dict[str, Callable[..., VcsProviderFactory]], _PathLikeConverter
):
    def find_repository_root(self, path: _Pathlike) -> Optional[VcsProvider]:
        real_path: Path = _PathLikeConverter._pathlike_to_path(path)
        return self.find_repository_root_by_path(real_path)

    def find_repository_root_by_path(
        self, path: Path
    ) -> Optional[VcsProvider]:
        for _, value in self.items():
            factory: VcsProviderFactory = value()
            result: Optional[
                VcsProvider
            ] = factory.find_repository_root_from_path(path)
            if result is not None:
                return result

        return None

    def register(self, name: str) -> Callable:
        def decorator(clazz: Type[VcsProvider]):
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
    @property
    def is_available(self) -> bool:
        return True

    @property
    def is_clean(self) -> bool:
        return True

    def check_in_items(self, message: str, *files: Tuple[Path, ...]) -> None:
        # Must not be provided
        pass

    def create_tag_from_string(self, version_formatted: str) -> None:
        # Must not be provided
        pass

    def get_most_recent_tag(self) -> Optional[Version]:
        # Cannot be provided
        return None

    def get_number_of_changes_since_last_release(self) -> int:
        # Cannot be provided
        return 0

    def get_changes_not_checked_in(self) -> int:
        # Cannot be provided
        return 0


class VcsProviderError(Exception):
    pass
