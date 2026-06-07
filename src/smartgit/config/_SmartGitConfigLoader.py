""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._SmartGitConfigLoader.py                                                                   """
""" SmartGit configuration loader interface                                                                          """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional

from pydantic_core import ValidationError

from smartgit.common.constants import (
    SG_KEY_CONFIG_PATH,
    SG_KEY_DOTENV_PATH,
    SG_VAL_BASE_DIR,
    SG_VAL_CONFIG_FILE_DEFAULT,
    SG_VAL_DOTENV_FILE_DEFAULT,
)
from smartgit.config._SmartGitConfig import SmartGitConfig
from smartgit.utils import getSmartLogger, isNoneOrEmpty

LOGGER = getSmartLogger()


class ConfigSourceType(Enum):
    """Supported implicit config discovery origins."""

    # Represents the source specified via environment variable i.e. SMARTGIT_CONFIG_PATH
    ENV = auto()
    # Represents the source specified in the current working directory
    LOCAL = auto()
    # Represents the source specified in the installation working directory
    GLOBAL = auto()


class ConfigType(Enum):
    """Supported SmartGit Configuration types"""

    JSON = SG_VAL_CONFIG_FILE_DEFAULT
    DOTENV = SG_VAL_DOTENV_FILE_DEFAULT

    @property
    def config_name(self) -> str:
        return self.value


@dataclass(frozen=True)
class ConfigSource:
    """A single implicit config source in priority order."""

    config_type: ConfigType
    source_type: ConfigSourceType

    @property
    def source_path(self) -> Path:
        """
        Configuration source path w/ base path and name
        :throws: ValueError if implicit source path is invalid
        """
        if self.source_type is ConfigSourceType.ENV:
            env = SG_KEY_CONFIG_PATH if self.config_type is ConfigType.JSON else SG_KEY_DOTENV_PATH
            try:
                return Path(os.environ[env].strip())
            except KeyError:
                raise ValueError(f'Configuration source not set. env.{env} not found')
        elif self.source_type is ConfigSourceType.LOCAL:
            return Path.cwd().resolve().absolute() / self.source_name
        elif self.source_type is ConfigSourceType.GLOBAL:
            return SG_VAL_BASE_DIR / self.source_name

        raise Exception(f'Unknown ConfigSourceType: {self.source_type}')

    @property
    def source_name(self) -> str:
        return self.config_type.config_name


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
