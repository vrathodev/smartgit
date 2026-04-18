""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file common.constants._Constants.py                                                                             """
""" Contains the definition of the global constants for SmartGit                                                     """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path

SG_VAL_CONFIG_FILE_DEFAULT: str = 'smartgit.config.json'
SG_VAL_DOTENV_FILE_DEFAULT: str = '.env'
SG_VAL_BASE_DIR: Path           = Path(__file__).parent.parent.parent.parent.parent.resolve()

# Environment variables
SG_KEY_CONFIG_PATH = 'SMARTGIT_CONFIG_PATH'
# TODO: What should it default to? BASE_DIR or CWD
SG_VAL_CONFIG_PATH_DEFAULT = SG_VAL_BASE_DIR / SG_VAL_CONFIG_FILE_DEFAULT

SG_KEY_DOTENV_PATH = 'SMARTGIT_DOTENV_PATH'
# TODO: What should it default to? BASE_DIR or CWD
SG_VAL_DOTENV_PATH_DEFAULT = SG_VAL_BASE_DIR / SG_VAL_DOTENV_FILE_DEFAULT
