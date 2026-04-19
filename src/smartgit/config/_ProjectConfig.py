""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._ProjectConfig.py                                                                          """
""" Configurations settings model for SmartGit Projects                                                              """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.fields import Field

from smartgit.config._Properties import Properties
from smartgit.config._RepoConfig import RepoConfig


class ProjectConfig(BaseModel):
    """
    ProjectConfig -- Configuration settings for a SmartGit project
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        cache_strings=True,
        extra='ignore',
        frozen=True,
        str_strip_whitespace=True,
    )

    repos: Optional[dict[str, Optional[RepoConfig]]] = Field(
        description='Repository names -> associated configurations mapping',
        default_factory=dict
    )
    properties: Properties = Field(
        description='Project-specific properties, takes precedence over global properties but lower than repo-specific properties',
        default_factory=Properties
    )
