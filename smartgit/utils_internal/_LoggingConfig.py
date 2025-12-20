""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file Utils/_LoggingConfig.py                                                                                    """
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

from smartgit.utils_internal._GenUtility import isNoneOrEmpty, createDir

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class SmartLogger(logging.Logger):
    """
    Custom logger that extends logging.Logger with additional functionality:
    1. Function entrance logging
    2. Filtering out third-party logs like gitpython
    """
    # Environment Variable Names
    ENV_LOGGING_CONFIG: str = 'SMARTGIT_LOGGING_CONFIG'
    ENV_LOG_PATH: str = 'SMARTGIT_LOG_PATH'
    ENV_LOG_LEVEL: str = 'SMARTGIT_LOG_LEVEL'

    # Logger Defaults
    LOG_NAME: str = 'smartgit'
    LOG_FORMAT: str = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
    DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S'
    # Customizable via environment variable
    LOG_LEVEL: str = logging.DEBUG
    LOG_PATH: str = BASE_DIR / 'logs' / 'smartgit.log'

    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)

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

        self.log(inLevel, f'+++ ENTER {inFnName}')

    def header(self, inMessage: str, inLineLength: int = 100):
        """Prints a formatted header with the given message centered within a line of specified length."""
        inMessage = inMessage.strip()
        messageLen = len(inMessage)
        firstLen = (inLineLength - messageLen - 2) // 2
        secLen = inLineLength - messageLen - 2 - firstLen

        self.info('=' * inLineLength)
        self.info('=' * firstLen + f' {inMessage.upper()} ' + '=' * secLen)
        self.info('=' * inLineLength)

    def footer(self, inMessage: str, inLineLength: int = 100):
        """Prints a formatted footer with the given message centered within a line of specified length."""
        inMessage = inMessage.strip()
        messageLen = len(inMessage)
        firstLen = (inLineLength - messageLen - 2) // 2
        secLen = inLineLength - messageLen - 2 - firstLen

        self.info('=' * firstLen + f' {inMessage} ' + '=' * secLen)

    def highlight(self, inMessage: str, inLineLength: int = 100):
        """Prints a highlighted message with the given text centered within a line of specified length."""
        inMessage = inMessage.strip()
        messageLen = len(inMessage)
        firstLen = (inLineLength - messageLen - 2) // 2
        secLen = inLineLength - messageLen - 2 - firstLen

        self.info('+' * firstLen + f' {inMessage} ' + '+' * secLen)

    @classmethod
    def logEntrance(cls, inLogger=None):
        """
        Decorator to log function entrance
        Usage: @SimbaLogger.logEntrance(logger)
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if inLogger:
                    logger = inLogger
                else:
                    logger = getSmartLogger()

                logger.entrance(func.__name__)

                # Call the original function
                return func(*args, **kwargs)

            return wrapper

        return decorator


def getSmartLogger() -> SmartLogger:
    f"""
    Returns a configured SmartLogger instance
    
    To be used across the project for consistent logging.
    """
    global _LOGGER
    return _LOGGER


@functools.lru_cache(maxsize=1)
def configSmartLogger() -> SmartLogger:
    """
    Configures SmartLogger from JSON config file if available, else uses default configuration.
    Allows overriding config via environment variable i.e. SMARTGIT_LOG_PATH, SMARTGIT_LOG_LEVEL, etc.
    """
    logging.setLoggerClass(SmartLogger)

    log_config_path = os.environ.get(SmartLogger.ENV_LOGGING_CONFIG, '').strip()
    log_config_path = os.path.abspath(
        log_config_path if log_config_path else os.path.join(BASE_DIR, 'logging.config.json')
    )

    logger = None
    try:
        with open(log_config_path) as file:
            dictConfig(json.load(file))

        logger = logging.getLogger(SmartLogger.LOG_NAME)
        logger.info(f'Logging configured from file: {log_config_path}')
    except Exception as e:
        configLogging()
        logger = logging.getLogger(SmartLogger.LOG_NAME)
        logger.warning(f'Failed to load logging configuration from {log_config_path}: {e}')
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
    level = SmartLogger.LOG_LEVEL if isinstance(level, str) and 'level' in level.lower() else level

    logFormat = inLogFormat if not isNoneOrEmpty(inLogFormat) else SmartLogger.LOG_FORMAT
    dateFormat = inDateFormat if not isNoneOrEmpty(inDateFormat) else SmartLogger.DATE_FORMAT
    logFile = Path(inLogFilePath.strip() if not isNoneOrEmpty(inLogFilePath) else SmartLogger.LOG_PATH).resolve()

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


# Logging instance cache
_LOGGER: Optional['SmartLogger'] = configSmartLogger()
