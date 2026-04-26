""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file config._Properties.py                                                                                      """
""" Contains the definition of the SmartGit configuration properties                                                 """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path
from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, DirectoryPath, Field, PositiveInt, StringConstraints

from smartgit.common.constants import (
    SG_VAL_BRANCH_NAME_DEFAULT, SG_VAL_REMOTE_NAME_DEFAULT,
)
from smartgit.common.types import SmartURL
from smartgit.utils import getSmartLogger

LOGGER = getSmartLogger()

StringProperty = StringConstraints(
    strip_whitespace=True,
    min_length=1
)


class Properties(BaseModel):
    """
    SmartGit Properties

    Represents the property set that can be applied at global, project, or repository scope.

    These properties act as operational defaults. More specific scopes override less specific ones during config resolution.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        cache_strings=True,
        extra='ignore',
        frozen=True,
        str_strip_whitespace=True,
        json_schema_extra={
            'examples': [
                {
                    'GIT_ROOT'           : 'C:/Users/example/workspace',
                    'GIT_REMOTE_BASE_URL': 'https://github.com/my-org',
                    'GIT_SUBMODULE_INIT' : True,
                    'GIT_READONLY_MODE'  : False,
                }
            ]
        },
    )

    GIT_ROOT: Annotated[Path, DirectoryPath] = Field(
        description='Base directory under which SmartGit locates or creates repositories. '
                    'Repository names are resolved against this path.',
        default_factory=lambda: Path.cwd().resolve(),
        examples=['C:/Users/example/workspace']
    )

    GIT_REMOTE_BASE_URL: Annotated[SmartURL, StringProperty] = Field(
        description='Base remote URL prefix used when SmartGit has to derive a repository clone URL. '
                    'For example, repo `my-repo` becomes `<GIT_REMOTE_BASE_URL>/my-repo`.',
        default=None,
        validate_default=False,
        min_length=1,
        examples=['https://github.com/my-org']
    )

    GIT_DEFAULT_REMOTE: Annotated[str, StringProperty] = Field(
        description='Default git remote name to use when a command does not explicitly specify one.',
        default=SG_VAL_REMOTE_NAME_DEFAULT,
        examples=['origin']
    )

    GIT_DEFAULT_BRANCH: Annotated[str, StringProperty] = Field(
        description='Default branch name to use when a command or config entry does not explicitly specify one.',
        default=SG_VAL_BRANCH_NAME_DEFAULT,
        examples=['main']
    )

    GIT_SUBMODULE_INIT: bool = Field(
        description='Whether SmartGit should initialize git submodules after clone or smart-init operations.',
        default=False,
        examples=[True]
    )

    GIT_FETCH_JOBS: PositiveInt = Field(
        description='Number of parallel jobs to use for git fetch operations. '
                    'Higher values can improve throughput on larger projects.',
        default=5,
        examples=[5]
    )

    GIT_READONLY_MODE: bool = Field(
        description='Marks the associated SmartGit scope as read-only. '
                    'Mutating operations should refuse to run when this is true.',
        default=False,
        examples=[False]
    )

    @classmethod
    def merge(cls, inLeft: Optional[dict[str, Any]], inRight: Optional[dict[str, Any]]):
        """
        Merges the `inRight` raw properties into `inLeft`
        On collision, Properties of `inLeft` takes precedence
        Otherwise, includes union of unique properties in both.

        :return: The merged raw properties
        """
        LOGGER.entrance()

        if inLeft is None:
            return inRight if inRight is not None else None
        elif inRight is None:
            return inLeft
        else:
            return inRight | inLeft
