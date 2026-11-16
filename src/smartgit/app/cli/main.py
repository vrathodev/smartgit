""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.main.py                                                                                   """
""" SmartGit Typer CLI Entrypoint                                                                                    """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from pydantic import ValidationError
from typer import Context, Option

from smartgit.app.cli.apps import CLI_APP
from smartgit.app.cli.command import _Config, _Project, _Repo
from smartgit.common.constants import (
    SG_VAL_CLI_LOGGER_NAME,
    SG_VAL_CORE_LOGGER_NAME,
    SG_VAL_EXIT_CODE_OPERATION_FAILED,
    SG_VAL_LOG_LEVEL_OFF,
)
from smartgit.common.errors import SmartGitError, SmartGitInternalError
from smartgit.config import SmartGitConfigLoader
from smartgit.utils import configSmartLogger, getSmartLogger

CLI_COMMAND_MODULES = (_Config, _Project, _Repo)


@CLI_APP.callback()
def main_callback(
    ctx: Context,
    config_path: Annotated[
        Optional[Path],
        Option('--config', help='Path to an explicit SmartGit configuration file.'),
    ] = None,
    verbosity: Annotated[
        int,
        Option('-v', count=True, help='Verbosity levels (-v: WARNING, -vv: INFO, -vvv: DEBUG)')
    ] = 0,
    quiet: Annotated[
        bool,
        Option('--quiet', '-q/-nq', help='Quiet mode. Suppresses all output except for errors.')
    ] = False
):
    """
    Initializes per-invocation CLI context

    :param ctx:             Typer shared-context for associated CLI invocation
    :param verbosity:       [Optional] Verbosity level for logging.
                            -v: WARNING, -vv: INFO, -vvv: DEBUG
                            Defaults to 0 (NOTSET), Falls back to the Log level configured in logging config
    :param quiet:           [Optional] Quiet mode. Suppresses all logging output except for errors.
    :param config_path:     [Optional] Explicit SmartGit config file path. Defaults to None
    """
    verbosity_level: int = 40 - (10 * min(verbosity, 3)) if verbosity > 0 else 0
    if quiet:
        log_level_quiet: int = logging.getLevelName(SG_VAL_LOG_LEVEL_OFF)
        if 'LEVEL' in str(log_level_quiet).upper():
            raise SmartGitInternalError(f'Unexpected error: logging.{SG_VAL_LOG_LEVEL_OFF} is expected but not defined')
        verbosity_level = log_level_quiet

    LOGGER = configSmartLogger(SG_VAL_CLI_LOGGER_NAME, verbosity_level)
    _ = configSmartLogger(SG_VAL_CORE_LOGGER_NAME, verbosity_level)

    LOGGER.entrance()

    if ctx.resilient_parsing:
        LOGGER.debug('Invoked with Resilient Parsing mode ON, skipping...')
        return

    ctx.ensure_object(dict)
    ctx.obj['config'] = SmartGitConfigLoader().load(inJSONConfigPath=config_path)
    ctx.obj['quiet'] = quiet


def main() -> None:
    """
    SmartGit CLI entrypoint

    Operational (per repository) failures never reach here, they are returned as results by SmartGit and
    rendered by the commands (see report_results). This is only the boundary for the failures outside of
    the repository operations: invalid configuration/input and internal errors.
    """
    LOGGER = getSmartLogger(SG_VAL_CLI_LOGGER_NAME)
    try:
        asyncio.run(CLI_APP())
        return
    except SmartGitInternalError as error:
        LOGGER.debug(error, exc_info=True, stack_info=True)
        message = error.display_message
    except SmartGitError as error:
        LOGGER.debug(error, exc_info=True, stack_info=True)
        message = f'Error: {error}'
    except ValidationError as error:
        LOGGER.debug(error, exc_info=True, stack_info=True)
        message = f'Error: {error}'
    except Exception as error:
        LOGGER.debug(error, exc_info=True, stack_info=True)
        message = f'Unexpected Error: {error}, Please report this issue to the SmartGit team'

    typer.echo(message, err=True)
    raise SystemExit(SG_VAL_EXIT_CODE_OPERATION_FAILED)
