""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._SmartGitConfigLoader.py                                                                   """
""" SmartGit configuration loader interface                                                                          """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path
from typing import List, Optional

from pydantic_core import ValidationError

from smartgit.common.constants import (
    SG_VAL_DOTENV_FILE_DEFAULT,
)

from smartgit.config._ConfigTypeMeta import ConfigSource, ConfigSourceType, ConfigType
from smartgit.config._SmartGitConfig import SmartGitConfig
from smartgit.utils import getSmartLogger, isNoneOrEmpty

LOGGER = getSmartLogger()

# Default SmartGit configurations to fall back
DEFAULT_CONFIG_JSON_SOURCES: List[ConfigSource] = [
    ConfigSource(config_type=ConfigType.JSON, source_type=ConfigSourceType.ENV),
    ConfigSource(config_type=ConfigType.JSON, source_type=ConfigSourceType.LOCAL),
    ConfigSource(config_type=ConfigType.JSON, source_type=ConfigSourceType.GLOBAL),
]

DEFAULT_CONFIG_DOTENV_SOURCES: List[ConfigSource] = [
    ConfigSource(config_type=ConfigType.DOTENV, source_type=ConfigSourceType.ENV),
    ConfigSource(config_type=ConfigType.DOTENV, source_type=ConfigSourceType.LOCAL),
    ConfigSource(config_type=ConfigType.DOTENV, source_type=ConfigSourceType.GLOBAL),
]


class SmartGitConfigLoader:
    """
    Loads SmartGitConfig using explicit inputs and ordered implicit sources
    """

    def __init__(
        self,
        inJSONConfigSources: Optional[List[ConfigSource]] = None,
        inDotEnvConfigSources: Optional[List[ConfigSource]] = None
    ):
        """
        To set up the configurations sources in priority order
        :param inJSONConfigSources:     List of JSON config sources in priority order
        :param inDotEnvConfigSources:   List of dotenv config sources in priority order
        """
        if isNoneOrEmpty(inJSONConfigSources):
            inJSONConfigSources = DEFAULT_CONFIG_JSON_SOURCES
        if isNoneOrEmpty(inDotEnvConfigSources):
            inDotEnvConfigSources = DEFAULT_CONFIG_DOTENV_SOURCES

        self.__mJSONSources: List[ConfigSource] = inJSONConfigSources
        self.__mDotEnvSources: List[ConfigSource] = inDotEnvConfigSources

    def load(
        self,
        inJSONConfigPath: Optional[Path] = None,
        inDotEnvConfigPath: Optional[Path] = None,
    ) -> SmartGitConfig:
        """Loads the SmartGitConfig using optional explicit inputs and ordered implicit sources"""
        currDotEnvConfigPath: Path = None

        # Validate dotenv config path
        if not isNoneOrEmpty(inDotEnvConfigPath):
            currDotEnvConfigPath = Path(inDotEnvConfigPath).resolve().absolute()
            try:
                self.__validate_dotenv_config_path(currDotEnvConfigPath, ignoreError=False)
            except ValueError as error:
                LOGGER.exception(error)
                raise error
        else:
            for source in self.__mDotEnvSources:
                try:
                    self.__validate_dotenv_config_path(source.source_path, ignoreError=False)
                    currDotEnvConfigPath = source.source_path
                    break
                except ValueError as error:
                    LOGGER.debug(error, exc_info=True, stack_info=True)

        if isNoneOrEmpty(currDotEnvConfigPath):
            LOGGER.warning('Failed to load any of the default dotenv configuration sources, skipping')

        if not isNoneOrEmpty(inJSONConfigPath):
            inJSONConfigPath = Path(inJSONConfigPath)
            return SmartGitConfig(inJSONConfigPath=inJSONConfigPath, inDotEnvConfigPath=currDotEnvConfigPath)

        config: SmartGitConfig = SmartGitConfig()
        for source in self.__mJSONSources:
            try:
                config = SmartGitConfig(
                    inJSONConfigPath=source.source_path,
                    inDotEnvConfigPath=currDotEnvConfigPath
                )
                break
            except ValidationError as error:
                LOGGER.debug(error, exc_info=True, stack_info=True)
            except ValueError as error:
                LOGGER.debug(error, exc_info=True, stack_info=True)

        if isNoneOrEmpty(config):
            LOGGER.warning('Failed to load any of the default JSON configuration sources, skipping')

        return config

    def __validate_dotenv_config_path(self, inConfigPath: Path, ignoreError: bool = False) -> bool:
        inConfigPath = inConfigPath.resolve().absolute()
        result: bool = (
            inConfigPath.exists() and
            inConfigPath.is_file() and
            inConfigPath.name == SG_VAL_DOTENV_FILE_DEFAULT
        )

        if not result:
            if ignoreError:
                return result

            raise ValueError(
                f'Invalid config: `{inConfigPath}`\n'
                f'Must be a file named `{SG_VAL_DOTENV_FILE_DEFAULT}` w/ valid path.'
            )

        return result
