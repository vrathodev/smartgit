""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.core._SmartRepo.py                                                                                """
""" Enhanced repository class with additional Git operations                                                         """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Coroutine, FrozenSet, Generator, List, Optional, Self

from git import GitCommandError, InvalidGitRepositoryError, Repo

from smartgit.common.constants import SG_VAL_REMOTE_NAME_DEFAULT
from smartgit.common.errors import (
    InvalidConfigError,
    InvalidOperationError,
    InvalidValueError,
    NoneOrEmptyValueError,
    OperationError,
)
from smartgit.common.types import SmartPath
from smartgit.config import ConfigType
from smartgit.config import Properties, RepoConfig, SmartGitConfig
from smartgit.utils import *

# Logger instance
LOGGER = getSmartLogger()


@dataclass(frozen=True)
class GitCMD:
    """
    Represents a Git command with its arguments.
    """
    args = tuple[str, ...]

    def __init__(self, args: list[str]):
        # Filter empty args (e.g., from conditional --prune flags)
        object.__setattr__(self, 'args', tuple(a.strip() for a in args if not isNoneOrEmpty(a)))


class SmartRepo(Repo):
    """
    SmartRepo -- Async + sync Git operations capable SmartGit primitive
    """

    def __init__(self, inRepoConfig: Optional[RepoConfig], **kwargs):
        """
        Initializes the SmartRepo with the RepoConfig

        :param inRepoConfig:    [Optional] Repository configuration to initialize the SmartRepo with.
        """
        super().__init__(**kwargs)

        self.__mRepoConfig: RepoConfig = inRepoConfig or RepoConfig()

    @property
    def config(self) -> RepoConfig:
        return self.__mRepoConfig

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def path(self) -> Path:
        return Path(self.working_dir)

    @property
    def properties(self) -> Properties:
        return self.__mRepoConfig.properties

    @cached_property
    def remote_branches(self) -> FrozenSet[str]:
        """
        Returns a frozen set of remote branch names in the repository
        """
        LOGGER.entrance()

        branches = set()

        for remote in self.remotes:
            remote.fetch()
            for ref in remote.refs:
                branches.add(ref.name)

        return frozenset(branches)

    def execute(self, inCommand: List[str]):
        """
        Executes a Git command *synchronously* on a given repository
        :param inCommand: Git command to execute
        :raises NoneOrEmptyValueError
        :raises GitCommandError
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inCommand):
            raise NoneOrEmptyValueError('Command')

        command: List[str] = [part.strip() for part in inCommand if not isNoneOrEmpty(part)]
        LOGGER.debug(f'Git command (sync): {' '.join(command)}')
        LOGGER.debug(self.git.execute(command))

    async def aexecute(self, inCommand: List[str]):
        """
        Executes a Git command *asynchronously* on a given repository
        :param inCommand: Git command to execute
        :raises NoneOrEmptyValueError
        :raises GitCommandError
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inCommand):
            raise NoneOrEmptyValueError('Command')

        command: List[str] = [part.strip() for part in inCommand if not isNoneOrEmpty(part)]
        LOGGER.debug(f'Git command (async): {' '.join(command)}')

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.path
        )

        while True:
            output: bytes = await process.stdout.readline()
            outputStr: str = output.decode().strip()
            if isNoneOrEmpty(outputStr):
                LOGGER.debug('Empty output received for above command')
                break
            else:
                LOGGER.debug('Output:')
                LOGGER.debug(outputStr)

        returnCode: int = await process.wait()
        if returnCode != 0:
            error: bytes = await process.stderr.read()
            errorStr: str = error.decode().strip()
            LOGGER.error(f'Error (RC {returnCode}):')
            LOGGER.error(errorStr)
            raise GitCommandError(' '.join(command), returnCode, errorStr)

    def _create_branch(
        self,
        inBranchName: str,
        inStartPoint: str,
        inPushRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT
    ):
        """
        Creates a new branch from the specified start point (commit hash or branch name or tag)

        :param inBranchName:    Name of the new branch to create
        :param inStartPoint:    to start the new branch from
        :param inPushRemote:    Whether to push the new branch to remote (optional) Defaults to False
        :param inRemoteName:    Name of the remote to push to (optional) Defaults to 'origin'
        :raises InvalidOperationError
        :raises InvalidValueError
        :raises NoneOrEmptyValueError
        """
        LOGGER.entrance()

        if self.properties.GIT_READONLY_MODE:
            raise InvalidOperationError(f'Can not create `{inBranchName}` branch, `{self.name}` repo is marked READ-ONLY')

        if isNoneOrEmpty(inBranchName):
            raise NoneOrEmptyValueError('BranchName')
        if isNoneOrEmpty(inStartPoint):
            raise NoneOrEmptyValueError('StartPoint')
        if isNoneOrEmpty(inRemoteName):
            raise NoneOrEmptyValueError('RemoteName')

        inBranchName = inBranchName.strip()
        inStartPoint = inStartPoint.strip()
        inRemoteName = inRemoteName.strip()

        if inBranchName in self.branches:
            LOGGER.warning(f'Branch {inBranchName} already exists. Skipping creation.')
            return
        if inBranchName in self.remote_branches:
            LOGGER.warning(f'Branch {inBranchName} already exists in remote. Skipping creation.')
            return
        if not self.is_valid_object(inStartPoint):
            raise InvalidValueError(f'Reference {inStartPoint} is not a valid branch, commit or tag')

        yield GitCMD(
            [
                'git',
                'branch',
                inBranchName,
                inStartPoint,
            ]
        )
        LOGGER.info(f'Branch {inBranchName} created successfully from {inStartPoint} in local')

        if inPushRemote:
            yield GitCMD(
                [
                    'git',
                    'push',
                    '--set-upstream',
                    inRemoteName,
                    inBranchName
                ]
            )
            LOGGER.info(f'Branch {inBranchName} pushed successfully to Remote {inRemoteName}')

    def create_branch(
        self,
        inBranchName: str,
        inStartPoint: str,
        inPushRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT
    ):
        LOGGER.entrance()

        return self._run_sync_command(
            self._create_branch(inBranchName, inStartPoint, inPushRemote, inRemoteName),
            self.execute
        )

    async def async_create_branch(
        self,
        inBranchName: str,
        inStartPoint: str,
        inPushRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT
    ):
        LOGGER.entrance()

        return await self._run_async_command(
            self._create_branch(inBranchName, inStartPoint, inPushRemote, inRemoteName),
            self.aexecute
        )

    def _delete_branch(
        self,
        inBranchName: str,
        inFromRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT,
        inForce: bool = False
    ):
        """
        Deletes a branch locally and/or from remote.

        :param inBranchName:    Name of the branch to delete
        :param inFromRemote:    Whether to delete the branch from remote (optional) Defaults to False
        :param inRemoteName:    Name of the remote to delete from (optional) Defaults to 'origin'
        :param inForce:         Whether to force delete the branch (optional) Defaults to False
        :raises InvalidOperationError
        :raises NoneOrEmptyValueError
        """
        LOGGER.entrance()

        if self.properties.GIT_READONLY_MODE:
            raise InvalidOperationError(f'Can not delete {inBranchName} branch, {self.name} is marked READ-ONLY')

        if isNoneOrEmpty(inBranchName):
            raise NoneOrEmptyValueError('BranchName')

        inBranchName = inBranchName.strip()

        if inBranchName in self.branches:
            yield GitCMD(
                [
                    'git',
                    'branch',
                    '-D' if inForce else '-d',
                    inBranchName,
                ]
            )
            LOGGER.info(f'Branch {inBranchName} deleted from local')
        else:
            LOGGER.warning(f'Branch {inBranchName} does not exist locally. Skipping local deletion.')

        if inFromRemote:
            # TODO: Check if branch exists before deletion to NOT deal w/ Git's unformatted errors.
            yield GitCMD(
                [
                    'git',
                    'push',
                    inRemoteName,
                    '--delete',
                    inBranchName,
                ]
            )

    def delete_branch(
        self,
        inBranchName: str,
        inFromRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT,
        inForce: bool = False
    ):
        LOGGER.entrance()

        return self._run_sync_command(
            self._delete_branch(inBranchName, inFromRemote, inRemoteName, inForce),
            self.execute
        )

    async def async_delete_branch(
        self,
        inBranchName: str,
        inFromRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT,
        inForce: bool = False
    ):
        LOGGER.entrance()

        return await self._run_async_command(
            self._delete_branch(inBranchName, inFromRemote, inRemoteName, inForce),
            self.aexecute
        )

    def _fetch(
        self,
        inRemote: Optional[str] = None,
        inSkipTags: bool = False
    ):
        """
        Fetches from the remote(s)
        :param inRemote: [Optional] Name of the remote, default fetches from all remotes
        :param inSkipTags: [Optional] Should skip fetching the tags
        """
        LOGGER.entrance()

        command = ['git', 'fetch']
        if isNoneOrEmpty(inRemote):
            command.append('--all')
            command.extend(['--jobs', str(self.properties.GIT_FETCH_JOBS)])
        else:
            command.append(inRemote.strip())
        if inSkipTags:
            command.append('--no-tags')

        yield GitCMD(command)

    def fetch(
        self,
        inRemote: Optional[str] = None,
        inSkipTags: bool = False
    ):
        LOGGER.entrance()

        return self._run_sync_command(self._fetch(inRemote, inSkipTags), self.execute)

    async def afetch(
        self,
        inRemote: Optional[str] = None,
        inSkipTags: bool = False
    ):
        LOGGER.entrance()

        return await self._run_async_command(self._fetch(inRemote, inSkipTags), self.aexecute)

    def _prune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
        LOGGER.entrance()

        if not (inPruneBranches or inPruneTags):
            raise InvalidValueError('Must specify whether to prune branches and/or tags')

        yield GitCMD(
            [
                'git',
                'fetch',
                '--prune' if inPruneBranches else '',
                '--prune-tags' if inPruneTags else '',
            ]
        )

    def prune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        LOGGER.entrance()

        return self._run_sync_command(self._prune(inPruneBranches, inPruneTags), self.execute)

    async def aprune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        LOGGER.entrance()

        return await self._run_async_command(self._prune(inPruneBranches, inPruneTags), self.aexecute)

    def _pull(self, inBranchName: str = None, inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT):
        """
        Pulls the latest changes

        :param inBranchName:    Name of the branch to sync, defaults to current active branch if None (optional)
        :param inRemoteName:    Name of the remote to sync with, defaults to 'origin' (optional)
        :raises NoneOrEmptyValueError
        :raises OperationError
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inRemoteName):
            raise NoneOrEmptyValueError('RemoteName')
        if isNoneOrEmpty(inBranchName):
            try:
                LOGGER.info(f'Specified branch is None or empty. Using {self.active_branch.name} to sync.')
                inBranchName = self.active_branch.name
            except TypeError | ValueError as error:
                raise OperationError(
                    f'Detached/Invalid HEAD state detected for Repo {self.name}, '
                    f'Can not pull. Fix the repo state and try again.'
                ) from error

        inBranchName = inBranchName.strip()
        inRemoteName = inRemoteName.strip()

        switchBranch: bool = self.active_branch.name != inBranchName

        if switchBranch:
            if inBranchName not in self.branches:
                LOGGER.warning(f'Branch {inBranchName} does not exist locally, attempting to checkout from remote...')
            yield GitCMD(
                [
                    'git',
                    'switch',
                    inBranchName
                ]
            )

        yield GitCMD(
            [
                'git',
                'pull',
                '--no-tags',
                inRemoteName,
                inBranchName,
            ]
        )
        LOGGER.info(f'Pulled {inBranchName} successfully from {inRemoteName}')

    def pull(self, inBranchName: str = None, inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT):
        LOGGER.entrance()

        return self._run_sync_command(
            self._pull(inBranchName, inRemoteName),
            self.execute
        )

    async def apull(self, inBranchName: str = None, inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT):
        LOGGER.entrance()

        return await self._run_async_command(
            self._pull(inBranchName, inRemoteName),
            self.aexecute
        )

    @classmethod
    def from_config(cls, inRepoName: str, inConfig: SmartGitConfig) -> Self:
        """
        Initializes a SmartRepo from the configuration for the given repository name

        :param inRepoName:  Name of the repository
        :param inConfig:    SmartGit Master Configuration instance
        :returns: The initialized SmartRepo instance
        :raises InvalidConfigError
        :raises NoneOrEmptyValueError
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inRepoName):
            raise NoneOrEmptyValueError('RepoName')

        inRepoName = inRepoName.strip()
        repoConfig: Optional[RepoConfig] = inConfig.get_repo_config(inRepoName)
        if isNoneOrEmpty(repoConfig):
            raise InvalidConfigError(
                f'Repo {inRepoName} is not configured in {str(inConfig.get_config_source(ConfigType.JSON))}'
            )

        return cls.smart_init(inRepoName=inRepoName, inRepoConfig=repoConfig)

    @classmethod
    def is_valid(cls, inRepoPath: Path) -> bool:
        LOGGER.entrance()
        if not isNoneOrEmpty(inRepoPath):
            try:
                Repo(inRepoPath)
                return True
            except Exception:
                pass
        return False

    @classmethod
    def repo_path(cls, inRepoNameORPath: SmartPath, inBasePath: SmartPath) -> Path:
        """
        Constructs the repository path `inBasePath/RepoName` if inRepoNameORPath is a path, else returns the path as is.

        :param inRepoNameORPath:    Repository name/path
        :param inBasePath:          Base path of the repo
        :raises NoneOrEmptyValueError
        """
        if isNoneOrEmpty(inRepoNameORPath):
            raise NoneOrEmptyValueError('RepoNameORPath')
        if isNoneOrEmpty(inBasePath):
            raise NoneOrEmptyValueError('BasePath')

        inBasePath: Path = convertToPath(inBasePath)
        inRepoNameORPath = str(inRepoNameORPath).strip()
        repoPath = Path(inRepoNameORPath if os.sep in inRepoNameORPath else inBasePath / inRepoNameORPath)

        return repoPath.resolve()

    @classmethod
    def smart_init(
        cls,
        inRepoName: str,
        inRepoConfig: RepoConfig,
        inBranch: str = None,
    ) -> Self:
        """
        Initializes a SmartRepo by
            1. Locating the repository at prop.GIT_ROOT/inRepoName if exists
            2. Cloning the repository from prop.GIT_REMOTE_BASE_URL/inRepoName
            3. Switching to the specified branch if provided
            4. Submodule Initialization if prop.GIT_SUBMODULE_INIT enabled

        :param inRepoName:          Name of the Repository
        :param inRepoConfig:        Configuration of the Repository
        :param inBranch:            Branch to check out (optional)
                                    Defaults to remote and local HEAD, for new and existing repositories respectively
        :raises NoneOrEmptyValueError
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inRepoName):
            raise NoneOrEmptyValueError('RepoName')
        if isNoneOrEmpty(inRepoConfig):
            raise NoneOrEmptyValueError('RepoConfig')

        inRepoName = inRepoName.strip()
        destinationPath: Path = convertToPath(inRepoConfig.properties.GIT_ROOT)

        repoPath: Path = destinationPath / inRepoName
        repoPath.mkdir(parents=True, exist_ok=True)

        try:
            repo = cls(path=repoPath, inRepoConfig=inRepoConfig)
            LOGGER.info(f'Repo `{str(repoPath)}` already exists. Skipping clone...')
        except InvalidGitRepositoryError:
            cls.clone_from(
                url=f'{inRepoConfig.properties.GIT_REMOTE_BASE_URL}/{inRepoName}.git',
                to_path=repoPath,
            )
            repo = cls(path=repoPath, inRepoConfig=inRepoConfig)
            LOGGER.info(f'Repo `{str(repoPath)}` cloned successfully')

        if not isNoneOrEmpty(inBranch):
            repo.execute(['git', 'switch', str(inBranch).strip()])
        if inRepoConfig.properties.GIT_SUBMODULE_INIT:
            repo.execute(
                ['git', 'submodule', 'update', '--init', '--recursive', '--jobs', str(repo.properties.GIT_FETCH_JOBS)]
            )

        return repo

    @classmethod
    async def asmart_init(
        cls,
        inRepoName: str,
        inRepoConfig: RepoConfig,
        inBranch: str = None,
    ) -> Self:
        return await asyncio.to_thread(
            cls.smart_init,
            inRepoName,
            inRepoConfig,
            inBranch
        )

    def _run_sync_command(
        self,
        inSteps: Generator[GitCMD, str, Any],
        inExecutor: Callable[[List[str]], None]
    ) -> Any:
        """
        Synchronous runner to execute given Git commands
        :param inSteps: Generator yielding GitCMD instances
        :param inExecutor: Callable to execute the Git command
        """
        try:
            command: GitCMD = next(inSteps)
            while True:
                result = inExecutor(list(command.args))
                command = inSteps.send(result)
        except StopIteration as completed:
            return completed.value

    async def _run_async_command(
        self,
        inSteps: Generator[GitCMD, str, Any],
        inExecutor: Callable[[List[str]], Coroutine[Any, Any, None]]
    ) -> Any:
        """
        Asynchronous runner to execute given Git commands
        :param inSteps: Generator yielding GitCMD instances
        :param inExecutor: Async callable to execute the Git command
        """
        try:
            command: GitCMD = next(inSteps)
            while True:
                result = await inExecutor(list(command.args))
                command = inSteps.send(result)
        except StopIteration as completed:
            return completed.value
