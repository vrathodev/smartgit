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


class RepoOperationError(OperationError):
    """
    Represents a failed repository operation
    Wraps the native/domain root cause with the context (repo, path, branch, operation) it failed in
    """

    def __init__(
        self,
        inCause: BaseException,
        inOperation: str,
        inRepoName: str,
        inRepoPath: str,
        inBranch: str | None = None,
        inCommand: str | None = None,
    ) -> None:
        """
        Initializes the RepoOperationError with the root cause and the context of the failure

        :param inCause:         Native/domain exception that caused the failure
        :param inOperation:     Name of the operation that failed (e.g. pull, fetch)
        :param inRepoName:      Name of the repository the operation failed on
        :param inRepoPath:      Path of the repository the operation failed on
        :param inBranch:        [Optional] Branch the operation failed on. Defaults to None (unknown)
        :param inCommand:       [Optional] Git command being executed at the failure. Defaults to None
        """
        self.cause: BaseException = inCause
        self.operation: str = inOperation
        self.repo_name: str = inRepoName
        self.repo_path: str = inRepoPath
        self.branch: str | None = inBranch
        self.command: str | None = inCommand

        super().__init__(self._format())
        self.__cause__ = inCause

    @property
    def cause_type(self) -> str:
        return type(self.cause).__name__

    @property
    def cause_message(self) -> str:
        # Some native errors (e.g. TimeoutError) have an empty message
        return str(self.cause).strip() or self.cause_type

    def _format(self) -> str:
        """
        Formats the context and the root cause as a single message
        """
        context = [f'path: {self.repo_path}']
        if not isNoneOrEmptyStr(self.branch):
            context.insert(0, f'branch: {self.branch}')
        if not isNoneOrEmptyStr(self.command):
            context.append(f'command: {self.command}')

        return (
            f'`{self.operation}` failed for repo `{self.repo_name}` ({', '.join(context)})\n'
            f'{self.cause_type}: {self.cause_message}'
        )
