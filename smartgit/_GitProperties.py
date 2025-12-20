""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit/_GitProperties.py                                                                                 """
""" Base class to manage Git-related properties                                                                      """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from typing import *

from smartgit.utils_internal._GenUtility import isNoneOrEmpty, validateEnvVariable
from smartgit.utils_internal._LoggingConfig import getSmartLogger

# Logger instance
LOGGER = getSmartLogger()


class GitProperties:
    def __init__(
            self,
            inGitRoot: Optional[str] = None,
            inGitCloneRemoteURLPrefix: Optional[str] = None,
    ):
        """
        Initializes Git properties
        - GIT_ROOT
        - GIT_CLONE_REMOTE_URL_PREFIX

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
        self.__mGitRoot: str = os.path.abspath(
            validateEnvVariable('GIT_ROOT', inFallbackValue=os.getcwd(), inLogger=LOGGER)
            if isNoneOrEmpty(inGitRoot)
            else inGitRoot.strip()
        )

        self.__mGitCloneRemoteURLPrefix: str = (
            validateEnvVariable('GIT_CLONE_REMOTE_URL_PREFIX', inLogger=LOGGER)
            if isNoneOrEmpty(inGitCloneRemoteURLPrefix)
            else inGitCloneRemoteURLPrefix.strip()
        )

        if isNoneOrEmpty(self.__mGitCloneRemoteURLPrefix):
            LOGGER.warning(
                'Property:GIT_CLONE_REMOTE_URL_PREFIX is not set via parameter or environment variable. '
                'Clone operations may fail without a valid remote URL prefix.'
            )

    @property
    def GitRoot(self) -> str:
        return self.__mGitRoot

    @property
    def GitCloneRemoteURLPrefix(self) -> Optional[str]:
        return self.__mGitCloneRemoteURLPrefix
