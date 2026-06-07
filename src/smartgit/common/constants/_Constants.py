""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file common.constants._Constants.py                                                                             """
""" Contains the definition of the global constants for SmartGit                                                     """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path

SG_VAL_APP_NAME: str                    = 'smartgit'
SG_VAL_BASE_DIR: Path                   = Path(__file__).parent.parent.parent.parent.parent.resolve()
SG_VAL_CONFIG_FILE_DEFAULT: str         = 'smartgit.config.json'
SG_VAL_DOTENV_FILE_DEFAULT: str         = 'smartgit.config.env'
SG_VAL_LOG_CONFIG_FILE_DEFAULT: str     = 'logging.config.json'

# Environment variables
SG_KEY_CONFIG_PATH: str                 = 'SMARTGIT_CONFIG_PATH'
# TODO: What should it default to? BASE_DIR or CWD
SG_VAL_CONFIG_PATH_DEFAULT: Path        = SG_VAL_BASE_DIR / SG_VAL_CONFIG_FILE_DEFAULT

SG_KEY_DOTENV_PATH: str                 = 'SMARTGIT_DOTENV_PATH'
# TODO: What should it default to? BASE_DIR or CWD
SG_VAL_DOTENV_PATH_DEFAULT: Path        = SG_VAL_BASE_DIR / SG_VAL_DOTENV_FILE_DEFAULT

# Git-ops defaults
SG_VAL_BRANCH_NAME_DEFAULT: str = 'main'
SG_VAL_REMOTE_NAME_DEFAULT: str = 'origin'

# Logging env variables and default
SG_KEY_LOG_CONFIG_PATH: str             = 'SMARTGIT_LOGGING_CONFIG_PATH'
SG_VAL_LOG_CONFIG_DEFAULT: Path         = SG_VAL_BASE_DIR / SG_VAL_LOG_CONFIG_FILE_DEFAULT

SG_KEY_LOG_LEVEL: str                   = 'SMARTGIT_LOG_LEVEL'
SG_VAL_LOG_LEVEL_DEFAULT: str           = 'WARNING'
SG_KEY_LOG_PATH: str                    = 'SMARTGIT_LOG_PATH'
SG_VAL_LOG_PATH_DEFAULT: Path           = SG_VAL_BASE_DIR / 'logs' / f'{SG_VAL_APP_NAME}.log'

SG_VAL_LOGGER_NAME: str                 = SG_VAL_APP_NAME
SG_VAL_LOG_FORMAT: str                  = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
SG_VAL_LOG_DATETIME_FORMAT: str         = '%Y-%m-%d %H:%M:%S'
