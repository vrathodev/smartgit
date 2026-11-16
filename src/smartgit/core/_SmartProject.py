""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.core._SmartProject.py                                                                             """
""" Contains the definition of SmartProject class and related APIs                                                   """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
from typing import *

from smartgit.common.constants import SG_VAL_REMOTE_NAME_DEFAULT
from smartgit.common.errors import InvalidConfigError, NoneOrEmptyValueError
from smartgit.common.results import OperationResult, partition_results
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
        inInitResults: Optional[Iterable[OperationResult]] = None,
    ):
        """
        Initializes the SmartProject with the ProjectConfig

        :param inProjectName:       Name of the Project
        :param inProjectConfig:     Configuration of the Project
        :param inInitResults:       [Optional] Results of the repositories initialization.
                                    Repositories that failed to initialize are not part of the project and are
                                    reported with the results of its operations. Defaults to None
        :raises NoneOrEmptyValueError
        """
        if isNoneOrEmpty(inProjectName):
            raise NoneOrEmptyValueError('ProjectName')
        if isNoneOrEmpty(inProjectConfig):
            raise NoneOrEmptyValueError('ProjectConfig')

        inProjectName = inProjectName.strip()
        self.__mProjectName: str = inProjectName
        self.__mProjectConfig: ProjectConfig = inProjectConfig
        self.__mRepos: Set[SmartRepo] = set()
        self.__mInitResults: Tuple[OperationResult, ...] = tuple(inInitResults or ())

        _, initFailures = partition_results(self.__mInitResults)
        failedRepoNames: Set[str] = {failure.context.repo_name for failure in initFailures}

        for repoName, repoConfig in self.__mProjectConfig.repos.items():
            if repoName.strip() in failedRepoNames:
                continue
            self.__mRepos.add(
                SmartRepo(
                    path=repoConfig.properties.GIT_ROOT / repoName,
                    inRepoConfig=repoConfig
                )
            )

    @property
    def config(self) -> ProjectConfig:
        return self.__mProjectConfig

    @property
    def name(self) -> str:
        return self.__mProjectName

    @property
    def properties(self):
        return self.__mProjectConfig.properties

    @property
    def repositories(self) -> FrozenSet[SmartRepo]:
        return frozenset(self.__mRepos)

    @property
    def init_results(self) -> Tuple[OperationResult, ...]:
        return self.__mInitResults

    def _with_init_failures(self, inResults: Iterable[OperationResult]) -> List[OperationResult]:
        """
        Prepends the repositories initialization failures to the results of a batch operation, so that the
        repositories that could not be initialized (e.g. clone failure) are not silently left out of the batch
        """
        _, initFailures = partition_results(self.__mInitResults)

        return [*initFailures, *inResults]

    def fetch(
        self,
        inRemote: Optional[str] = None,
        inSkipTags: bool = False
    ) -> List[OperationResult]:
        """
        Fetches from the remote(s) (sync)
        :param inRemote: [Optional] Name of the remote, default fetches from all remotes
        :param inSkipTags: [Optional] Should skip fetching the tags
        :returns: Result of the fetch per repository, a failure never aborts the remaining repositories
        """
        LOGGER.entrance()

        return self._with_init_failures(repo.fetch(inRemote, inSkipTags) for repo in self.repositories)

    async def afetch(
        self,
        inRemote: Optional[str] = None,
        inSkipTags: bool = False
    ) -> List[OperationResult]:
        """
        Fetches from the remote(s) (async)
        :param inRemote: [Optional] Name of the remote, default fetches from all remotes
        :param inSkipTags: [Optional] Should skip fetching the tags
        :returns: Result of the fetch per repository, a failure never aborts the remaining repositories
        """
        LOGGER.entrance()

        return self._with_init_failures(
            await asyncio.gather(*(repo.afetch(inRemote, inSkipTags) for repo in self.repositories))
        )

    def prune(self, inPruneBranches: bool = False, inPruneTags: bool = False) -> List[OperationResult]:
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        :returns: Result of the prune per repository, a failure never aborts the remaining repositories
        """
        LOGGER.entrance()

        return self._with_init_failures(repo.prune(inPruneBranches, inPruneTags) for repo in self.repositories)

    async def aprune(self, inPruneBranches: bool = False, inPruneTags: bool = False) -> List[OperationResult]:
        """
        Prunes branches and/or tags (async)

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        :returns: Result of the prune per repository, a failure never aborts the remaining repositories
        """
        LOGGER.entrance()

        return self._with_init_failures(
            await asyncio.gather(*(repo.aprune(inPruneBranches, inPruneTags) for repo in self.repositories))
        )

    def pull(
        self,
        inBranchName: str = None,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT
    ) -> List[OperationResult]:
        """
        Pulls the latest changes

        :param inBranchName:    Name of the branch to sync, defaults to current active branch if None (optional)
        :param inRemoteName:    Name of the remote to sync with, defaults to 'origin' (optional)
        :returns: Result of the pull per repository, a failure never aborts the remaining repositories
        """
        LOGGER.entrance()

        return self._with_init_failures(repo.pull(inBranchName, inRemoteName) for repo in self.repositories)

    async def apull(
        self,
        inBranchName: str = None,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT
    ) -> List[OperationResult]:
        """
        Pulls the latest changes (async)

        :param inBranchName:    Name of the branch to sync, defaults to current active branch if None (optional)
        :param inRemoteName:    Name of the remote to sync with, defaults to 'origin' (optional)
        :returns: Result of the pull per repository, a failure never aborts the remaining repositories
        """
        LOGGER.entrance()

        return self._with_init_failures(
            await asyncio.gather(*(repo.apull(inBranchName, inRemoteName) for repo in self.repositories))
        )

    @classmethod
    def from_config(cls, inProjectName: str, inConfig: SmartGitConfig, inBranch: str = None) -> Self:
        LOGGER.entrance()

        if isNoneOrEmpty(inProjectName):
            raise NoneOrEmptyValueError('ProjectName')

        inProjectName = inProjectName.strip()
        projectConfig: Optional[ProjectConfig] = inConfig.get_project_config(inProjectName)
        if isNoneOrEmpty(projectConfig):
            raise InvalidConfigError(
                f'Project {inProjectName} is not configured in {str(inConfig.get_config_source(ConfigType.JSON))}'
            )

        return cls.smart_init(inProjectName=inProjectName, inProjectConfig=projectConfig, inBranch=inBranch)

    @classmethod
    async def from_config_async(cls, inProjectName: str, inConfig: SmartGitConfig, inBranch: str = None) -> Self:
        """
        Initializes a SmartProject from the configuration for the given project name

        :param inProjectName:   Name of the repository
        :param inConfig:        SmartGit Master Configuration instance
        :param inBranch:        Branch to check out in every repository (optional)
        :returns: The initialized SmartProject instance, see init_results for the outcome per repository
        :raises NoneOrEmptyValueError
        :raises InvalidConfigError
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inProjectName):
            raise NoneOrEmptyValueError('ProjectName')

        inProjectName = inProjectName.strip()
        projectConfig: Optional[ProjectConfig] = inConfig.get_project_config(inProjectName)
        if isNoneOrEmpty(projectConfig):
            raise InvalidConfigError(
                f'Project {inProjectName} is not configured in {str(inConfig.get_config_source(ConfigType.JSON))}'
            )

        return await cls.asmart_init(inProjectName=inProjectName, inProjectConfig=projectConfig, inBranch=inBranch)

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
        :returns: The SmartProject of the repositories initialized successfully, a repository failing to initialize
                  never aborts the others. See init_results for the outcome per repository
        :raises NoneOrEmptyValueError
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inProjectName):
            raise NoneOrEmptyValueError('ProjectName')
        if isNoneOrEmpty(inProjectConfig):
            raise NoneOrEmptyValueError('ProjectConfig')

        inProjectName = inProjectName.strip()

        initResults: List[OperationResult] = [
            SmartRepo.try_init(repoName.strip(), repoConfig, inBranch)[1]
            for repoName, repoConfig in inProjectConfig.repos.items()
        ]

        return cls(inProjectName, inProjectConfig, initResults)

    @classmethod
    async def asmart_init(
        cls,
        inProjectName: str,
        inProjectConfig: ProjectConfig,
        inBranch: str = None
    ) -> Self:
        LOGGER.entrance()

        if isNoneOrEmpty(inProjectName):
            raise NoneOrEmptyValueError('ProjectName')
        if isNoneOrEmpty(inProjectConfig):
            raise NoneOrEmptyValueError('ProjectConfig')

        inProjectName = inProjectName.strip()
        outcomes = await asyncio.gather(
            *(SmartRepo.atry_init(
                repoName.strip(),
                repoConfig,
                inBranch
            ) for repoName, repoConfig in inProjectConfig.repos.items())
        )

        return cls(inProjectName, inProjectConfig, [result for _, result in outcomes])
