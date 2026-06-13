""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.command._Repo.py                                                                          """
""" Contains the definition of the Repo subcommands for SmartGit CLI                                                 """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path
from typing import Annotated, Optional

import typer
from typer import Argument, Context, Option

from smartgit.app.cli.apps import CLI_APP_REPO
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME
from smartgit.config import ConfigType, SmartGitConfig
from smartgit.config import RepoConfig
from smartgit.core import SmartRepo
from smartgit.utils import getSmartLogger, isNoneOrEmpty

# CLI Logger
LOGGER = getSmartLogger(SG_VAL_CLI_LOGGER_NAME)


def resolve_repo(inRepoName: str, inConfig: SmartGitConfig) -> SmartRepo:
    """
    Resolves the SmartRepo instance from the CLI optional for repo name
    """
    LOGGER.entrance()

    repoBasePath: Path
    repoName: str
    repoConfig: RepoConfig

    CWD = Path.cwd().resolve().absolute()
    if not isNoneOrEmpty(inRepoName):
        repoName = inRepoName.strip()
        repoConfig = inConfig.get_repo_config(repoName)
        if isNoneOrEmpty(repoConfig):
            raise Exception(f'Repo `{repoName}` not configured in `{str(inConfig.get_config_source(ConfigType.JSON))}`')

        repoBasePath = repoConfig.properties.GIT_ROOT
    else:
        repoName = CWD.name
        repoBasePath = CWD.parent
        repoConfig = RepoConfig()

    return SmartRepo(path=repoBasePath / repoName, inRepoConfig=repoConfig)


@CLI_APP_REPO.command('create-branch')
def create_branch(
    ctx: Context,
    branch: Annotated[
        str,
        Argument(help='Name of the new branch')
    ],
    create_from: Annotated[
        str,
        Argument(help='Base reference (branch, commit, tag) to create new branch from')
    ],
    repo_name: Annotated[
        Optional[str],
        Option(
            '--repo', '-r',
            help='Name of the repo. Defaults to the name of CWD'
        )
    ] = None,
    should_push: Annotated[
        bool,
        Option(
            '--push',
            help='Pushes the new branch to the remote'
        )
    ] = False,
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
        repo: SmartRepo = resolve_repo(repo_name, config)
        repo.create_branch(
            inBranchName=branch,
            inStartPoint=create_from,
            inPushRemote=should_push,
            inRemoteName=str(remote).strip() if not isNoneOrEmpty(remote) else repo.properties.GIT_DEFAULT_REMOTE,
        )
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True, color=True)
        raise typer.Exit(code=1) from error


@CLI_APP_REPO.command('delete-branch')
def delete_branch(
    ctx: Context,
    branch: Annotated[
        str,
        Argument(help='Name of the branch')
    ],
    repo_name: Annotated[
        Optional[str],
        Option(
            '--repo', '-r',
            help='Name of the repo. Defaults to the name of CWD'
        )
    ] = None,
    from_remote: Annotated[
        bool,
        Option(
            '--from-remote',
            help='Deletes the branch from the target remote as well'
        )
    ] = False,
    force: Annotated[
        bool,
        Option(
            '--force',
            help='Forces deletion of the local branch'
        )
    ] = False,
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
        repo: SmartRepo = resolve_repo(repo_name, config)
        repo.delete_branch(
            inBranchName=branch,
            inFromRemote=from_remote,
            inRemoteName=str(remote).strip() if not isNoneOrEmpty(remote) else repo.properties.GIT_DEFAULT_REMOTE,
            inForce=force,
        )
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True, color=True)
        raise typer.Exit(code=1) from error


@CLI_APP_REPO.command('pull')
def pull(
    ctx: Context,
    repo_name: Annotated[
        Optional[str],
        Option(
            '--repo', '-r',
            help='Name of the repo. Defaults to the name of CWD'
        )
    ] = None,
    branch: Annotated[
        Optional[str],
        Option(
            '--branch',
            help='Branch name to pull. Defaults to the active branch when omitted'
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
        repo: SmartRepo = resolve_repo(repo_name, config)
        repo.pull(
            inBranchName=str(branch).strip() if not isNoneOrEmpty(branch) else None,
            inRemoteName=str(remote).strip() if not isNoneOrEmpty(remote) else repo.properties.GIT_DEFAULT_REMOTE,
        )
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True, color=True)
        raise typer.Exit(code=1) from error


@CLI_APP_REPO.command('init')
def init(
    ctx: Context,
    repo_name: Annotated[
        str,
        Argument(help='Name of the configured repo to initialize')
    ],
    branch: Annotated[
        Optional[str],
        Option(
            '--branch',
            help='Branch to switch to after initialization'
        )
    ] = None,
):
    LOGGER.entrance()
    try:
        config: SmartGitConfig = ctx.obj['config']
        repo: SmartRepo = resolve_repo(repo_name, config)
        SmartRepo.smart_init(
            inRepoName=repo.name,
            inRepoConfig=repo.config,
            inBranch=str(branch).strip() if not isNoneOrEmpty(branch) else None,
        )
    except Exception as error:
        LOGGER.exception(error)
        typer.echo(f'Error: {error}', err=True, color=True)
        raise typer.Exit(code=1) from error
