""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file app.cli._Reporting.py                                                                                      """
""" Renders the SmartGit operation results for the CLI                                                               """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from typing import Iterable

import typer
from typer import Context

from smartgit.common.constants import SG_VAL_EXIT_CODE_OPERATION_FAILED
from smartgit.common.results import FailureResult, OperationResult, SuccessResult, partition_results


def _describe(inResult: OperationResult) -> str:
    """
    Describes the operation a result belongs to, e.g. `pull (main)`
    """
    context = inResult.context

    return f'{context.operation} ({context.branch})' if context.branch else context.operation


def report_results(inContext: Context, inResults: Iterable[OperationResult]) -> None:
    """
    Renders the summary of the results and exits with a non-zero code if any of the operations failed

    :param inContext:   Typer context of the invocation (quiet mode is read from it)
    :param inResults:   Results of the operations executed by the command
    :raises typer.Exit: With a non-zero code if the results contain any failure
    """
    quiet: bool = bool((inContext.obj or {}).get('quiet', False))
    successes, failures = partition_results(sorted(inResults, key=lambda result: result.context.repo_name))

    if not quiet:
        _render_successes(successes)
    _render_failures(failures)
    if not quiet:
        typer.echo(f'Summary: {len(successes)} succeeded, {len(failures)} failed')

    if failures:
        raise typer.Exit(code=SG_VAL_EXIT_CODE_OPERATION_FAILED)


def _render_successes(inSuccesses: Iterable[SuccessResult]) -> None:
    for success in inSuccesses:
        typer.echo(f'[ OK ] {success.context.repo_name}: {_describe(success)}')


def _render_failures(inFailures: Iterable[FailureResult]) -> None:
    for failure in inFailures:
        # The message already carries the repo, path, branch and operation alongside the root cause
        head, *details = failure.message.splitlines()
        typer.echo(f'[FAIL] {head}', err=True)
        for detail in details:
            typer.echo(f'       {detail}', err=True)
