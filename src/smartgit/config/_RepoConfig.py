""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._RepoConfig.py                                                                             """
""" Configurations settings model for Repository                                                                     """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pydantic import BaseModel
from pydantic.fields import Field
from pydantic_settings import SettingsConfigDict

from smartgit.config._Properties import Properties


class RepoConfig(BaseModel):
    """
    RepoConfig -- Configuration settings for a SmartGit repository
    """
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix='GIT_',
        extra='ignore',
        frozen=True
    )

    properties: Properties = Field(
        description='Repository-specific properties, takes precedence over its inheritance hierarchy of the properties',
        default_factory=Properties
    )
