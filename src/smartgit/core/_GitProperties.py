""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_GitProperties.py                                                                                 """
""" Base class to manage Git-related properties                                                                      """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from pathlib import Path
from typing import *

from smartgit.utils import *

# Logger instance
LOGGER = getSmartLogger()


class GitProperties:
    def __init__(
            self,
            inGitRoot: Optional[str | os.PathLike[str] | Path] = None,
            inGitCloneRemoteURLPrefix: Optional[str] = None,
    ):
        """
        Initializes Git properties
        - GIT_ROOT
        - GIT_CLONE_REMOTE_URL_PREFIX

        Args:
            inGitRoot (Optional[Path]):
                Base directory for cloning repositories.
                    1. Recognizes inGitRoot if provided
                    2. Fallbacks to env.GIT_ROOT
                    3. Current working directory is the last resort

            inGitCloneRemoteURLPrefix (Optional[str]):
                Base URL for remote repositories.
                    1. Recognizes inRemoteURLPrefix if provided
                    2. Fallbacks to env.GIT_CLONE_REMOTE_URL_PREFIX
        """
        self.__mGitRoot: Path = Path(
            validateEnvVariable('GIT_ROOT', inFallbackValue=os.getcwd(), inLogger=LOGGER)
        ) if isNoneOrEmpty(inGitRoot) else convertToPath(inGitRoot)
        self.__mGitRoot.resolve()

        self.__mGitCloneRemoteURLPrefix: str = (
            validateEnvVariable('GIT_CLONE_REMOTE_URL_PREFIX', inLogger=LOGGER)
            if isNoneOrEmpty(inGitCloneRemoteURLPrefix) else inGitCloneRemoteURLPrefix.strip()
        )

        if isNoneOrEmpty(self.__mGitCloneRemoteURLPrefix):
            LOGGER.warning(
                'Property:GIT_CLONE_REMOTE_URL_PREFIX is not set via parameter or environment variable. '
                'Clone operations may fail without a valid remote URL prefix.'
            )

    @property
    def GitRoot(self) -> Path:
        return self.__mGitRoot

    @property
    def GitCloneRemoteURLPrefix(self) -> Optional[str]:
        return self.__mGitCloneRemoteURLPrefix

    def make_repo_path(self, inRepoPath: str | os.PathLike[str] | Path) -> Path:
        """
        Constructs the repository path `GitRoot/InRepoPath` if inRepoPath is relative, else returns the path as is.

        :param inRepoPath: Repository path (relative or absolute) in string, PathLike or Path representation
        """
        if isNoneOrEmpty(inRepoPath):
            raise ValueError(f'{inRepoPath=} cannot be None or Empty')

        repoPath = convertToPath(inRepoPath)
        repoPath = repoPath if repoPath.is_absolute() else self.GitRoot / repoPath

        return repoPath.resolve()
