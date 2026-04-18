""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._SmartGitConfig.py                                                                         """
""" Configurations settings master model for SmartGit (that composes each SmartGit primitives models)                """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import copy
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import dotenv_values
from pydantic import model_validator
from pydantic.fields import Field, FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, JsonConfigSettingsSource

from smartgit.common.constants import (
    SG_KEY_DOTENV_PATH, SG_VAL_DOTENV_PATH_DEFAULT,
    SG_KEY_CONFIG_PATH, SG_VAL_CONFIG_PATH_DEFAULT
)
from smartgit.config._ProjectConfig import ProjectConfig
from smartgit.config._Properties import Properties
from smartgit.config._RepoConfig import RepoConfig
from smartgit.utils import getSmartLogger, isNoneOrEmpty

LOGGER = getSmartLogger()


class PropertiesSettingEnvSource(PydanticBaseSettingsSource):
    """
    Custom Properties Environment Settings source
    """

    def __call__(self) -> dict[str, Any]:
        """
        Custom settings source exclusive for reading properties through env & .env

        Environment variables takes higher precedence over those defined in dotenv file
        """
        LOGGER.entrance()
        envFile: Path = Path(self.config.get('env_file', SG_VAL_DOTENV_PATH_DEFAULT))
        props: dict[str, Any] = dict()

        dotEnv = dotenv_values(envFile)
        for prop in Properties.model_fields.keys():
            if os.getenv(prop) is not None:
                props[prop] = os.getenv(prop)
            elif dotEnv.get(prop) is not None:
                props[prop] = dotEnv.get(prop)

        return {'properties': props}

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        pass


class SmartGitConfig(BaseSettings):
    """
    SmartGitConfig -- Configuration master settings for SmartGit
    """
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix='GIT_',
        env_file=Path(os.getenv(SG_KEY_DOTENV_PATH, SG_VAL_DOTENV_PATH_DEFAULT)).resolve(),
        json_file=Path(os.getenv(SG_KEY_CONFIG_PATH, SG_VAL_CONFIG_PATH_DEFAULT)).resolve(),
        extra='ignore',
        frozen=True
    )

    repos: Optional[dict[str, Optional[RepoConfig]]] = Field(
        description='Repository names -> associated configurations mapping',
        default_factory=dict
    )
    projects: Optional[dict[str, Optional[ProjectConfig]]] = Field(
        description='Project names -> associated configurations mapping',
        default_factory=dict
    )
    properties: Properties = Field(
        description='Global properties applicable to all repositories & projects, takes lower precedence over the project/repo-specific properties',
        default_factory=Properties,
    )

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            # Denotes the python object initialization i.e. MyModel(key=val)
            init_settings,
            # Environment variables
            env_settings,
            # dotenv files
            dotenv_settings,
            # Exclusive custom settings source for properties (env vars > dotenv)
            PropertiesSettingEnvSource(settings_cls),
            # Denotes the JSON configuration file i.e. smartgit.config.json
            JsonConfigSettingsSource(settings_cls),
            # Denotes secret files that define the settings
            file_secret_settings
        )

    @model_validator(mode='before')
    @classmethod
    def __resolve(cls, inRawConfig: dict[str, Any]):
        """
        Pre-processes the raw config to resolve the precedence order
        TODO: Define the configurations precedence document to explain this piece of code

        TODO: Refactor and break further into methods
        :return: The processed `raw` config instance
        """
        LOGGER.entrance()

        # Resolving global repos
        globalProps: Optional[dict[str, Any]] = inRawConfig.get('properties')
        globalRepos = inRawConfig.get('repos')
        globalRepoNames: list[str] = list()
        if isNoneOrEmpty(globalRepos):
            if isinstance(globalRepos, list) or isinstance(globalRepos, dict):
                LOGGER.debug('No global repositories configured in the loaded config')
            else:
                LOGGER.debug('Invalid global `repos` configured')
                return inRawConfig
        elif isinstance(globalRepos, list):
            # Allows repo-names to be configured as list while read as intended
            LOGGER.debug('Global repositories are configured as list, converting into the dict...')
            globalRepoNames.extend(globalRepos)
            globalRepos: dict[str, Any] = dict()
            for name in globalRepoNames:
                globalRepos[name] = None
            inRawConfig['repos'] = globalRepos

        if isNoneOrEmpty(globalProps) or not isinstance(globalProps, dict):
            LOGGER.debug('Invalid/empty global `properties` configured')
            return inRawConfig

        # Merge/propagate the global props to that of the global repos
        for name, repoConfig in globalRepos.items():
            if repoConfig is None:
                repoConfig: dict['str', Any] = dict()
                repoConfig['properties'] = None

            repoProps: Optional[dict[str, Any]] = repoConfig.get('properties')
            repoConfig['properties'] = Properties.merge(repoProps, globalProps)
            globalRepos[name] = repoConfig

        # Resolving projects
        globalProjects: Optional[dict[str, Any]] = inRawConfig.get('projects')
        if isNoneOrEmpty(globalProjects) or not isinstance(globalProjects, dict):
            LOGGER.debug('Invalid/empty global `projects` configured')
            return inRawConfig

        for name, projectConfig in globalProjects.items():
            if isNoneOrEmpty(projectConfig) or not isinstance(projectConfig, dict):
                LOGGER.debug(f'Invalid/empty `projects.{name}` configured')
                continue

            # Resolving project level repos
            projectProps: Optional[dict[str, Any]] = projectConfig.get('properties')
            projectRepos = projectConfig.get('repos')
            projectRepoNames: list[str] = list()
            if isNoneOrEmpty(projectRepos):
                if isinstance(projectRepos, list) or isinstance(projectRepos, dict):
                    LOGGER.debug(f'No `projects.{name}.repos` repositories configured in the loaded config')
                else:
                    LOGGER.debug(f'Invalid `projects.{name}.repos` configured')
                    return inRawConfig
            elif isinstance(projectRepos, list):
                # Allows repo-names to be configured as list while read as intended
                LOGGER.debug(f'projects.{name}.repos are configured as list, converting into the dict...')
                projectRepoNames.extend(projectRepos)
                projectRepos: dict[str, Any] = dict()
                for name in projectRepoNames:
                    projectRepos[name] = None
                projectConfig['repos'] = projectRepos

            if isNoneOrEmpty(projectProps) or not isinstance(projectProps, dict):
                LOGGER.debug('Invalid/empty global `properties` configured')
                return inRawConfig

            resolvedProjectProps = Properties.merge(projectProps, globalProps)
            projectConfig['properties'] = resolvedProjectProps

            # Merge/propagate the project props to that of the project repos
            for name, repoConfig in projectRepos.items():
                globalRepoConfig = globalRepos.get(name)
                if repoConfig is None:
                    if not isNoneOrEmpty(globalRepoConfig):
                        # Reuse the global repo config as fallback
                        repoConfig = copy.deepcopy(globalRepoConfig)
                        projectRepos[name] = repoConfig
                    else:
                        repoConfig: dict['str', Any] = dict()
                        repoConfig['properties'] = None

                repoProps: Optional[dict[str, Any]] = repoConfig.get('properties')
                repoConfig['properties'] = Properties.merge(repoProps, resolvedProjectProps)
                projectRepos[name] = repoConfig

        return inRawConfig
