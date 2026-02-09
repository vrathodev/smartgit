""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_SmartRepo.py                                                                                     """
""" Enhanced repository class with additional Git operations                                                         """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from functools import cached_property
from os import PathLike
from pathlib import Path
from typing import FrozenSet

from git import Repo

from smartgit.utils_internal import *

# Logger instance
LOGGER = getSmartLogger()


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

        LOGGER.debug(self.git.execute([
            'git',
            'branch',
            inBranchName.strip(),
            inStartPoint.strip(),
        ]))
        LOGGER.info(f'`{inBranchName=}` created successfully from `{inStartPoint=}` in local')

        if inPushRemote:
            LOGGER.debug(self.git.execute([
                'git',
                'push',
                '--set-upstream',
                inRemoteName,
                inBranchName
            ]))
            LOGGER.info(f'`{inBranchName=}` pushed successfully to `{inRemoteName=}`')

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
        LOGGER.entrance()

        if isNoneOrEmpty(inBranchName):
            raise ValueError(f'{inBranchName=} cannot be None or Empty')

        inBranchName = inBranchName.strip()

        if inBranchName in self.branches:
            LOGGER.debug(self.git.execute([
                'git',
                'branch',
                '-D' if inForce else '-d',
                inBranchName,
            ]))
            LOGGER.info(f'`{inBranchName=}` deleted from local')
        else:
            LOGGER.warning(f'`{inBranchName=}` does not exist locally. Skipping local deletion.')

        if inFromRemote:
            if f'{inRemoteName}/{inBranchName}' in self.remote_branches:
                LOGGER.debug(self.git.execute([
                    'git',
                    'push',
                    inRemoteName,
                    '--delete',
                    inBranchName,
                ]))
            else:
                LOGGER.warning(f'`{inBranchName=}` does not exist in remote. Skipping remote deletion.')

    def pull(self, inBranchName: str = None, inRemoteName: str = 'origin'):
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
            LOGGER.debug(self.git.execute([
                'git',
                'switch',
                inBranchName,
                f'{inRemoteName}/{inBranchName}',
            ]))
            return

        LOGGER.debug(self.git.execute([
            'git',
            'pull',
            inRemoteName,
            inBranchName,
        ]))
        LOGGER.info(f'Pulled {inBranchName} successfully from {inRemoteName}')

    def prune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
        LOGGER.entrance()

        if not (inPruneBranches or inPruneTags):
            raise ValueError('Must specify whether to prune branches and/or tags')

        LOGGER.debug(self.git.execute([
            'git',
            'fetch',
            '--prune' if inPruneBranches else '',
            '--prune-tags' if inPruneTags else '',
        ]))

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
            LOGGER.debug(repo.git.execute(['git', 'switch', inBranch]))
        if initSubmodules:
            LOGGER.debug(repo.git.execute(['git', 'submodule', 'update', '--init', '--recursive']))

        return repo
