""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.utils._LoggingConfig.py                                                                           """
""" Contains logging configuration and utility functions for consistent logging across the project                   """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import functools
import inspect
import json
import logging
import os
from logging.config import dictConfig
from pathlib import Path
from typing import *

from smartgit.common.constants import (
    SG_KEY_LOG_CONFIG_PATH,
    SG_KEY_LOG_LEVEL,
    SG_KEY_LOG_PATH,
    SG_VAL_CORE_LOGGER_NAME,
    SG_VAL_LOG_CONFIG_DEFAULT,
    SG_VAL_LOG_DATETIME_FORMAT,
    SG_VAL_LOG_FORMAT,
    SG_VAL_LOG_LEVEL_DEFAULT,
    SG_VAL_LOG_PATH_DEFAULT,
)
from smartgit.utils._GenUtility import createDir, isNoneOrEmpty

CWD = Path.cwd().resolve()


class SmartLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that extends the standard logger API with SmartGit-specific helpers:
    1. Function entrance logging
    2. Structured visual separators for log output
    """

    def __init__(self, inLogger: logging.Logger, inExtra: Optional[dict[str, Any]] = None):
        super().__init__(inLogger, extra=inExtra or {})

    def entrance(self, inFnName: Optional[str] = None, inLevel: int = logging.DEBUG):
        """
        Log function entrance with optional function name.
        If function name is not provided, it will be automatically detected.
        Log format will be consistent with context filter: classname.method or filename.method
        """
        if inFnName is None:
            # Get calling function name if not provided
            frame = inspect.currentframe().f_back

            if frame:
                inFnName = frame.f_code.co_name
                module = frame.f_globals.get('__name__', '')

                try:
                    if 'self' in frame.f_locals:
                        # Class member function
                        instance = frame.f_locals['self']
                        className = instance.__class__.__name__
                        inFnName = f'{className}.{inFnName}'
                    elif 'cls' in frame.f_locals:
                        # Class method
                        cls = frame.f_locals['cls']
                        className = cls.__name__
                        inFnName = f'{className}::{inFnName}'
                    else:
                        inFnName = f'{module}:{inFnName}'
                except:
                    inFnName = f'{module}:{inFnName}'
            else:
                inFnName = "<UNKNOWN>"

        self.log(inLevel, '+++ ENTER %s', inFnName, stacklevel=2)

    def header(self, inMessage: str, inLineLength: int = 100):
        """Prints a formatted header with the given message centered within a line of specified length."""
        inMessage = inMessage.strip()
        messageLen = len(inMessage)
        firstLen = (inLineLength - messageLen - 2) // 2
        secLen = inLineLength - messageLen - 2 - firstLen

        self.info('%s', '=' * inLineLength, stacklevel=2)
        self.info('%s %s %s', '=' * firstLen, inMessage.upper(), '=' * secLen, stacklevel=2)
        self.info('%s', '=' * inLineLength, stacklevel=2)

    def footer(self, inMessage: str, inLineLength: int = 100):
        """Prints a formatted footer with the given message centered within a line of specified length."""
        inMessage = inMessage.strip()
        messageLen = len(inMessage)
        firstLen = (inLineLength - messageLen - 2) // 2
        secLen = inLineLength - messageLen - 2 - firstLen

        self.info('%s %s %s', '=' * firstLen, inMessage, '=' * secLen, stacklevel=2)

    def highlight(self, inMessage: str, inLineLength: int = 100):
        """Prints a highlighted message with the given text centered within a line of specified length."""
        inMessage = inMessage.strip()
        messageLen = len(inMessage)
        firstLen = (inLineLength - messageLen - 2) // 2
        secLen = inLineLength - messageLen - 2 - firstLen

        self.info('%s %s %s', '+' * firstLen, inMessage, '+' * secLen, stacklevel=2)

    @classmethod
    def logEntrance(cls, inLogger=None):
        """
        Decorator to log function entrance.
        Usage: @SmartLoggerAdapter.logEntrance(logger)
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = inLogger if inLogger is not None else getSmartLogger()

                logger.entrance(func.__name__)

                # Call the original function
                return func(*args, **kwargs)

            return wrapper

        return decorator


@functools.lru_cache(maxsize=2)
def getSmartLogger(inLoggerName: str = None) -> SmartLoggerAdapter:
    """
    Returns the shared SmartGit logger adapter without configuring logging.
    Logging configuration remains the responsibility of explicit bootstrap code.

    :param inLoggerName: Name of the logger instance to configure, defaults to 'smartgit'
    """
    if isNoneOrEmpty(inLoggerName):
        inLoggerName = SG_VAL_CORE_LOGGER_NAME
    inLoggerName = inLoggerName.strip()

    return SmartLoggerAdapter(logging.getLogger(inLoggerName))


@functools.lru_cache(maxsize=1)
def configSmartLogger(inLoggerName: str = None) -> SmartLoggerAdapter:
    """
    Configures SmartGit logging from JSON config file if available, else uses default configuration.
    Allows overriding config via environment variable i.e. SMARTGIT_LOG_PATH, SMARTGIT_LOG_LEVEL, etc.

    :param inLoggerName: Name of the logger instance to configure, defaults to 'smartgit'
    """
    logConfigPath = os.environ.get(SG_KEY_LOG_CONFIG_PATH, '').strip()
    logConfigPath = os.path.abspath(
        logConfigPath if logConfigPath else str(SG_VAL_LOG_CONFIG_DEFAULT)
    )

    logger = getSmartLogger(inLoggerName)
    try:
        with open(logConfigPath) as file:
            dictConfig(json.load(file))

        logger.info(f'Logging configured from file: `{logConfigPath}`')
    except Exception as e:
        configLogging(
            inLevel=os.getenv(SG_KEY_LOG_LEVEL),
            inLogFilePath=os.getenv(SG_KEY_LOG_PATH)
        )
        logger.warning(f'Failed to load logging configuration from {logConfigPath}: {e}')
    finally:
        return logger


def configLogging(
    inLevel: Optional[str] = None,
    inLogFormat: Optional[str] = None,
    inDateFormat: Optional[str] = None,
    inLogFilePath: Optional[str] = None,
    inEnableConsole: bool = True,
    inEnableFile: bool = True
):
    """
    Configures logging with specified parameters or defaults from environment variables
    """
    level = logging.getLevelName(inLevel.strip().upper() if not isNoneOrEmpty(inLevel) else '')
    level = SG_VAL_LOG_LEVEL_DEFAULT if isinstance(level, str) and 'level' in level.lower() else level

    logFormat = inLogFormat if not isNoneOrEmpty(inLogFormat) else SG_VAL_LOG_FORMAT
    dateFormat = inDateFormat if not isNoneOrEmpty(inDateFormat) else SG_VAL_LOG_DATETIME_FORMAT
    logFile = Path(inLogFilePath.strip() if not isNoneOrEmpty(inLogFilePath) else SG_VAL_LOG_PATH_DEFAULT).resolve()

    if inEnableFile and logFile:
        createDir(str(logFile.parent))

    logging.basicConfig(
        level=level,
        format=logFormat,
        datefmt=dateFormat,
        handlers=[
            logging.StreamHandler() if inEnableConsole else logging.NullHandler(),
            logging.FileHandler(logFile) if inEnableFile else logging.NullHandler()
        ],
        force=True
    )
