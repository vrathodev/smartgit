""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_SmartGit.py                                                                                      """
""" Enhanced Git functionality with repository management capabilities                                               """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from typing import *

from git import Git
from git.exc import InvalidGitRepositoryError

from smartgit._GitProperties import GitProperties
from smartgit._SmartRepo import SmartRepo
from smartgit.utils_internal._GenUtility import isNoneOrEmpty, createDir
from smartgit.utils_internal._LoggingConfig import getSmartLogger

# Logger instance
LOGGER = getSmartLogger()


class SmartGit(GitProperties, Git):
    def __init__(
            self,
            inGitRoot: Optional[str] = None,
            inGitCloneRemoteURLPrefix: Optional[str] = None,
    ):
        """
        Initialize SmartGit with root directory and remote URL prefix.

        Args:
            inGitRoot (Optional[str]):
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

        self.__mRepos: Set[SmartRepo] = self.__init_repos()
        LOGGER.debug(f'Initialized SmartGit at {self.GitRoot} with {len(self.repositories)} repositories')

    @property
    def repositories(self) -> FrozenSet[SmartRepo]:
        return frozenset(self.__mRepos)

    def clone(
            self, inRepoName: str, inBranch: str = 'main', initSubmodules: bool = False
    ) -> SmartRepo:
        """
        Clone a repository from the configured remote URL prefix.

        :param inRepoName:          Name of the repository to clone
        :param inBranch:            Branch to check out after cloning. (optional) Defaults to 'main'
        :param initSubmodules:      Whether to initialize submodules after cloning. (optional) Defaults to False
        :return: GitPython Repo instance for the cloned repository
        :raises Exception: If clone operation fails
        """
        LOGGER.entrance('SmartGit.clone')

        assert not isNoneOrEmpty(self.GitCloneRemoteURLPrefix)
        repo: SmartRepo = SmartGit.clone_from(
            inRepoName,
            self.GitRoot,
            self.GitCloneRemoteURLPrefix,
            inBranch,
            initSubmodules,
        )
        self.__mRepos.add(repo)
        return repo

    def __init_repos(self) -> Set[SmartRepo]:
        """
        Initializes the local repositories under the GIT_ROOT directory.
        """
        repos: Set[SmartRepo] = set()

        for repoName in os.listdir(self.GitRoot):
            repoPath = os.path.join(self.GitRoot, repoName)

            try:
                repos.add(SmartRepo(repoPath))
                LOGGER.debug('Found repository: %s', repoPath)
            except InvalidGitRepositoryError:
                LOGGER.warning('Invalid Git repository at: %s', repoPath)
                continue

        return repos

    @classmethod
    def clone_from(
            cls,
            inRepoName: str,
            inDestinationPath: str,
            inRemoteURLPrefix: str,
            inBranch: str = 'main',
            initSubmodules: bool = False,
    ) -> SmartRepo:
        """
        Clone a repository from the given remote URL prefix.

        :param inRepoName:          Name of the repository to clone
        :param inDestinationPath:   Local path where repo will be cloned before inRepoName appending.
        :param inRemoteURLPrefix:   Remote URL prefix to use for cloning.
        :param inBranch:            Branch to check out after cloning. (optional) Defaults to 'main'
        :param initSubmodules:      Whether to initialize submodules after cloning. (optional) Defaults to False
        :return: GitPython Repo instance for the cloned repository
        :raises Exception: If clone operation fails
        """
        LOGGER.entrance('SmartGit::clone_from')

        if any(
                isNoneOrEmpty(param)
                for param in [inRepoName, inDestinationPath, inRemoteURLPrefix, inBranch]
        ):
            raise ValueError('ERROR: Required param can not be None or empty')

        inRepoName = inRepoName.strip()
        inBranch = inBranch.strip()
        inDestinationPath = inDestinationPath.strip()
        inRemoteURLPrefix = inRemoteURLPrefix.strip()

        createDir(inDestinationPath)

        repoPath: str = os.path.join(inDestinationPath, inRepoName)
        if SmartRepo.is_valid(repoPath):
            repo = SmartRepo(repoPath)
            LOGGER.info(f'`{repoPath}` already exists. Skipping clone...')
        else:
            repo = SmartRepo.clone_from(
                url=f'{inRemoteURLPrefix}/{inRepoName}.git',
                to_path=os.path.join(inDestinationPath, inRepoName),
            )
            LOGGER.info(f'Cloned `{repoPath}` successfully')

        repo.git.execute(['git', 'checkout', inBranch])
        if initSubmodules:
            repo.git.execute(['git', 'submodule', 'update', '--init', '--recursive'])

        return repo
