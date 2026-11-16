""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.app.cli.command._Repo.py                                                                          """
""" Contains the definition of the Repo subcommands for SmartGit CLI                                                 """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path
from typing import Annotated, Callable, Optional, Tuple

from typer import Argument, Context, Option

from smartgit.app.cli._Reporting import report_results
from smartgit.app.cli.apps import CLI_APP_REPO
from smartgit.common.constants import SG_VAL_CLI_LOGGER_NAME
from smartgit.common.results import OperationResult
from smartgit.config import Properties, RepoConfig
from smartgit.config import SmartGitConfig
from smartgit.core import SmartRepo
from smartgit.utils import getSmartLogger, isNoneOrEmpty

# CLI Logger
LOGGER = getSmartLogger(SG_VAL_CLI_LOGGER_NAME)


def resolve_repo(inRepoName: str, inConfig: SmartGitConfig) -> Tuple[Optional[SmartRepo], OperationResult]:
    """
    Resolves the SmartRepo instance from the CLI optional for repo name

    :returns: Tuple of (SmartRepo or None if it failed to initialize, result of the initialization)
    """
    LOGGER.entrance()

    if not isNoneOrEmpty(inRepoName):
        return SmartRepo.try_from_config(inRepoName, inConfig)

    # Repo is NOT configured
    CWD = Path.cwd().resolve().absolute()
    repoName: str = CWD.name
    repoConfig: RepoConfig = RepoConfig(properties=Properties(GIT_ROOT=CWD.parent))

    # Current Repo operations are intended to be sync
    return SmartRepo.try_init(repoName, repoConfig)


def run_on_repo(
    inContext: Context,
    inRepoName: Optional[str],
    inOperation: Callable[[SmartRepo], OperationResult]
) -> None:
    """
    Resolves the repo, runs the operation on it and reports the result (exits non-zero on failure)
    """
    LOGGER.entrance()

    repo, initResult = resolve_repo(inRepoName, inContext.obj['config'])
    report_results(inContext, [initResult if repo is None else inOperation(repo)])


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
            '--repo',
            help='Name of the repo. Defaults to the name of CWD'
        )
    ] = None,
    should_push: Annotated[
        bool,
        Option(
            '--push/--no-push',
            help='Pushes the new branch to the remote'
        )
    ] = False,
    remote: Annotated[
        Optional[str],
        Option(
            '--remote', '-r',
            help='Name of the remote'
        )
    ] = None,
):
    LOGGER.entrance()

    run_on_repo(
        ctx,
        repo_name,
        lambda repo: repo.create_branch(
            inBranchName=branch,
            inStartPoint=create_from,
            inPushRemote=should_push,
            inRemoteName=str(remote).strip() if not isNoneOrEmpty(remote) else repo.properties.GIT_DEFAULT_REMOTE,
        )
    )


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
            '--repo',
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
            '--force/--no-force',
            help='Forces deletion of the local branch'
        )
    ] = False,
    remote: Annotated[
        Optional[str],
        Option(
            '--remote', '-r',
            help='Name of the remote'
        )
    ] = None,
):
    LOGGER.entrance()

    run_on_repo(
        ctx,
        repo_name,
        lambda repo: repo.delete_branch(
            inBranchName=branch,
            inFromRemote=from_remote,
            inRemoteName=str(remote).strip() if not isNoneOrEmpty(remote) else repo.properties.GIT_DEFAULT_REMOTE,
            inForce=force,
        )
    )


@CLI_APP_REPO.command('pull')
def pull(
    ctx: Context,
    repo_name: Annotated[
        Optional[str],
        Option(
            '--repo',
            help='Name of the repo. Defaults to the name of CWD'
        )
    ] = None,
    branch: Annotated[
        Optional[str],
        Option(
            '--branch', '-b',
            help='Branch name to pull. Defaults to the active branch when omitted'
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

    run_on_repo(
        ctx,
        repo_name,
        lambda repo: repo.pull(
            inBranchName=str(branch).strip() if not isNoneOrEmpty(branch) else None,
            inRemoteName=str(remote).strip() if not isNoneOrEmpty(remote) else repo.properties.GIT_DEFAULT_REMOTE,
        )
    )


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
            '--branch', '-b',
            help='Branch to switch to after initialization'
        )
    ] = None,
):
    # TODO: Fix branch usage
    LOGGER.entrance()

    config: SmartGitConfig = ctx.obj['config']
    _, initResult = resolve_repo(repo_name, config)
    report_results(ctx, [initResult])
