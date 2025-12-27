""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_SmartRepo.py                                                                                     """
""" Enhanced repository class with additional Git operations                                                         """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from os import PathLike
from pathlib import Path

from git import Repo

from smartgit.utils_internal import *

# Logger instance
LOGGER = getSmartLogger()


class SmartRepo(Repo):
    @property
    def name(self) -> str:
        return os.path.basename(self.working_dir or self.working_tree_dir or '')

    def prune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
        LOGGER.entrance()

        if not (inPruneBranches or inPruneTags):
            raise ValueError('Must specify to prune branches or tags')

        self.git.execute(
            [
                'git',
                'fetch',
                '--prune' if inPruneBranches else '',
                '--prune-tags' if inPruneTags else '',
            ]
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
            inBranch: str = 'main',
            initSubmodules: bool = False
    ) -> 'SmartRepo':
        """
        Initializes a SmartRepo by
            1. Locating the repository at inDestinationPath/inRepoName if it exists
            2. Cloning the repository from inRemoteURLPrefix/inRepoName

        :param inRepoName:          Name of the repository to clone
        :param inDestinationPath:   Base directory to locate or clone the given repository
        :param inRemoteURLPrefix:   Remote URL prefix to use for cloning.
        :param inBranch:            Branch to check out (optional) Defaults to 'main'
        :param initSubmodules:      Whether to initialize submodules (optional) Defaults to False
        :raises Exception: If clone operation fails
        """
        LOGGER.entrance()

        if any(
                isNoneOrEmpty(param)
                for param in [inRepoName, inDestinationPath, inRemoteURLPrefix, inBranch]
        ):
            raise ValueError('ERROR: Required param can not be None or empty')

        inRepoName = inRepoName.strip()
        inRemoteURLPrefix = inRemoteURLPrefix.strip()
        inBranch = inBranch.strip()

        destinationPath: Path = convertToPath(inDestinationPath)
        destinationPath.mkdir(parents=True, exist_ok=True)

        repoPath: Path = destinationPath / inRepoName
        if SmartRepo.is_valid(repoPath):
            repo = SmartRepo(repoPath)
            LOGGER.info(f'`{repoPath}` already exists. Skipping clone...')
        else:
            repo = SmartRepo.clone_from(
                url=f'{inRemoteURLPrefix}/{inRepoName}.git',
                to_path=repoPath,
            )
            LOGGER.info(f'Cloned `{repoPath}` successfully')

        LOGGER.debug(repo.git.execute(['git', 'checkout', inBranch]))
        if initSubmodules:
            LOGGER.debug(repo.git.execute(['git', 'submodule', 'update', '--init', '--recursive']))

        return repo
