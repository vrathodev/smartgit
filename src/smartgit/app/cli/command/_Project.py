""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.command._Project.py                                                                       """
""" Contains the definition of the Project subcommands for SmartGit CLI                                              """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
from typing import Annotated, Optional

import typer
from typer import Argument, Context, Option

from smartgit.app.cli.apps import CLI_APP_PROJECT
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME
from smartgit.config import ConfigType
from smartgit.config import ProjectConfig
from smartgit.config import SmartGitConfig
from smartgit.core import SmartProject
from smartgit.utils import getSmartLogger, isNoneOrEmpty

# CLI Logger
LOGGER = getSmartLogger(SG_VAL_CLI_LOGGER_NAME)


def resolve_project(inProjectName: str, inConfig: SmartGitConfig) -> SmartProject:
    """
    Resolves the SmartProject instance from the CLI project name
    """
    LOGGER.entrance()

    if isNoneOrEmpty(inProjectName):
        raise ValueError(f'{inProjectName=} cannot be None or empty')

    projectName = inProjectName.strip()
    projectConfig: ProjectConfig = inConfig.get_project_config(inProjectName=projectName)
    if isNoneOrEmpty(projectConfig):
        raise ValueError(f'Project `{projectName}` not configured in `{str(inConfig.get_config_source(ConfigType.JSON))}`')

    return SmartProject(inProjectName=projectName, inProjectConfig=projectConfig)


@CLI_APP_PROJECT.command('fetch')
def fetch(
    ctx: Context,
    project: Annotated[
        str,
        Argument(help='Name of the project')
    ],
    remote: Annotated[
        Optional[str],
        Option(
            '--remote',
            help='Name of the remote'
        )
    ] = None,
    fetch_tags: Annotated[
        bool,
        Option(
            '--tags',
            help='Fetches the tags'
        )
    ] = False,
):
    LOGGER.entrance()
    try:
        config: SmartGitConfig = ctx.obj['config']
        smartProject: SmartProject = SmartProject.from_config(inProjectName=project, inConfig=config)
        asyncio.run(
            smartProject.afetch(
                inRemote=str(remote).strip() if not isNoneOrEmpty(remote) else smartProject.properties.GIT_DEFAULT_REMOTE,
                inSkipTags=not fetch_tags
            )
        )
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error


@CLI_APP_PROJECT.command('prune')
def prune(
    ctx: Context,
    project: Annotated[
        str,
        Argument(help='Name of the project')
    ],
    prune_branches: Annotated[
        bool,
        Option(
            '--branches',
            help='Prunes remote-tracking branches'
        )
    ] = False,
    prune_tags: Annotated[
        bool,
        Option(
            '--tags',
            help='Prunes fetched tags'
        )
    ] = False,
):
    LOGGER.entrance()
    try:
        config: SmartGitConfig = ctx.obj['config']
        smartProject: SmartProject = SmartProject.from_config(inProjectName=project, inConfig=config)
        asyncio.run(
            smartProject.aprune(
                inPruneBranches=prune_branches,
                inPruneTags=prune_tags,
            )
        )
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error


@CLI_APP_PROJECT.command('pull')
def pull(
    ctx: Context,
    project: Annotated[
        str,
        Argument(help='Name of the project')
    ],
    branch: Annotated[
        Optional[str],
        Option(
            '--branch',
            help='Name of the branch. Defaults to the active branch when omitted'
        )
    ] = None,
    remote: Annotated[
        Optional[str],
        Option(
            '--remote',
            help='Name of the remote'
        )
    ] = None,
):
    LOGGER.entrance()
    try:
        config: SmartGitConfig = ctx.obj['config']
        smartProject: SmartProject = resolve_project(inProjectName=project, inConfig=config)
        asyncio.run(
            smartProject.apull(
                inBranchName=str(branch).strip() if not isNoneOrEmpty(branch) else None,
                inRemoteName=str(remote).strip() if not isNoneOrEmpty(
                    remote
                ) else smartProject.properties.GIT_DEFAULT_REMOTE,
            )
        )
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error


@CLI_APP_PROJECT.command('init')
def init_project(
    ctx: Context,
    project: Annotated[
        str,
        Argument(help='Name of the project')
    ],
    branch: Annotated[
        Optional[str],
        Option(
            '--branch',
            help='Name of the branch to switch to after initialization'
        )
    ] = None,
):
    LOGGER.entrance()
    try:
        config: SmartGitConfig = ctx.obj['config']
        smartProject: SmartProject = resolve_project(inProjectName=project, inConfig=config)
        asyncio.run(
            SmartProject.asmart_init(
                inProjectName=smartProject.name,
                inProjectConfig=smartProject.config,
                inBranch=str(branch).strip() if not isNoneOrEmpty(branch) else None,
            )
        )
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True)
        raise typer.Exit(code=1) from error
