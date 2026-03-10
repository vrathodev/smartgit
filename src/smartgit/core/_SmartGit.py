""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_SmartGit.py                                                                                      """
""" Enhanced Git functionality with repository management capabilities                                               """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from pathlib import Path
from typing import *

from git import Git
from git.exc import InvalidGitRepositoryError

from smartgit.core._GitProperties import GitProperties
from smartgit.core._SmartRepo import SmartRepo
from smartgit.utils import *

# Logger instance
LOGGER = getSmartLogger()


class SmartGit(GitProperties, Git):
    def __init__(
            self,
            inGitRoot: Optional[str | os.PathLike[str] | Path] = None,
            inGitCloneRemoteURLPrefix: Optional[str] = None,
    ):
        """
        Initialize SmartGit with root directory and remote URL prefix.

        Args:
            inGitRoot (Optional[str | os.PathLike[str] | Path]):
                Base directory for cloning repositories.
                    1. Recognizes inGitRoot if provided
                    2. Fallbacks to env.GIT_ROOT
                    3. Current working directory is the last resort

            inGitCloneRemoteURLPrefix (Optional[str]):
                Base URL for remote repositories.
                    1. Recognizes inRemoteURLPrefix if provided
                    2. Fallbacks to env.GIT_CLONE_REMOTE_URL_PREFIX
        """
        GitProperties.__init__(self, inGitRoot, inGitCloneRemoteURLPrefix)
        Git.__init__(self)

        self.__mRepos: Set[SmartRepo] = set(SmartGit.filter_repos(self.GitRoot))
        LOGGER.debug(f'Initialized SmartGit at {self.GitRoot} with {len(self.repositories)} repositories')

    @property
    def repositories(self) -> FrozenSet[SmartRepo]:
        return frozenset(self.__mRepos)

    def clone(self, inRepoName: str, inBranch: str = None, initSubmodules: bool = False) -> SmartRepo:
        """
        TODO: UNUSED -- Remove later?
        Clone a repository from the configured remote URL prefix.

        :param inRepoName:          Name of the repository to clone
        :param inBranch:            Branch to check out (optional)
                                    Defaults to remote and local HEAD
                                    for new and existing repositories respectively if not specified
        :param initSubmodules:      Whether to initialize submodules after cloning. (optional) Defaults to False
        :raises Exception: If clone operation fails
        """
        LOGGER.entrance()

        if isNoneOrEmpty(self.GitCloneRemoteURLPrefix):
            raise ValueError(f'GitCloneRemoteURLPrefix MUST be set to perform clone operation')

        repo: SmartRepo = SmartRepo.smart_init(
            inRepoName,
            self.GitRoot,
            self.GitCloneRemoteURLPrefix,
            inBranch,
            initSubmodules,
        )
        self.__mRepos.add(repo)
        return repo

    @classmethod
    def filter_repos(
            cls,
            inGitRoot: str | os.PathLike[str] | Path,
            inFilter: Callable[[SmartRepo], bool] = lambda x: x
    ) -> List[SmartRepo]:
        """
        Finds all the valid Git repositories under the given root directory.
        :param inGitRoot:       Root directory to search for Git repositories
        :param inFilter:        [Optional] Function to filter-out repositories
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inGitRoot):
            raise ValueError(f'{inGitRoot=} cannot be None or Empty')
        if not callable(inFilter):
            raise ValueError(f'{inFilter=} must be a callable function')

        gitRoot: Path = convertToPath(inGitRoot)
        if not (gitRoot.exists() and gitRoot.is_dir()):
            raise ValueError(f'`{inGitRoot=}` is not a valid directory path')

        repos: List[SmartRepo] = list()

        for repoName in gitRoot.iterdir():
            repoPath: Path = gitRoot / repoName

            try:
                repo = SmartRepo(repoPath)
                if not inFilter(repo):
                    LOGGER.warning(f'`{repo.name}` is filtered-out by the given filter')
                    continue
                repos.append(repo)
                LOGGER.debug(f'Found repository: {repoPath}')
            except InvalidGitRepositoryError:
                LOGGER.warning(f'Invalid Git repository {repoPath}, skipping...')
                continue

        return repos
