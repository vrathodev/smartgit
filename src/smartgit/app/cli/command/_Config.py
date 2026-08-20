""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.command._Config.py                                                                        """
""" Contains the definition of the Config subcommands for SmartGit CLI                                               """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path
from typing import Annotated, Optional

from typer import Context, Option, echo

from smartgit.app.cli.apps import CLI_APP_CONFIG
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME
from smartgit.config import ConfigType, SmartGitConfig
from smartgit.utils import getSmartLogger, isNoneOrEmpty

LOGGER = getSmartLogger(SG_VAL_CLI_LOGGER_NAME)


@CLI_APP_CONFIG.command('show')
def show_config(
    ctx: Context,
    show_path: Annotated[
        bool,
        Option(
            '--path/--no-path', '-p/-np',
            help='Shows the loaded configuration file paths'
        )
    ] = True,
    show_config: Annotated[
        bool,
        Option(
            '--config/--no-config', '-c/-nc',
            help='Shows the loaded configuration in JSON format'
        )
    ] = False,
):
    LOGGER.entrance()

    config: SmartGitConfig = ctx.obj['config']
    json_path: Optional[Path] = config.get_config_source(ConfigType.JSON)
    dotenv_path: Optional[Path] = config.get_config_source(ConfigType.DOTENV)

    if isNoneOrEmpty(json_path):
        # Should never happen
        raise Exception('Unexpected error: Configuration (JSON) could not be loaded')

    if show_path:
        if isNoneOrEmpty(dotenv_path):
            echo(f'Optional Configuration (dotenv) is not specified')
        else:
            echo(f'Configuration (dotenv) loaded from `{str(dotenv_path)}`')

        echo(f'Configuration (JSON) loaded from `{str(json_path)}`')

    if show_config:
        echo('The SmartGit `resolved` configuration is shown below')
        echo('-' * 30)
        config: SmartGitConfig = ctx.obj['config']
        echo(config.model_dump_json(indent=2))
