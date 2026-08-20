""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.utils._GenUtility.py                                                                              """
""" Contains the definition of the general utility methods                                                           """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import errno
import os
from pathlib import Path

from smartgit.common.errors import InvalidValueError, SmartGitError


def assure(inParam: dict, inArg: str, ignoreError: bool = False):
    """Assure if the given `inArg` is a key of `inParam`"""
    if inParam is not None and inArg in inParam and inParam[inArg] is not None:
        return inParam[inArg]
    else:
        # If set to True, No Exception would be thrown but would return False
        # in case given inArg is not a key of inParam
        if ignoreError:
            return False
        else:
            raise InvalidValueError(f'Invalid Expression: {inParam}[{inArg}]')


def convertToPath(inPath: str | os.PathLike[str] | Path) -> Path:
    """Converts the given path in any representations to Path object"""
    if isinstance(inPath, Path):
        return inPath
    elif isinstance(inPath, (str, os.PathLike)):
        return Path(inPath)
    else:
        raise InvalidValueError(f'inPath must be of type str, os.PathLike or Path, provided type is: {type(inPath)}')


def createDir(inDirPath: str, inMode: int = 0o777):
    """Creates the absent directories from the given path."""
    try:
        os.makedirs(inDirPath, inMode)
    except OSError as err:
        # Re-raise the error unless it's for already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(inDirPath):
            raise SmartGitError(f'Failed to create directory {inDirPath}') from err


def isNoneOrEmpty(inVal) -> bool:
    """Checks if the given value is None or Empty"""
    if inVal is None:
        return True
    elif isinstance(inVal, str):
        return inVal is None or len(inVal.strip()) == 0
    elif isinstance(inVal, dict):
        return (
                inVal is None or
                len(inVal) == 0 or
                all(map(lambda x: isNoneOrEmpty(x) and isNoneOrEmpty(inVal[x]), inVal))
        )
    elif isinstance(inVal, list) or isinstance(inVal, tuple):
        return (
                inVal is None or
                len(inVal) == 0 or
                all(map(lambda x: isNoneOrEmpty(x), inVal))
        )
    else:
        return isNoneOrEmpty(str(inVal).strip())


def readFile(inPath: Path, inMode: str = 'r', inEncoding: str = 'utf-8') -> str | None:
    """
    Reads the content of the file

    :throws FileNotFoundError if the file does not exist, IOError for other I/O errors
    """
    with inPath.open(mode=inMode, encoding=inEncoding) as file:
        content = file.read()

    return content
