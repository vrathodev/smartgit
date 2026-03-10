""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_SmartRepo.py                                                                                     """
""" Enhanced repository class with additional Git operations                                                         """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
import os
from dataclasses import dataclass
from functools import cached_property
from os import PathLike
from pathlib import Path
from typing import FrozenSet, List, Generator, Any, Callable, Coroutine

from git import Repo, CommandError

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
    @property
    def name(self) -> str:
        return os.path.basename(self.working_dir or self.working_tree_dir or '')

    @cached_property
    def remote_branches(self) -> FrozenSet[str]:
        """
        Returns a frozen set of remote branch names in the repository
        """
        LOGGER.entrance()

        branches = set()

        for remote in self.remotes:
            LOGGER.debug(f'Fetching from {remote.name=}')
            remote.fetch()
            for ref in remote.refs:
                LOGGER.debug(f'Processing {ref.name=}')
                branches.add(ref.name)

        return frozenset(branches)

    def execute(self, inCommand: List[str]):
        """
        Executes a Git command synchronously on a given repository
        :param inCommand: Git command to execute
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inCommand):
            raise ValueError(f'{inCommand=} cannot be None or Empty')

        command: List[str] = [part.strip() for part in inCommand if not isNoneOrEmpty(part)]
        LOGGER.debug(f'Git command (sync): {' '.join(command)}')
        LOGGER.debug(self.git.execute(command))

    async def aexecute(self, inCommand: List[str]):
        """
        Executes a Git command asynchronously on a given repository
        :param inCommand: Git command to execute
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inCommand):
            raise ValueError(f'{inCommand=} cannot be None or Empty')

        command: List[str] = [part.strip() for part in inCommand if not isNoneOrEmpty(part)]
        LOGGER.debug(f'Git command (async): {' '.join(command)}')

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir
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
            raise CommandError(' '.join(command), returnCode, errorStr)

    def _create_branch(
            self,
            inBranchName: str,
            inStartPoint: str,
            inPushRemote: bool = False,
            inRemoteName: str = 'origin'):
        """
        Creates a new branch from the specified start point (commit hash or branch name or tag)

        :param inBranchName:    Name of the new branch to create
        :param inStartPoint:    to start the new branch from
        :param inPushRemote:    Whether to push the new branch to remote (optional) Defaults to False
        :param inRemoteName:    Name of the remote to push to (optional) Defaults to 'origin'
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inBranchName):
            raise ValueError(f'{inBranchName=} cannot be None or Empty')
        if isNoneOrEmpty(inStartPoint):
            raise ValueError(f'{inStartPoint=} cannot be None or Empty')
        if isNoneOrEmpty(inRemoteName):
            raise ValueError(f'{inRemoteName=} cannot be None or Empty')

        inBranchName = inBranchName.strip()
        inStartPoint = inStartPoint.strip()
        inRemoteName = inRemoteName.strip()

        if inBranchName in self.branches:
            LOGGER.warning(f'`{inBranchName=}` already exists. Skipping creation.')
            return
        if inBranchName in self.remote_branches:
            LOGGER.warning(f'`{inBranchName=}` already exists in remote. Skipping creation.')
            return
        if not self.is_valid_object(inStartPoint):
            LOGGER.exception(f'`{inStartPoint=}` is NOT a valid reference. Aborting branch creation.')
            raise Exception('`{inStartPoint=}` is NOT a valid reference.')

        yield GitCMD([
            'git',
            'branch',
            inBranchName.strip(),
            inStartPoint.strip(),
        ])
        LOGGER.info(f'`{inBranchName=}` created successfully from `{inStartPoint=}` in local')

        if inPushRemote:
            yield GitCMD([
                'git',
                'push',
                '--set-upstream',
                inRemoteName,
                inBranchName
            ])
            LOGGER.info(f'`{inBranchName=}` pushed successfully to `{inRemoteName=}`')

    def create_branch(
            self,
            inBranchName: str,
            inStartPoint: str,
            inPushRemote: bool = False,
            inRemoteName: str = 'origin'):
        """
        Creates a new branch from the specified start point (commit hash or branch name or tag)

        :param inBranchName:    Name of the new branch to create
        :param inStartPoint:    to start the new branch from
        :param inPushRemote:    Whether to push the new branch to remote (optional) Defaults to False
        :param inRemoteName:    Name of the remote to push to (optional) Defaults to 'origin'
        """
        return self._run_sync_command(
            self._create_branch(inBranchName, inStartPoint, inPushRemote, inRemoteName),
            self.execute
        )

    async def async_create_branch(
            self,
            inBranchName: str,
            inStartPoint: str,
            inPushRemote: bool = False,
            inRemoteName: str = 'origin'):
        """
        Creates a new branch from the specified start point (commit hash or branch name or tag)

        :param inBranchName:    Name of the new branch to create
        :param inStartPoint:    to start the new branch from
        :param inPushRemote:    Whether to push the new branch to remote (optional) Defaults to False
        :param inRemoteName:    Name of the remote to push to (optional) Defaults to 'origin'
        """
        return await self._run_async_command(
            self._create_branch(inBranchName, inStartPoint, inPushRemote, inRemoteName),
            self.aexecute
        )

    def _delete_branch(
            self,
            inBranchName: str,
            inFromRemote: bool = False,
            inRemoteName: str = 'origin',
            inForce: bool = False):
        """
        Deletes a branch locally and/or from remote.
        :param inBranchName:    Name of the branch to delete
        :param inFromRemote:    Whether to delete the branch from remote (optional) Defaults to False
        :param inRemoteName:    Name of the remote to delete from (optional) Defaults to 'origin'
        :param inForce:         Whether to force delete the branch (optional) Defaults to False
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inBranchName):
            raise ValueError(f'{inBranchName=} cannot be None or Empty')

        inBranchName = inBranchName.strip()

        if inBranchName in self.branches:
            yield GitCMD([
                'git',
                'branch',
                '-D' if inForce else '-d',
                inBranchName,
            ])
            LOGGER.info(f'`{inBranchName=}` deleted from local')
        else:
            LOGGER.warning(f'`{inBranchName=}` does not exist locally. Skipping local deletion.')

        if inFromRemote:
            if f'{inRemoteName}/{inBranchName}' in self.remote_branches:
                yield GitCMD([
                    'git',
                    'push',
                    inRemoteName,
                    '--delete',
                    inBranchName,
                ])
            else:
                LOGGER.warning(f'`{inBranchName=}` does not exist in remote. Skipping remote deletion.')

    def delete_branch(
            self,
            inBranchName: str,
            inFromRemote: bool = False,
            inRemoteName: str = 'origin',
            inForce: bool = False):
        """
        Deletes a branch locally and/or from remote.
        :param inBranchName:    Name of the branch to delete
        :param inFromRemote:    Whether to delete the branch from remote (optional) Defaults to False
        :param inRemoteName:    Name of the remote to delete from (optional) Defaults to 'origin'
        :param inForce:         Whether to force delete the branch (optional) Defaults to False
        """
        return self._run_sync_command(
            self._delete_branch(inBranchName, inFromRemote, inRemoteName, inForce),
            self.execute
        )

    async def async_delete_branch(
            self,
            inBranchName: str,
            inFromRemote: bool = False,
            inRemoteName: str = 'origin',
            inForce: bool = False):
        """
        Deletes a branch locally and/or from remote.
        :param inBranchName:    Name of the branch to delete
        :param inFromRemote:    Whether to delete the branch from remote (optional) Defaults to False
        :param inRemoteName:    Name of the remote to delete from (optional) Defaults to 'origin'
        :param inForce:         Whether to force delete the branch (optional) Defaults to False
        """
        return await self._run_async_command(
            self._delete_branch(inBranchName, inFromRemote, inRemoteName, inForce),
            self.aexecute
        )

    def _prune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
        LOGGER.entrance()

        if not (inPruneBranches or inPruneTags):
            raise ValueError('Must specify whether to prune branches and/or tags')

        yield GitCMD([
            'git',
            'fetch',
            '--prune' if inPruneBranches else '',
            '--prune-tags' if inPruneTags else '',
        ])

    def prune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
        return self._run_sync_command(self._prune(inPruneBranches, inPruneTags), self.execute)

    async def aprune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
        return await self._run_async_command(self._prune(inPruneBranches, inPruneTags), self.aexecute)

    def _pull(self, inBranchName: str = None, inRemoteName: str = 'origin'):
        """
        Pulls the latest changes

        :param inBranchName:    Name of the branch to sync, defaults to current active branch if None (optional)
        :param inRemoteName:    Name of the remote to sync with, defaults to 'origin' (optional)
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inRemoteName):
            raise ValueError(f'{inRemoteName=} cannot be None or Empty')
        if isNoneOrEmpty(inBranchName):
            try:
                LOGGER.info(f'{inBranchName=} is None or empty. Using {self.active_branch.name} for sync.')
                inBranchName = self.active_branch.name
            except TypeError as error:
                LOGGER.exception('Detached HEAD state detected, Please specify a valid branch name to sync.')
                raise error

        inBranchName = inBranchName.strip()
        inRemoteName = inRemoteName.strip()

        if f'{inRemoteName}/{inBranchName}' not in self.remote_branches:
            LOGGER.warning(f'`{inBranchName=}` does not exist on {inRemoteName=}. Aborting sync operation.')
            return
        if inBranchName not in self.branches:
            LOGGER.warning(f'`{inBranchName=}` does not exist locally, attempting to checkout from remote...')
            yield GitCMD([
                'git',
                'switch',
                inBranchName,
                f'{inRemoteName}/{inBranchName}',
            ])
            return

        yield GitCMD([
            'git',
            'pull',
            inRemoteName,
            inBranchName,
        ])
        LOGGER.info(f'Pulled {inBranchName} successfully from {inRemoteName}')

    def pull(self, inBranchName: str = None, inRemoteName: str = 'origin'):
        """
        Pulls the latest changes

        :param inBranchName:    Name of the branch to sync, defaults to current active branch if None (optional)
        :param inRemoteName:    Name of the remote to sync with, defaults to 'origin' (optional)
        """
        return self._run_sync_command(
            self._pull(inBranchName, inRemoteName),
            self.execute
        )

    async def apull(self, inBranchName: str = None, inRemoteName: str = 'origin'):
        """
        Pulls the latest changes

        :param inBranchName:    Name of the branch to sync, defaults to current active branch if None (optional)
        :param inRemoteName:    Name of the remote to sync with, defaults to 'origin' (optional)
        """
        return await self._run_async_command(
            self._pull(inBranchName, inRemoteName),
            self.aexecute
        )

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
    def smart_init(
            cls,
            inRepoName: str,
            inDestinationPath: str | PathLike[str] | Path,
            inRemoteURLPrefix: str,
            inBranch: str = None,
            initSubmodules: bool = False
    ) -> 'SmartRepo':
        """
        Initializes a SmartRepo by
            1. Locating the repository at inDestinationPath/inRepoName if it exists
            2. Cloning the repository from inRemoteURLPrefix/inRepoName
            3. Switching to the specified branch if provided
            4. Initializing submodules if opted for

        :param inRepoName:          Name of the repository to clone
        :param inDestinationPath:   Base directory to locate or clone the given repository
        :param inRemoteURLPrefix:   Remote URL prefix to use for cloning.
        :param inBranch:            Branch to check out (optional)
                                    Defaults to remote and local HEAD
                                    for new and existing repositories respectively if not specified
        :param initSubmodules:      Whether to initialize submodules (optional) Defaults to False
        :raises Exception: If clone operation fails
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inRepoName):
            raise ValueError(f'{inRepoName=} cannot be None or Empty')
        if isNoneOrEmpty(inDestinationPath):
            raise ValueError(f'{inDestinationPath=} cannot be None or Empty')
        if isNoneOrEmpty(inRemoteURLPrefix):
            raise ValueError(f'{inRemoteURLPrefix=} cannot be None or Empty')

        inRepoName = inRepoName.strip()
        inRemoteURLPrefix = inRemoteURLPrefix.strip()

        destinationPath: Path = convertToPath(inDestinationPath)
        destinationPath.mkdir(parents=True, exist_ok=True)

        repoPath: Path = destinationPath / inRepoName
        if SmartRepo.is_valid(repoPath):
            repo = SmartRepo(repoPath)
            LOGGER.info(f'`{repoPath=}` already exists. Skipping clone...')
        else:
            repo = SmartRepo.clone_from(
                url=f'{inRemoteURLPrefix}/{inRepoName}.git',
                to_path=repoPath,
            )
            LOGGER.info(f'Cloned `{repoPath=}` successfully')

        if not isNoneOrEmpty(inBranch):
            inBranch = inBranch.strip()
            repo.execute(['git', 'switch', inBranch])
        if initSubmodules:
            repo.execute(['git', 'submodule', 'update', '--init', '--recursive'])

        return repo

    @classmethod
    async def asmart_init(
            cls,
            inRepoName: str,
            inDestinationPath: str | PathLike[str] | Path,
            inRemoteURLPrefix: str,
            inBranch: str = None,
            initSubmodules: bool = False
    ) -> 'SmartRepo':
        return await asyncio.to_thread(
            SmartRepo.smart_init,
            inRepoName,
            inDestinationPath,
            inRemoteURLPrefix,
            inBranch,
            initSubmodules
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
