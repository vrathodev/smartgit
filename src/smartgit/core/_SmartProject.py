""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.core._SmartProject.py                                                                             """
""" Contains the definition of SmartProject class and related APIs                                                   """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
from typing import *

from smartgit.common.constants import SG_VAL_REMOTE_NAME_DEFAULT
from smartgit.config import ConfigType
from smartgit.config import ProjectConfig, SmartGitConfig
from smartgit.core._SmartRepo import SmartRepo
from smartgit.utils import *

# Logger instance
LOGGER = getSmartLogger()


class SmartProject:
    """
    SmartProject -- A logical grouping of multiple related Git repositories

    Operates in sync and async mode for batch processing
    """

    def __init__(
        self,
        inProjectName: str,
        inProjectConfig: ProjectConfig,
    ):
        """
        Initializes the SmartProject with the ProjectConfig
        """
        if isNoneOrEmpty(inProjectName):
            raise ValueError(f'{inProjectName=} can not be None or empty')
        if isNoneOrEmpty(inProjectConfig):
            raise ValueError(f'{inProjectConfig=} can not be None or empty')

        inProjectName = inProjectName.strip()
        self.__mProjectName: str = inProjectName
        self.__mProjectConfig: ProjectConfig = inProjectConfig
        self.__mRepos: Set[SmartRepo] = set()

        for repoName, repoConfig in self.__mProjectConfig.repos.items():
            self.__mRepos.add(
                SmartRepo(
                    path=repoConfig.properties.GIT_ROOT / repoName,
                    inRepoConfig=repoConfig
                )
            )

    @property
    def repositories(self) -> FrozenSet[SmartRepo]:
        return frozenset(self.__mRepos)

    def fetch(
        self,
        inRemote: Optional[str] = None,
        inSkipTags: bool = False
    ):
        """
        Fetches from the remote(s) (sync)
        :param inRemote: [Optional] Name of the remote, default fetches from all remotes
        :param inSkipTags: [Optional] Should skip fetching the tags
        """
        LOGGER.entrance()

        for repo in self.repositories:
            repo.fetch(inRemote, inSkipTags)

    async def afetch(
        self,
        inRemote: Optional[str] = None,
        inSkipTags: bool = False
    ):
        """
        Fetches from the remote(s) (async)
        :param inRemote: [Optional] Name of the remote, default fetches from all remotes
        :param inSkipTags: [Optional] Should skip fetching the tags
        """
        LOGGER.entrance()

        await asyncio.gather(*(repo.afetch(inRemote, inSkipTags) for repo in self.repositories))

    def prune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
        LOGGER.entrance()

        for repo in self.repositories:
            repo.prune(inPruneBranches, inPruneTags)

    async def aprune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags (async)

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
        LOGGER.entrance()

        await asyncio.gather(*(repo.aprune(inPruneBranches, inPruneTags) for repo in self.repositories))

    def pull(self, inBranchName: str = None, inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT):
        """
        Pulls the latest changes

        :param inBranchName:    Name of the branch to sync, defaults to current active branch if None (optional)
        :param inRemoteName:    Name of the remote to sync with, defaults to 'origin' (optional)
        """
        LOGGER.entrance()

        for repo in self.repositories:
            repo.pull(inBranchName, inRemoteName)

    async def apull(self, inBranchName: str = None, inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT):
        """
        Pulls the latest changes (async)

        :param inBranchName:    Name of the branch to sync, defaults to current active branch if None (optional)
        :param inRemoteName:    Name of the remote to sync with, defaults to 'origin' (optional)
        """
        LOGGER.entrance()

        await asyncio.gather(*(repo.apull(inBranchName, inRemoteName) for repo in self.repositories))

    @classmethod
    def from_config(cls, inProjectName: str, inConfig: SmartGitConfig) -> Self:
        """
        Initializes a SmartProject from the configuration for the given project name

        :param inProjectName:   Name of the repository
        :param inConfig:        SmartGit Master Configuration instance
        :returns: The initialized SmartProject instance
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inProjectName):
            raise ValueError(f'{inProjectName=} cannot be None or Empty')

        inProjectName = inProjectName.strip()
        try:
            projectConfig: Optional[ProjectConfig] = inConfig.get_project_config(inProjectName)
            if isNoneOrEmpty(projectConfig):
                raise Exception(f'{projectConfig} is not configured in {inConfig.get_config_source(ConfigType.JSON)}')
        except Exception as e:
            LOGGER.exception(e)
            raise

        return cls(inProjectName, projectConfig)

    @classmethod
    def smart_init(
        cls,
        inProjectName: str,
        inProjectConfig: ProjectConfig,
        inBranch: str = None
    ) -> Self:
        """
        Initializes a SmartProject by
            1. Locating the repository at prop.GIT_ROOT/inRepoName if exists
            2. Cloning the repository from prop.GIT_REMOTE_BASE_URL/inRepoName
            3. Switching to the specified branch if provided
            4. Submodule Initialization if prop.GIT_SUBMODULE_INIT enabled

        :param inProjectName:       Name of the Project
        :param inProjectConfig:     Configuration of the Project
        :param inBranch:            Branch to check out (optional)
                                    Defaults to remote and local HEAD, for new and existing repositories respectively
        :raises Exception: If clone operation fails
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inProjectName):
            raise ValueError(f'{inProjectName=} cannot be None or Empty')
        if isNoneOrEmpty(inProjectConfig):
            raise ValueError(f'{inProjectConfig=} cannot be None or Empty')

        inProjectName = inProjectName.strip()

        for repoName, repoConfig in inProjectConfig.repos.items():
            SmartRepo.smart_init(repoName.strip(), repoConfig, inBranch)

        return cls(inProjectName, inProjectConfig)

    @classmethod
    async def asmart_init(
        cls,
        inProjectName: str,
        inProjectConfig: ProjectConfig,
        inBranch: str = None
    ) -> Self:
        LOGGER.entrance()

        if isNoneOrEmpty(inProjectName):
            raise ValueError(f'{inProjectName=} cannot be None or Empty')
        if isNoneOrEmpty(inProjectConfig):
            raise ValueError(f'{inProjectConfig=} cannot be None or Empty')

        inProjectName = inProjectName.strip()
        await asyncio.gather(
            *(SmartRepo.asmart_init(
                repoName.strip(),
                repoConfig,
                inBranch
            ) for repoName, repoConfig in inProjectConfig.repos.items())
        )

        return cls(inProjectName, inProjectConfig)
