from abc import abstractmethod
from pathlib import Path
from .core import VcsProviderFactory, VcsFileSystemIdentifier

class GitCommonVcsProviderFactory(VcsProviderFactory):
    __git_provider = VcsFileSystemIdentifier(file_name=None, dir_name=".git")
    
    @abstractmethod
    def _create_provider(self, path: Path) -> VcsProvider:
        raise NotImplementedError()
    
    @property()
    def vcs_fs_root(self) -> VcsFileSystemIdentifier:
        return self.__git_provider
