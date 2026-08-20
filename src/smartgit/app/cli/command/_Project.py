""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.command._Project.py                                                                       """
""" Contains the definition of the Project subcommands for SmartGit CLI                                              """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import asyncio
import functools
from typing import Annotated, Optional

from typer import Argument, Context, Option

from smartgit.app.cli.apps import CLI_APP_PROJECT
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME
from smartgit.config import SmartGitConfig
from smartgit.core import SmartProject
from smartgit.utils import getSmartLogger, isNoneOrEmpty

# CLI Logger
LOGGER = getSmartLogger(SG_VAL_CLI_LOGGER_NAME)


def async_command(afunc):
    """Decorator that accepts async function for typer sync command method"""

    @functools.wraps(afunc)
    def wrapper(*args, **kwargs):
        return asyncio.run(afunc(*args, **kwargs))

    return wrapper


@CLI_APP_PROJECT.command('fetch')
@async_command
async def fetch(
    ctx: Context,
    project: Annotated[
        str,
        Argument(help='Name of the project')
    ],
    remote: Annotated[
        Optional[str],
        Option(
            '--remote', '-r',
            help='Name of the remote'
        )
    ] = None,
    fetch_tags: Annotated[
        bool,
        Option(
            '--tags/--no-tags', '-t/-nt',
            help='Fetches the tags'
        )
    ] = False,
):
    LOGGER.entrance()

    config: SmartGitConfig = ctx.obj['config']
    smartProject: SmartProject = await SmartProject.from_config_async(inProjectName=project, inConfig=config)
    await smartProject.afetch(
        inRemote=str(remote).strip() if not isNoneOrEmpty(remote) else smartProject.properties.GIT_DEFAULT_REMOTE,
        inSkipTags=not fetch_tags
    )


@CLI_APP_PROJECT.command('prune')
@async_command
async def prune(
    ctx: Context,
    project: Annotated[
        str,
        Argument(help='Name of the project')
    ],
    remote: Annotated[
        Optional[str],
        Option(
            '--remote', '-r',
            help='Name of the remote'
        )
    ] = None,
    prune_branches: Annotated[
        bool,
        Option(
            '--branches/--no-branches', '-b/-nb',
            help='Prunes remote-tracking branches'
        )
    ] = False,
    prune_tags: Annotated[
        bool,
        Option(
            '--tags/--no-tags', '-t/-nt',
            help='Prunes fetched tags'
        )
    ] = False,
):
    # TODO: Fix remote usage
    LOGGER.entrance()

    config: SmartGitConfig = ctx.obj['config']
    smartProject: SmartProject = await SmartProject.from_config_async(inProjectName=project, inConfig=config)
    await smartProject.aprune(inPruneBranches=prune_branches, inPruneTags=prune_tags)


@CLI_APP_PROJECT.command('pull')
@async_command
async def pull(
    ctx: Context,
    project: Annotated[
        str,
        Argument(help='Name of the project')
    ],
    branch: Annotated[
        Optional[str],
        Option(
            '--branch', '-b',
            help='Name of the branch. Defaults to the active branch when omitted'
        )
    ] = None,
    remote: Annotated[
        Optional[str],
        Option(
            '--remote', '-r',
            help='Name of the remote'
        )
    ] = None,
):
    LOGGER.entrance()

    config: SmartGitConfig = ctx.obj['config']
    smartProject: SmartProject = await SmartProject.from_config_async(inProjectName=project, inConfig=config)
    await smartProject.apull(
        inBranchName=str(branch).strip() if not isNoneOrEmpty(branch) else None,
        inRemoteName=str(remote).strip() if not isNoneOrEmpty(remote) else smartProject.properties.GIT_DEFAULT_REMOTE,
    )


@CLI_APP_PROJECT.command('init')
@async_command
async def init(
    ctx: Context,
    project: Annotated[
        str,
        Argument(help='Name of the project')
    ],
    branch: Annotated[
        Optional[str],
        Option(
            '--branch', '-b',
            help='Name of the branch to switch to after initialization'
        )
    ] = None,
):
    LOGGER.entrance()

    config: SmartGitConfig = ctx.obj['config']
    smartProject: SmartProject = await SmartProject.from_config_async(inProjectName=project, inConfig=config)
    await SmartProject.asmart_init(
        inProjectName=smartProject.name,
        inProjectConfig=smartProject.config,
        inBranch=str(branch).strip() if not isNoneOrEmpty(branch) else None,
    )
