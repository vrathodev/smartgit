""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file common.results._Results.py                                                                                 """
""" Contains the definition of the Result data objects for SmartGit operations                                       """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from typing import Iterable, List, Literal, Optional, Self, Tuple

from pydantic import BaseModel, ConfigDict

from smartgit.common.errors import RepoOperationError


class OperationContext(BaseModel):
    """
    Represents the context (repo, path, branch, operation) an operation was executed in
    """
    model_config = ConfigDict(frozen=True)

    operation: str
    repo_name: str
    repo_path: str
    branch: Optional[str] = None
    command: Optional[str] = None


class SuccessResult(BaseModel):
    """
    Represents an operation that completed successfully
    """
    model_config = ConfigDict(frozen=True)

    status: Literal['success'] = 'success'
    context: OperationContext


class FailureResult(BaseModel):
    """
    Represents an operation that failed, localized to the repository it failed on
    """
    model_config = ConfigDict(frozen=True)

    status: Literal['failure'] = 'failure'
    context: OperationContext
    error_type: str
    error_message: str
    message: str

    @classmethod
    def from_exception(cls, inError: BaseException, inContext: OperationContext) -> Self:
        """
        Creates a FailureResult from a native/domain exception, enriched with the context of the failure

        The exception is wrapped in a RepoOperationError (unless it already is one) so that the message
        always carries the repository, path, branch and operation alongside the root cause.

        :param inError:     Native/domain exception raised by the operation
        :param inContext:   Context of the operation the exception was raised in
        :returns: The FailureResult describing the failure
        """
        cause: BaseException = inError.cause if isinstance(inError, RepoOperationError) else inError
        error = RepoOperationError(
            inCause=cause,
            inOperation=inContext.operation,
            inRepoName=inContext.repo_name,
            inRepoPath=inContext.repo_path,
            inBranch=inContext.branch,
            inCommand=inContext.command,
        )

        return cls(
            context=inContext,
            error_type=error.cause_type,
            error_message=error.cause_message,
            message=str(error),
        )


type OperationResult = SuccessResult | FailureResult


def partition_results(inResults: Iterable[OperationResult]) -> Tuple[List[SuccessResult], List[FailureResult]]:
    """
    Partitions the results into successes and failures, preserving the order

    :param inResults:   Results to partition
    :returns: Tuple of (successes, failures)
    """
    successes: List[SuccessResult] = []
    failures: List[FailureResult] = []
    for result in inResults:
        if isinstance(result, FailureResult):
            failures.append(result)
        else:
            successes.append(result)

    return successes, failures
