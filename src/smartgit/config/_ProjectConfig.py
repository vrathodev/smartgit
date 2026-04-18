""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._ProjectConfig.py                                                                          """
""" Configurations settings model for SmartGit Projects                                                              """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from typing import Optional

from pydantic import BaseModel
from pydantic.fields import Field
from pydantic_settings import SettingsConfigDict

from smartgit.config._RepoConfig import RepoConfig
from smartgit.config._Properties import Properties


class ProjectConfig(BaseModel):
    """
    ProjectConfig -- Configuration settings for a SmartGit project
    """
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix='GIT_',
        extra='ignore',
        frozen=True
    )

    repos: Optional[dict[str, Optional[RepoConfig]]] = Field(
        description='Repository names -> associated configurations mapping',
        default_factory=dict
    )
    properties: Properties = Field(
        description='Project-specific properties, takes precedence over global properties but lower than repo-specific properties',
        default_factory=Properties
    )
