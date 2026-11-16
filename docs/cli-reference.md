# CLI Command Reference

```bash
smartgit --help
```

See [Configuration](configuration.md) for how `--config` and properties like `GIT_ROOT`/`GIT_REMOTE_BASE_URL` are
resolved.

## Global options

Apply to every subcommand:

| Option              | Description                                                              |
|---------------------|---------------------------------------------------------------------------|
| `--config PATH`     | Path to an explicit SmartGit configuration file.                          |
| `-v`, `-vv`, `-vvv`  | Increase logging verbosity (WARNING / INFO / DEBUG).                      |
| `--quiet`, `-q`     | Suppress all output except errors.                                        |

## `smartgit repo` — operate on a single repository

```bash
smartgit repo init <repo-name> [--branch BRANCH]
smartgit repo pull [--repo NAME] [--branch BRANCH] [--remote NAME]
smartgit repo create-branch <branch> <create-from> [--repo NAME] [--push/--no-push] [--remote NAME]
smartgit repo delete-branch <branch> [--repo NAME] [--from-remote] [--force/--no-force] [--remote NAME]
```

`--repo` is optional for `pull`, `create-branch`, and `delete-branch` — when omitted, SmartGit operates on the Git
repository in the current working directory.

## `smartgit project` — operate on a named group of repositories

```bash
smartgit project init <project-name> [--branch BRANCH]
smartgit project fetch <project-name> [--remote NAME] [--tags/--no-tags]
smartgit project prune <project-name> [--branches/--no-branches] [--tags/--no-tags]
smartgit project pull <project-name> [--branch BRANCH] [--remote NAME]
```

Project commands dispatch to every repository in the project concurrently via `asyncio.gather` (see
`SmartProject.afetch`/`aprune`/`apull` in `smartgit.core`), so the command's total time tracks the slowest repo
rather than the sum of all of them.

### Results and exit codes

Every repository reports its own result, and a failure in one repository
(network timeout, OS error, Git error, clone failure) does not cancel the others in batched async operations.
On the batch execution completion, the command prints a per-repository summary and
the failures with their context (operation, repository, branch, path, Git command, root cause) — no stack traces.

```text
[ OK ] repo-a: pull (main)
[FAIL] `pull` failed for repo `repo-b` (branch: main, path: C:\ws\repo-b, command: git pull --no-tags origin main)
       GitCommandError: Cmd('git') failed due to: exit code(1) ...
Summary: 1 succeeded, 1 failed
```

| Exit code | Meaning                                                                                       |
|-----------|-----------------------------------------------------------------------------------------------|
| `0`       | Every repository operation succeeded.                                                         |
| `1`       | At least one repository operation failed, or the configuration/input was invalid.             |

With `--quiet`, only the failures are printed. The full stack trace of a failure is written to the log (`-vvv` or the
log file), not to the console.

## `smartgit config` — inspect the resolved configuration

```bash
smartgit config show [--path/--no-path] [--config/--no-config]
```

Prints the configuration file paths that were loaded and, optionally, the fully-resolved configuration as JSON.
