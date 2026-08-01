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
from smartgit.app.cli.command import _Config, _Project, _Repo
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME, SG_VAL_CORE_LOGGER_NAME
from smartgit.config import SmartGitConfigLoader
from smartgit.utils import configSmartLogger

CLI_COMMAND_MODULES = (_Config, _Project, _Repo)

# Logger instances
LOGGER = configSmartLogger(SG_VAL_CLI_LOGGER_NAME)
_ = configSmartLogger(SG_VAL_CORE_LOGGER_NAME)


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
                            Defaults to 0 (ERROR)
    :param quiet:           [Optional] Quiet mode. Suppresses all logging output except for errors.
    :param config_path:     [Optional] Explicit SmartGit config file path. Defaults to None
    """
    LOGGER.entrance()

    if ctx.resilient_parsing:
        LOGGER.debug('Invoked with Resilient Parsing mode ON, skipping...')
        return

    # TODO:
    #  configSmartLogger() logs already, before quiet mode is identified here,
    #  resolve multiple loggers maintenance overhead for CLI, Core, MCP, etc.
    verbosity_level: int = 40 - (10 * min(verbosity, 3)) if not quiet else 0
    LOGGER.setLevel(verbosity_level)
    _.setLevel(verbosity_level)

    try:
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
