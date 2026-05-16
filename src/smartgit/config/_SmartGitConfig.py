""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" @file smartgit.config._SmartGitConfig.py                                                                         """
""" Configurations settings master model for SmartGit (that composes each SmartGit primitives models)                """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import copy
import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import model_validator
from pydantic.fields import Field
from pydantic_settings import BaseSettings, JsonConfigSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict

from smartgit.common.constants import (
    SG_KEY_CONFIG_PATH,
    SG_KEY_DOTENV_PATH,
    SG_VAL_CONFIG_PATH_DEFAULT,
    SG_VAL_DOTENV_PATH_DEFAULT,
)
from smartgit.config._ProjectConfig import ProjectConfig
from smartgit.config._Properties import Properties
from smartgit.config._RepoConfig import RepoConfig
from smartgit.utils import getSmartLogger, isNoneOrEmpty

LOGGER = getSmartLogger()


class SmartGitConfig(BaseSettings):
    """
    SmartGitConfig -- Configuration master settings for SmartGit
    """

    def __init__(self, inJSONConfigPath: Optional[Path] = None, inEnvConfigPath: Optional[Path] = None, **kwargs):
        """
        Forward constructor to parameterize the Config path
        as model_config is initialized at compile time.
        :param inJSONConfigPath:    The Configuration (config.json) file path
        :param inEnvConfigPath:     The Environment Configuration (.env) file path
        :param kwargs:              BaseSettings recognized Keyword-args
        """

        def load_config(inConfig: Optional[Path]) -> Optional[dict[str, Any]]:
            """Internal helper method to load config"""
            if isNoneOrEmpty(inConfig):
                LOGGER.debug(f'`{inConfig=}` is invalid/empty')
                return None
            if not (inConfig.exists() and inConfig.is_file()):
                LOGGER.debug(f'Configuration `{inConfig}` either does not exist or is not a file.')
                return None

            try:
                config: dict[str, Any] = None
                with inConfig.open(mode='r', encoding='utf-8') as file:
                    config = json.load(file)
                return config
            except (json.JSONDecodeError, Exception) as e:
                LOGGER.exception(f'Failed to load configuration from `{inConfig.resolve()}`: {e}')
                return None

        # Load JSON configuration
        configSource: Path = None
        config: Optional[dict[str, Any]] = load_config(inJSONConfigPath)
        if config is None:
            LOGGER.debug(f'Proceeding to load the fallback configuration from env.{SG_KEY_CONFIG_PATH}...')

            fallbackConfigPath: Path = Path(os.getenv(SG_KEY_CONFIG_PATH, SG_VAL_CONFIG_PATH_DEFAULT)).resolve()
            config = load_config(fallbackConfigPath)
            if config is None:
                LOGGER.warning('Proceeding with the empty configuration to fallback to the Config models defaults')
                config = dict()
            else:
                configSource = fallbackConfigPath
        else:
            configSource = Path(inJSONConfigPath).resolve()

        # Load Environment configuration
        envConfigSource: Path = None
        if isNoneOrEmpty(inEnvConfigPath):
            envConfigSource = Path(os.getenv(SG_KEY_DOTENV_PATH, SG_VAL_DOTENV_PATH_DEFAULT)).resolve()
            if not (envConfigSource.exists() and envConfigSource.is_file()):
                LOGGER.warning(f'Failed to load environment configuration from `{inEnvConfigPath}`, skipping...')
        else:
            envConfigSource = Path(inEnvConfigPath).resolve()

        if not isNoneOrEmpty(configSource):
            LOGGER.info(f'SmartGit configured from file: `{configSource}`')
        if not isNoneOrEmpty(envConfigSource):
            LOGGER.info(f'SmartGit configured from file: `{envConfigSource}`')

        super().__init__(**{**config, **kwargs}, _env_file=envConfigSource)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix='GIT_',
        env_nested_delimiter='',
        extra='ignore',
        frozen=True,
        json_schema_extra={
            'examples': [
                {
                    'properties': {
                        'GIT_ROOT'           : 'C:/Users/example/workspace',
                        'GIT_REMOTE_BASE_URL': 'https://github.com/my-org',
                        'GIT_SUBMODULE_INIT' : True,
                    },
                    'repos'     : {
                        'my-repo': {
                            'properties': {
                                'GIT_READONLY_MODE': True
                            }
                        }
                    },
                    'projects'  : {
                        'my-project': {
                            'repos'     : {
                                'this-repo': None,
                                'that-repo': None,
                            },
                            'properties': {
                                'GIT_FETCH_JOBS'    : 5,
                                'GIT_SUBMODULE_INIT': True,
                            }
                        }
                    }
                }
            ]
        },
    )

    repos: Optional[dict[str, Optional[RepoConfig]]] = Field(
        description='Standalone repositories mapped by repository name or path to optional repository-specific '
                    'configuration.',
        default_factory=dict,
    )
    projects: Optional[dict[str, Optional[ProjectConfig]]] = Field(
        description='Named project groups mapped to project configuration. '
                    'Each project can declare its own repos and scoped property overrides.',
        default_factory=dict
    )
    properties: Properties = Field(
        description='Global default properties applied to all repositories and projects before project-level and '
                    'repo-level overrides are merged in.',
        default_factory=Properties
    )

    def get_master_config_source(self) -> Path:
        """
        Retrieves the master configuration source (*.config.json)
        :return: The master configuration source path
        """
        configPath: Optional[Path] = self.model_config.get('json_file')
        # Should never happen
        assert not isNoneOrEmpty(configPath)

        return configPath.resolve()

    def get_project_config(self, inProjectName: str) -> Optional[ProjectConfig]:
        """
        Retrieves the associated Project config from the Project name
        :param inProjectName: The Project name
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inProjectName):
            raise ValueError(f'{inProjectName=} can not be None or empty')

        return self.projects.get(inProjectName.strip())

    def get_repo_config(self, inRepoName: str) -> Optional[RepoConfig]:
        """
        Retrieves the associated Repo config from the Repo name
        :param inRepoName: The Repo name
        """
        LOGGER.entrance()

        if isNoneOrEmpty(inRepoName):
            raise ValueError(f'{inRepoName=} can not be None or empty')

        inRepoName = inRepoName.strip()
        repoConfig: Optional[RepoConfig] = None
        if not isNoneOrEmpty(self.repos) and not isNoneOrEmpty(self.repos.get(inRepoName)):
            return self.repos.get(inRepoName)
        LOGGER.debug(f'{inRepoName} is not specified in the global `repos` section, checking in `Projects` section')

        matchProject: str = None
        for name, projectConfig in self.projects.items():
            if not (isNoneOrEmpty(projectConfig) or
                    isNoneOrEmpty(projectConfig.repos) or
                    isNoneOrEmpty(projectConfig.repos.get(inRepoName))):
                if isNoneOrEmpty(matchProject):
                    matchProject = name
                    repoConfig = projectConfig.repos.get(inRepoName)
                else:
                    raise Exception(
                        f'Can not determine the repository config source. '
                        f'As {inRepoName} is not specified in the global `repos`, '
                        f'but in multiple projects: {matchProject, name}'
                    )

        return repoConfig

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

        # Merge/propagate the global props to that of the global repos
        if isNoneOrEmpty(globalProps):
            LOGGER.debug('Empty global `properties` configured')
        else:
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

        for projectName, projectConfig in globalProjects.items():
            if isNoneOrEmpty(projectConfig) or not isinstance(projectConfig, dict):
                LOGGER.debug(f'Invalid/empty `projects.{projectName}` configured')
                continue

            # Resolving project level repos
            projectProps: Optional[dict[str, Any]] = projectConfig.get('properties')
            projectRepos = projectConfig.get('repos')
            projectRepoNames: list[str] = list()
            if isNoneOrEmpty(projectRepos):
                if isinstance(projectRepos, list) or isinstance(projectRepos, dict):
                    LOGGER.debug(f'No `projects.{projectName}.repos` repositories configured in the loaded config')
                else:
                    LOGGER.debug(f'Invalid `projects.{projectName}.repos` configured')
                    return inRawConfig
            elif isinstance(projectRepos, list):
                # Allows repo-names to be configured as list while read as intended
                LOGGER.debug(f'`projects.{projectName}.repos` are configured as list, converting into the dict...')
                projectRepoNames.extend(projectRepos)
                projectRepos: dict[str, Any] = dict()
                for repoName in projectRepoNames:
                    projectRepos[repoName] = None
                projectConfig['repos'] = projectRepos

            if isNoneOrEmpty(projectProps) or not isinstance(projectProps, dict):
                LOGGER.debug(f'Invalid/empty `projects.{projectName}.properties` configured')

            resolvedProjectProps = Properties.merge(projectProps, globalProps)
            projectConfig['properties'] = resolvedProjectProps

            # Merge/propagate the project props to that of the project repos
            for repoName, repoConfig in projectRepos.items():
                globalRepoConfig = globalRepos.get(repoName)
                if repoConfig is None:
                    if not isNoneOrEmpty(globalRepoConfig):
                        # Reuse the global repo config as fallback
                        repoConfig = copy.deepcopy(globalRepoConfig)
                        projectRepos[repoName] = repoConfig
                    else:
                        repoConfig: dict['str', Any] = dict()
                        repoConfig['properties'] = None

                repoProps: Optional[dict[str, Any]] = repoConfig.get('properties')
                repoConfig['properties'] = Properties.merge(repoProps, resolvedProjectProps)
                projectRepos[repoName] = repoConfig

        return inRawConfig
