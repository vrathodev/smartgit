""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.core._SmartRepo.py                                                                                """
""" Enhanced repository class with additional Git operations                                                         """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
import contextlib
import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Coroutine, FrozenSet, Generator, List, Optional, Self, Tuple

from git import GitCommandError, InvalidGitRepositoryError, Repo

from smartgit.common.constants import SG_VAL_REMOTE_NAME_DEFAULT
from smartgit.common.errors import (
    InvalidConfigError,
    InvalidOperationError,
    InvalidValueError,
    NoneOrEmptyValueError,
    OperationError,
    SmartGitError,
)
from smartgit.common.results import FailureResult, OperationContext, OperationResult, SuccessResult
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

        try:
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
                LOGGER.debug(f'Error (RC {returnCode}):')
                LOGGER.debug(errorStr)
                raise GitCommandError(' '.join(command), returnCode, errorStr)
        finally:
            # Never leave an orphaned subprocess behind (failed read/decode or task cancellation)
            if process.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    process.kill()
                await process.wait()

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
    ) -> OperationResult:
        LOGGER.entrance()

        return self._run_sync_command(
            'create-branch',
            self._create_branch(inBranchName, inStartPoint, inPushRemote, inRemoteName),
            self.execute,
            inBranchName
        )

    async def async_create_branch(
        self,
        inBranchName: str,
        inStartPoint: str,
        inPushRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT
    ) -> OperationResult:
        LOGGER.entrance()

        return await self._run_async_command(
            'create-branch',
            self._create_branch(inBranchName, inStartPoint, inPushRemote, inRemoteName),
            self.aexecute,
            inBranchName
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
            if f'{inRemoteName}/{inBranchName}' in self.remote_branches:
                yield GitCMD(
                    [
                        'git',
                        'push',
                        inRemoteName,
                        '--delete',
                        inBranchName,
                    ]
                )
                LOGGER.info(f'`{inBranchName=}` deleted from remote {inRemoteName=}')
            else:
                LOGGER.warning(f'`{inBranchName=}` does not exist on remote {inRemoteName=}. Skipping remote deletion.')

    def delete_branch(
        self,
        inBranchName: str,
        inFromRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT,
        inForce: bool = False
    ) -> OperationResult:
        LOGGER.entrance()

        return self._run_sync_command(
            'delete-branch',
            self._delete_branch(inBranchName, inFromRemote, inRemoteName, inForce),
            self.execute,
            inBranchName
        )

    async def async_delete_branch(
        self,
        inBranchName: str,
        inFromRemote: bool = False,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT,
        inForce: bool = False
    ) -> OperationResult:
        LOGGER.entrance()

        return await self._run_async_command(
            'delete-branch',
            self._delete_branch(inBranchName, inFromRemote, inRemoteName, inForce),
            self.aexecute,
            inBranchName
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
    ) -> OperationResult:
        LOGGER.entrance()

        return self._run_sync_command('fetch', self._fetch(inRemote, inSkipTags), self.execute)

    async def afetch(
        self,
        inRemote: Optional[str] = None,
        inSkipTags: bool = False
    ) -> OperationResult:
        LOGGER.entrance()

        return await self._run_async_command('fetch', self._fetch(inRemote, inSkipTags), self.aexecute)

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

    def prune(self, inPruneBranches: bool = False, inPruneTags: bool = False) -> OperationResult:
        LOGGER.entrance()

        return self._run_sync_command('prune', self._prune(inPruneBranches, inPruneTags), self.execute)

    async def aprune(self, inPruneBranches: bool = False, inPruneTags: bool = False) -> OperationResult:
        LOGGER.entrance()

        return await self._run_async_command('prune', self._prune(inPruneBranches, inPruneTags), self.aexecute)

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
            except (TypeError, ValueError) as error:
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

    def pull(self, inBranchName: str = None, inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT) -> OperationResult:
        LOGGER.entrance()

        return self._run_sync_command(
            'pull',
            self._pull(inBranchName, inRemoteName),
            self.execute,
            inBranchName
        )

    async def apull(
        self,
        inBranchName: str = None,
        inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT
    ) -> OperationResult:
        LOGGER.entrance()

        return await self._run_async_command(
            'pull',
            self._pull(inBranchName, inRemoteName),
            self.aexecute,
            inBranchName
        )

    @classmethod
    def _resolve_repo_config(cls, inRepoName: str, inConfig: SmartGitConfig) -> Tuple[str, RepoConfig]:
        """
        Resolves the configuration for the given repository name

        :param inRepoName:  Name of the repository
        :param inConfig:    SmartGit Master Configuration instance
        :returns: Tuple of (stripped repository name, repository configuration)
        :raises InvalidConfigError
        :raises NoneOrEmptyValueError
        """
        if isNoneOrEmpty(inRepoName):
            raise NoneOrEmptyValueError('RepoName')

        inRepoName = inRepoName.strip()
        repoConfig: Optional[RepoConfig] = inConfig.get_repo_config(inRepoName)
        if isNoneOrEmpty(repoConfig):
            raise InvalidConfigError(
                f'Repo {inRepoName} is not configured in {str(inConfig.get_config_source(ConfigType.JSON))}'
            )

        return inRepoName, repoConfig

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

        inRepoName, repoConfig = cls._resolve_repo_config(inRepoName, inConfig)

        return cls.smart_init(inRepoName=inRepoName, inRepoConfig=repoConfig)

    @classmethod
    def try_from_config(cls, inRepoName: str, inConfig: SmartGitConfig) -> Tuple[Optional[Self], OperationResult]:
        """
        Initializes a SmartRepo from the configuration for the given repository name, without raising for
        failures of the repository initialization itself (e.g. clone failure)

        :param inRepoName:  Name of the repository
        :param inConfig:    SmartGit Master Configuration instance
        :returns: Tuple of (initialized SmartRepo or None on failure, result of the initialization)
        :raises InvalidConfigError: If the repository is not configured
        :raises NoneOrEmptyValueError
        """
        LOGGER.entrance()

        inRepoName, repoConfig = cls._resolve_repo_config(inRepoName, inConfig)

        return cls.try_init(inRepoName=inRepoName, inRepoConfig=repoConfig)

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

    @classmethod
    def try_init(
        cls,
        inRepoName: str,
        inRepoConfig: RepoConfig,
        inBranch: str = None,
    ) -> Tuple[Optional[Self], OperationResult]:
        """
        Initializes a SmartRepo (see smart_init) without raising for the failures of the initialization
        (e.g. clone failure, branch switch failure, submodule failure)

        :param inRepoName:          Name of the Repository
        :param inRepoConfig:        Configuration of the Repository
        :param inBranch:            Branch to check out (optional)
                                    Defaults to remote and local HEAD, for new and existing repositories respectively
        :returns: Tuple of (initialized SmartRepo or None on failure, result of the initialization)
        :raises NoneOrEmptyValueError
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inRepoName):
            raise NoneOrEmptyValueError('RepoName')
        if isNoneOrEmpty(inRepoConfig):
            raise NoneOrEmptyValueError('RepoConfig')

        inRepoName = inRepoName.strip()
        context = OperationContext(
            operation='init',
            repo_name=inRepoName,
            repo_path=str(convertToPath(inRepoConfig.properties.GIT_ROOT) / inRepoName),
            branch=str(inBranch).strip() if not isNoneOrEmpty(inBranch) else None,
        )

        try:
            return cls.smart_init(inRepoName, inRepoConfig, inBranch), SuccessResult(context=context)
        except (Exception, SmartGitError) as error:
            LOGGER.debug(f'Initialization of {inRepoName} failed', exc_info=error)
            return None, FailureResult.from_exception(error, context)

    @classmethod
    async def atry_init(
        cls,
        inRepoName: str,
        inRepoConfig: RepoConfig,
        inBranch: str = None,
    ) -> Tuple[Optional[Self], OperationResult]:
        return await asyncio.to_thread(
            cls.try_init,
            inRepoName,
            inRepoConfig,
            inBranch
        )

    def _operation_context(
        self,
        inOperation: str,
        inBranch: Optional[str] = None,
        inCommand: Optional[GitCMD] = None
    ) -> OperationContext:
        """
        Creates the context of an operation on this repository

        :param inOperation: Name of the operation
        :param inBranch:    [Optional] Branch of the operation, defaults to the active branch when unknown
        :param inCommand:   [Optional] Git command being executed
        """
        if isNoneOrEmpty(inBranch):
            try:
                inBranch = self.active_branch.name
            except Exception:
                # Detached HEAD or unreadable repo state, branch is reported as unknown
                inBranch = None

        return OperationContext(
            operation=inOperation,
            repo_name=self.name,
            repo_path=str(self.path),
            branch=str(inBranch).strip() if not isNoneOrEmpty(inBranch) else None,
            command=' '.join(inCommand.args) if inCommand is not None else None,
        )

    def _failure_result(
        self,
        inError: BaseException,
        inOperation: str,
        inBranch: Optional[str],
        inCommand: Optional[GitCMD]
    ) -> FailureResult:
        """
        Converts the error raised by an operation into a FailureResult enriched with this repository's context
        """
        # Full trace is kept for the log only, the CLI renders the context-rich result instead
        LOGGER.debug(f'Operation {inOperation} failed for {self.name}', exc_info=inError)

        return FailureResult.from_exception(inError, self._operation_context(inOperation, inBranch, inCommand))

    def _run_sync_command(
        self,
        inOperation: str,
        inSteps: Generator[GitCMD, str, Any],
        inExecutor: Callable[[List[str]], None],
        inBranch: Optional[str] = None
    ) -> OperationResult:
        """
        Synchronous runner to execute given Git commands

        Containment boundary: expected errors (native OS, Git and SmartGit errors) never propagate out of the
        runner, they are returned as FailureResult instead. Cancellation (BaseException) is NOT swallowed.

        :param inOperation: Name of the operation being executed
        :param inSteps: Generator yielding GitCMD instances
        :param inExecutor: Callable to execute the Git command
        :param inBranch: [Optional] Branch the operation targets, defaults to the active branch when unknown
        :returns: SuccessResult if all the commands completed, FailureResult otherwise
        """
        # Command being executed, None when the failure is not raised by an executing command
        command: Optional[GitCMD] = None
        try:
            command = next(inSteps)
            while True:
                result = inExecutor(list(command.args))
                # Executed, errors raised by the generator past this point are not caused by this command
                command = None
                command = inSteps.send(result)
        except StopIteration:
            return SuccessResult(context=self._operation_context(inOperation, inBranch))
        except (Exception, SmartGitError) as error:
            return self._failure_result(error, inOperation, inBranch, command)

    async def _run_async_command(
        self,
        inOperation: str,
        inSteps: Generator[GitCMD, str, Any],
        inExecutor: Callable[[List[str]], Coroutine[Any, Any, None]],
        inBranch: Optional[str] = None
    ) -> OperationResult:
        """
        Asynchronous runner to execute given Git commands

        Containment boundary: expected errors (native OS, Git and SmartGit errors) never propagate out of the
        runner, they are returned as FailureResult instead. Cancellation (BaseException) is NOT swallowed.

        :param inOperation: Name of the operation being executed
        :param inSteps: Generator yielding GitCMD instances
        :param inExecutor: Async callable to execute the Git command
        :param inBranch: [Optional] Branch the operation targets, defaults to the active branch when unknown
        :returns: SuccessResult if all the commands completed, FailureResult otherwise
        """
        # Command being executed, None when the failure is not raised by an executing command
        command: Optional[GitCMD] = None
        try:
            command = next(inSteps)
            while True:
                result = await inExecutor(list(command.args))
                # Executed, errors raised by the generator past this point are not caused by this command
                command = None
                command = inSteps.send(result)
        except StopIteration:
            return SuccessResult(context=self._operation_context(inOperation, inBranch))
        except (Exception, SmartGitError) as error:
            return self._failure_result(error, inOperation, inBranch, command)
