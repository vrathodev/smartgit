""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.main.py                                                                                   """
""" SmartGit Typer CLI Entrypoint                                                                                    """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
from pathlib import Path
from typing import Annotated, Optional

import typer
from typer import Context, Option

from smartgit.app.cli.apps import CLI_APP
from smartgit.app.cli.command import _Project, _Repo
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME, SG_VAL_CORE_LOGGER_NAME
from smartgit.config import SmartGitConfigLoader
from smartgit.utils import configSmartLogger

CLI_COMMAND_MODULES = (_Project, _Repo)

# CLI Logger
LOGGER = configSmartLogger(SG_VAL_CLI_LOGGER_NAME)


@CLI_APP.callback()
def main_callback(
    ctx: Context,
    config_path: Annotated[
        Optional[Path],
        Option('--config', help='Path to an explicit SmartGit configuration file.'),
    ] = None,
):
    """
    Initializes per-invocation CLI context

    :param ctx:             Typer shared-context for associated CLI invocation
    :param config_path:     [Optional] Explicit SmartGit config file path. Defaults to None
    """
    LOGGER.entrance()
    try:
        configSmartLogger(SG_VAL_CORE_LOGGER_NAME)
        configSmartLogger(SG_VAL_CLI_LOGGER_NAME)

        ctx.ensure_object(dict)
        ctx.obj['config'] = SmartGitConfigLoader().load(inJSONConfigPath=config_path)
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error


def main() -> None:
    """
    SmartGit CLI entrypoint
    """
    try:
        asyncio.run(CLI_APP())
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error
