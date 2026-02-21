""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file Utils.GenUtility.py                                                                                        """
""" Contains the definition of the general utility methods                                                           """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import errno
import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional


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
            raise KeyError(f'Invalid Expression: {inParam}[{inArg}]')


def convertToPath(inPath: str | os.PathLike[str] | Path) -> Path:
    """Converts the given path in any representations to Path object"""
    if isinstance(inPath, Path):
        return inPath
    elif isinstance(inPath, (str, os.PathLike)):
        return Path(inPath)
    else:
        raise ValueError(f'inPath must be of type str, os.PathLike or Path, provided type is: {type(inPath)}')


def createDir(inDirPath: str, inMode: int = 0o777):
    """Creates the absent directories from the given path."""
    try:
        os.makedirs(inDirPath, inMode)
    except OSError as err:
        # Re-raise the error unless it's for already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(inDirPath):
            raise


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


def validateEnvVariable(
        inVarName: str,
        inValidator: Callable[..., Any] = lambda x: not isNoneOrEmpty(x),
        inFallbackValue: Optional[Any] = None,
        inLogger: Optional[logging.Logger] = None) -> Any | None:
    """
    Validates the given Environment Variable using the given Validator method else returns the Fallback Value
    :param inVarName: Name of the Environment Variable
    :param inValidator: Validator method to validate the Environment Variable
    :param inFallbackValue: Fallback Value to return if validation fails
    :param inLogger: Logger instance to log messages
    """
    if isNoneOrEmpty(inVarName):
        raise ValueError('Environment Variable name cannot be None or Empty')
    if not callable(inValidator):
        raise ValueError('inValidator must be a callable function')

    inVarName = inVarName.strip()
    value = os.getenv(inVarName)
    if not value:
        if inLogger:
            inLogger.warning(f'env.`{inVarName}` is not set, falling back to `{inFallbackValue}`')
        return inFallbackValue
    elif inValidator(value):
        value = value.strip()
        if inLogger:
            inLogger.info(f'Using env.{inVarName}={value}')
        return value
    else:
        if inLogger:
            inLogger.warning(
                f'env.`{inVarName}` is set to an invalid value: `{value}`, falling back to `{inFallbackValue}`'
            )
        return inFallbackValue
