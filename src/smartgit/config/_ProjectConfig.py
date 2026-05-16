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
        json_schema_extra={
            'examples': [
                {
                    'repos'     : {
                        'sc-utils'  : None,
                        'sc-runtime': {
                            'properties': {
                                'GIT_DEFAULT_BRANCH': 'release/10.3'
                            }
                        }
                    },
                    'properties': {
                        'GIT_FETCH_JOBS'    : 8,
                        'GIT_SUBMODULE_INIT': True,
                    }
                }
            ]
        },
    )

    repos: Optional[dict[str, Optional[RepoConfig]]] = Field(
        description='Repository names mapped to optional repository-specific config. '
                    'A null value means the repo participates in the project, '
                    'Fallbacks to the configuration defined in global `repos`'
                    'Otherwise, the project/global defaults.',
        default_factory=dict
    )
    properties: Properties = Field(
        description='Project-scoped property overrides. Takes precedence over global properties '
                    'but are overridden by repo-specific properties.',
        default_factory=Properties
    )
