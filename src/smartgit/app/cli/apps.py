""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.apps.py                                                                                   """
""" SmartGit Typer CLI app instances                                                                                 """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from typer import Typer

from smartgit.common.constants import SG_VAL_APP_NAME

CLI_APP_REPO = Typer(
    name=f'{SG_VAL_APP_NAME}.repo',
    no_args_is_help=True
)

CLI_APP_PROJECT = Typer(
    name=f'{SG_VAL_APP_NAME}.project',
    no_args_is_help=True
)

CLI_APP_CONFIG = Typer(
    name=f'{SG_VAL_APP_NAME}.config',
    no_args_is_help=True
)

CLI_APP = Typer(
    name=SG_VAL_APP_NAME,
    no_args_is_help=True
)

CLI_APP.add_typer(CLI_APP_REPO, name='repo')
CLI_APP.add_typer(CLI_APP_PROJECT, name='project')
CLI_APP.add_typer(CLI_APP_CONFIG, name='config')
