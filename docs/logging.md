# Logging

SmartGit configures two loggers: `smartgit` (core) and `smartgit-cli` (CLI). By default it loads
`logging.config.json` (a standard `logging.config.dictConfig` schema) if present, falling back to a basic
console/file configuration otherwise.

## Environment variables

| Variable                       | Purpose                                          |
|---------------------------------|---------------------------------------------------|
| `SMARTGIT_LOGGING_CONFIG_PATH`  | Path to a `dictConfig`-style JSON logging config.  |
| `SMARTGIT_LOG_LEVEL`            | Fallback log level when no config file is loaded.  |
| `SMARTGIT_LOG_PATH`             | Fallback log file path when no config file is loaded. |

The `-v`/`-vv`/`-vvv` and `--quiet` CLI flags (see the [CLI reference](cli-reference.md)) override the configured
level for the current invocation.
