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
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME, SG_VAL_CORE_LOGGER_NAME, SG_VAL_LOG_LEVEL_OFF
from smartgit.common.errors import SmartGitError, SmartGitInternalError
from smartgit.config import SmartGitConfig, SmartGitConfigLoader
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
        Option('--quiet', '-q', help='Quiet mode. Suppresses all output except for errors.')
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


def main() -> None:
    """
    SmartGit CLI entrypoint
    """
    try:
        asyncio.run(CLI_APP())
    except SmartGitInternalError as error:
        getSmartLogger(SG_VAL_CLI_LOGGER_NAME).exception(error, exc_info=True, stack_info=True)
        typer.echo(error.display_message, err=True)
        raise typer.Exit(code=1) from error
    except SmartGitError as error:
        getSmartLogger(SG_VAL_CLI_LOGGER_NAME).exception(error, exc_info=True, stack_info=True)
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error
    except ValidationError as error:
        getSmartLogger(SG_VAL_CLI_LOGGER_NAME).exception(error, exc_info=True, stack_info=True)
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        getSmartLogger(SG_VAL_CLI_LOGGER_NAME).exception(error, exc_info=True, stack_info=True)
        typer.echo(
            f'Unexpected Error: {error}, '
            f'Please report this issue to the SmartGit team',
            err=True
        )
        raise typer.Exit(code=1) from error
