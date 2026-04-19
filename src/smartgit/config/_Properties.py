""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file config._Properties.py                                                                                      """
""" Contains the definition of the SmartGit configuration properties                                                 """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pathlib import Path
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, PositiveInt, StringConstraints, DirectoryPath, ConfigDict, HttpUrl

from smartgit.common.constants import (
    SG_VAL_BRANCH_NAME_DEFAULT, SG_VAL_REMOTE_NAME_DEFAULT
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

    Represents all the properties applicable to all the SmartGit primitives
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        cache_strings=True,
        extra='ignore',
        frozen=True,
        str_strip_whitespace=True,
    )

    GIT_ROOT: Annotated[Path, DirectoryPath] = Field(
        description='Base directory to store all the repositories',
        default_factory=lambda: Path.cwd().resolve()
    )

    GIT_REMOTE_BASE_URL: Annotated[SmartURL, StringProperty] = Field(
        description='Base URL of the remote to clone the repositories from',
        default=None,
        validate_default=False,
        min_length=1
    )

    GIT_DEFAULT_REMOTE: Annotated[str, StringProperty] = Field(
        description='Default remote name',
        default=SG_VAL_REMOTE_NAME_DEFAULT
    )

    GIT_DEFAULT_BRANCH: Annotated[str, StringProperty] = Field(
        description='Default branch name',
        default=SG_VAL_BRANCH_NAME_DEFAULT
    )

    GIT_SUBMODULE_INIT: bool = Field(
        description='Whether to initialize git submodules after cloning the repositories',
        default=False
    )

    GIT_FETCH_JOBS: PositiveInt = Field(
        description='Number of parallel jobs to use to fetch from the remotes',
        default=5
    )

    GIT_READONLY_MODE: bool = Field(
        description='Whether the associated repo, project or any SmartGit primitive is READ-ONLY or not',
        default=False
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
