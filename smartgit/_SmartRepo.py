""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_SmartRepo.py                                                                                     """
""" Enhanced repository class with additional Git operations                                                         """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os

from git import Repo

from smartgit.utils_internal._GenUtility import isNoneOrEmpty
from smartgit.utils_internal._LoggingConfig import getSmartLogger

# Logger instance
LOGGER = getSmartLogger()


class SmartRepo(Repo):
    def prune(self, inPruneBranches: bool = False, inPruneTags: bool = False):
        """
        Prunes branches and/or tags.

        :param inPruneBranches:     Whether to prune branches. (optional) Defaults to False
        :param inPruneTags:         Whether to prune tags. (optional) Defaults to False
        """
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

    @property
    def name(self) -> str:
        return os.path.basename(self.working_dir or self.working_tree_dir or '')

    @classmethod
    def is_valid(cls, inRepoPath: str) -> bool:
        if not isNoneOrEmpty(inRepoPath):
            try:
                Repo(inRepoPath)
                return True
            except Exception:
                pass
        return False
