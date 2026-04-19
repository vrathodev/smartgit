""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file common.types._Types.py                                                                                     """
""" Contains the definition of the common types for SmartGit                                                         """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from os import PathLike
from pathlib import Path

from pydantic import HttpUrl

# Union types
type SmartPath = str | PathLike[str] | Path
type SmartURL = str | HttpUrl