# Configuration

SmartGit reads a JSON configuration file (`smartgit.config.json` by default) describing global properties, standalone
repositories, and projects. On startup it resolves a config file in this order:

1. `--config <path>` passed explicitly to the CLI
2. `SMARTGIT_CONFIG_PATH` environment variable
3. `smartgit.config.json` in the current working directory
4. `smartgit.config.json` next to the installed package

An optional dotenv file (`smartgit.config.env` by default, resolved the same way via `SMARTGIT_DOTENV_PATH`) can
override any property using the `GIT_` prefix (e.g. `GIT_DEFAULT_REMOTE=upstream`).

## Example `smartgit.config.json`

```json
{
    "properties": {
        "GIT_ROOT": "C:/Users/example/workspace",
        "GIT_REMOTE_BASE_URL": "https://github.com/my-org",
        "GIT_SUBMODULE_INIT": true
    },
    "repos": {
        "my-repo": {
            "properties": {
                "GIT_READONLY_MODE": true
            }
        }
    },
    "projects": {
        "my-project": {
            "repos": {
                "this-repo": null,
                "that-repo": null
            },
            "properties": {
                "GIT_FETCH_JOBS": 5,
                "GIT_SUBMODULE_INIT": true
            }
        }
    }
}
```

- `repos` — standalone repositories, each with an optional property override. A `null` value inherits the resolved
  global properties.
- `projects` — named groups of repositories. Each project can override properties for itself and for the repos it
  lists; a project-listed repo not otherwise found reuses the matching entry from the global `repos` section.
- `properties` — the base property set, cascaded down to every project and repo unless overridden.

Properties cascade **global → project → repository**, with the most specific scope winning on conflicts.

## Properties

| Property              | Type      | Default            | Description                                                                 |
|------------------------|-----------|--------------------|------------------------------------------------------------------------------|
| `GIT_ROOT`             | path      | current directory  | Base directory under which repositories are located or cloned.               |
| `GIT_REMOTE_BASE_URL`  | string    | —                  | Base URL used to derive a clone URL: `<GIT_REMOTE_BASE_URL>/<repo-name>.git`. |
| `GIT_DEFAULT_REMOTE`   | string    | `origin`           | Remote used when a command does not specify one.                             |
| `GIT_DEFAULT_BRANCH`   | string    | `main`             | Branch used when a command or config entry does not specify one.             |
| `GIT_SUBMODULE_INIT`   | bool      | `false`            | Initialize submodules after clone / smart-init.                              |
| `GIT_FETCH_JOBS`       | int       | `5`                | Parallel jobs used for `git fetch`.                                          |
| `GIT_READONLY_MODE`    | bool      | `false`            | Blocks mutating operations (e.g. branch create/delete) on this scope.        |

A repo/project name that is *not* found in `repos` or any `projects.<name>.repos` list falls back to sensible
defaults derived from the current working directory.

See also: [CLI command reference](cli-reference.md) · [Logging](logging.md)
