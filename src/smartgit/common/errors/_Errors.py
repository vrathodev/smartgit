""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file common.errors._Errors.py                                                                                   """
""" Contains the definition of the custom errors for SmartGit                                                        """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from enum import Enum
from typing import Any


# Maintenance note: String version duplicated to avoid circular import
def isNoneOrEmptyStr(inValue: str) -> bool:
    return inValue is None or len(inValue.strip()) == 0


class SmartGitError(BaseException):
    """
    Base error type for SmartGit
    All the errors/exceptions thrown by SmartGit inherits from this class
    """


class SmartGitInternalError(SmartGitError):
    """
    Represents an internal error for SmartGit
    Raised for the unexpected errors caused by the bugs and regressions in SmartGit
    """

    def __init__(self, inMessage: str, *args: Any) -> None:
        self.__mDisplayMessage = 'Internal Error: Please report this issue to the SmartGit team'
        super().__init__(
            inMessage.strip() if not isNoneOrEmptyStr(inMessage)
            else self.__mDisplayMessage,
            *args
        )

    @property
    def display_message(self) -> str:
        return self.__mDisplayMessage


class InvalidEnumError(SmartGitInternalError):
    def __init__(self, inEnumRef: Enum) -> None:
        super().__init__(f'Invalid {inEnumRef.__class__.__name__}: {inEnumRef.name}')


class InvalidValueError(SmartGitError, ValueError):
    """
    Base error type for Bad Input
    """


class InvalidConfigError(InvalidValueError):
    """
    Represents a configuration error
    Raised for missing or invalid config
    """


class NoneOrEmptyValueError(InvalidValueError):
    def __init__(self, inIdent: str) -> None:
        if isNoneOrEmptyStr(inIdent):
            raise SmartGitInternalError('Identifier can not be None or Empty to NoneOrEmptyValueError')
        super().__init__(f'"{inIdent}" can not be None or Empty')


class OperationError(SmartGitError):
    """
    Base error type for Operation errors
    """


class InvalidOperationError(OperationError):
    pass
