""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.main.py                                                                                   """
""" SmartGit Typer CLI Entrypoint                                                                                    """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path
from typing import Annotated, Optional

import typer
from typer import Context, Option

from smartgit.app.cli.apps import CLI_APP
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME
from smartgit.config import SmartGitConfigLoader
from smartgit.utils import configSmartLogger


@CLI_APP.callback()
def main_callback(
    inCTX: Context,
    inConfigPath: Annotated[
        Optional[Path],
        Option('--config', help='Path to an explicit SmartGit configuration file.'),
    ] = None,
):
    """
    Initializes per-invocation CLI context

    :param inCTX:           Typer shared-context for associated CLI invocation
    :param inConfigPath:    [Optional] Explicit SmartGit config file path. Defaults to None
    """
    try:
        inCTX.ensure_object(dict)
        inCTX.obj['config'] = SmartGitConfigLoader().load(inConfigPath)

        configSmartLogger(SG_VAL_CLI_LOGGER_NAME)
    except Exception as error:
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error


def main() -> None:
    """
    SmartGit CLI entrypoint
    """
    CLI_APP()
