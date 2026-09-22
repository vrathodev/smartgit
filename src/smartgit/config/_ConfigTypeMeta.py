""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._ConfigTypeMeta.py                                                                         """
""" Contains the definition of SmartGitConfig type primitives                                                        """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from smartgit.common.constants import (
    SG_KEY_CONFIG_PATH,
    SG_KEY_DOTENV_PATH,
    SG_VAL_BASE_DIR,
    SG_VAL_CONFIG_FILE_DEFAULT,
    SG_VAL_DOTENV_FILE_DEFAULT,
)


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
