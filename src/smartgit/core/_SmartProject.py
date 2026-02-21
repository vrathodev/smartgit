""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_SmartProject.py                                                                                  """
""" Contains the definition of SmartProject class and related APIs                                                   """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from os import PathLike
from pathlib import Path
from typing import *

from smartgit.core._GitProperties import GitProperties
from smartgit.core._SmartRepo import SmartRepo
from smartgit.utils import *

# Logger instance
LOGGER = getSmartLogger()


class SmartProject(GitProperties):
    """
    SmartProject -- A logical grouping of multiple related Git repositories
    """

    def __init__(
            self,
            inRepos: Optional[List[str | PathLike[str] | Path | SmartRepo]] = None,
            inProjectRoot: Optional[str | PathLike[str] | Path] = None,
            inCloneRemoteURLPrefix: Optional[str] = None
    ):
        """
        Initializes SmartProject with given repositories
        If no repositories are provided, initializes with all the repositories detected under the project root.

        :param inRepos:                     List of repositories names, paths or instances (optional)
        :param inProjectRoot:               Base directory for the project repositories (optional)
        :param inCloneRemoteURLPrefix:      Base URL for remote repositories (optional)
        """
        GitProperties.__init__(self, inProjectRoot, inCloneRemoteURLPrefix)
        self.__mRepos: Set[SmartRepo] = set()

        if isNoneOrEmpty(inRepos):
            LOGGER.info(f'No repositories provided; scanning `{self.GitRoot}` to detect repositories from')
        else:
            self.__mRepos.update(inRepos)

    @property
    def repositories(self) -> FrozenSet[SmartRepo]:
        return frozenset(self.__mRepos)

    def add_repo(self, inRepo: str | PathLike[str] | Path | SmartRepo):
        """
        Adds a repository to the project.

        :param inRepo: Repository name, path, or SmartRepo instance
        :raises InvalidGitRepositoryError: If the provided path is not a valid Git repository
        """
        if isNoneOrEmpty(inRepo):
            raise ValueError(f'{inRepo=} cannot be None or Empty')

        self.__mRepos.add(
            inRepo if isinstance(inRepo, SmartRepo) else SmartRepo(self.make_repo_path(inRepo))
        )

    def remove_repo(self, inRepo: str | PathLike[str] | Path | SmartRepo):
        """
        Removes a repository from the project.

        :param inRepo: Repository name, path, or SmartRepo instance
        """
        if isNoneOrEmpty(inRepo):
            raise ValueError(f'{inRepo=} cannot be None or Empty')

        if isinstance(inRepo, SmartRepo):
            self.__mRepos.discard(inRepo)
            return

        repoName: str = self.make_repo_path(inRepo).name
        for repo in self.__mRepos:
            if repo.name == repoName:
                self.__mRepos.discard(repo)
                break

    @classmethod
    def smart_init(
            cls,
            inRepos: List[str | PathLike[str] | Path | SmartRepo],
            inDestinationPath: str | PathLike[str] | Path,
            inRemoteURLPrefix: str,
            inBranch: str = None,
            initSubmodules: bool = False
    ) -> 'SmartProject':
        """
        Initializes a SmartProject by
            - Locating the repo at `inDestinationPath` using repo names/paths in `inRepos`
            - Cloning the repo from `inRemoteURLPrefix` if couldn't be located
            - Simply adding the SmartRepo to the project if already a SmartRepo instance

        :param inRepos:             List of repository names/paths or SmartRepo instances
        :param inDestinationPath:   Base directory to locate or clone the given repository
        :param inRemoteURLPrefix:   Remote URL prefix to use for cloning.
        :param inBranch:            Branch to check out (optional)
                                    Defaults to remote and local HEAD
                                    for new and existing repositories respectively if not specified
        :param initSubmodules:      Whether to initialize submodules (optional) Defaults to False
        :raises Exception: If clone operation fails
        """
        LOGGER.entrance()

        gitProps = GitProperties(inDestinationPath, inRemoteURLPrefix)
        smartRepos: List[SmartRepo] = list()

        for repo in inRepos:
            smartRepos.append(
                repo if isinstance(repo, SmartRepo) else SmartRepo.smart_init(
                    gitProps.make_repo_path(repo).name,
                    gitProps.GitRoot,
                    gitProps.GitCloneRemoteURLPrefix,
                    inBranch,
                    initSubmodules
                )
            )

        return SmartProject(smartRepos, gitProps.GitRoot, gitProps.GitCloneRemoteURLPrefix)
