""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._RepoConfig.py                                                                             """
""" Configurations settings model for Repository                                                                     """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from pydantic import BaseModel, ConfigDict
from pydantic.fields import Field

from smartgit.config._Properties import Properties


class RepoConfig(BaseModel):
    """
    RepoConfig -- Configuration settings for a SmartGit repository
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
                    'properties': {
                        'GIT_DEFAULT_BRANCH': 'develop',
                        'GIT_READONLY_MODE' : True,
                    }
                }
            ]
        },
    )

    properties: Properties = Field(
        description='Repository-specific property overrides. '
                    'Takes precedence over project and global properties after config resolution.',
        default_factory=Properties
    )
