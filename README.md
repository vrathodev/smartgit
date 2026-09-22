# SmartGit

Once you own more than a handful of related Git repositories, the same handful of Git commands stop being a
one-liner. Onboarding a new machine means cloning a dozen repos by hand. A routine fetch-and-prune becomes a
`for` loop (or a spreadsheet of repo names) that someone has to remember to run, repo by repo, one at a time.
SmartGit turns that repeated, sequential, easy-to-get-wrong process into one declarative config file and one
command — run concurrently across every repository it touches.

You describe your repositories and *projects* (named groups of related repositories) once, in a single JSON
configuration file, with properties that cascade from global → project → repository scope. SmartGit then drives
Git for you: cloning what's missing, fetching, pruning, pulling, and managing branches — either against a single
repo, or fanned out asynchronously across an entire project at once.

## Who it's for

- **Developers juggling many related repos** — SDKs split across languages, a service split into several
  repositories, or simply a personal workspace with dozens of independent clones — who are tired of `cd`-ing into
  each one to run the same Git command.
- **Platform/DevOps engineers** doing fleet-wide Git hygiene — nightly fetch + prune across every repo an
  organization owns, or standardized branch creation/cleanup across a project's repos.
- **Teams standardizing repo setup** — onboarding a new machine or environment by declaring "these repos, from this
  base URL, into this layout" once, instead of scripting a series of `git clone` calls.
- **CI/CD pipelines bootstrapping source environments** — a pipeline stage that needs a full, up-to-date checkout of
  every repository a build/test job depends on can call `smartgit project init`/`fetch` against the same config used
  locally, instead of maintaining a bespoke clone script per pipeline.

If your workflow is "one repo, occasionally," a plain `git` CLI is all you need. SmartGit earns its keep once you're
regularly running the *same* Git operation across a *set* of repositories — locally or in an automated environment.

## How it works

- **Layered configuration** — global, project, and repository-scoped properties (remote base URL, default
  branch/remote, submodule init, read-only mode, etc.) resolve into one effective config per repo.
- **Smart init** — locates a repository under its configured root if it already exists, otherwise clones it from
  the configured remote base URL, then optionally checks out a branch and initializes submodules.
- **Async multi-repo execution** — project-level operations run concurrently across every repository in the
  project (`asyncio.gather`), with each repo's Git call itself running as a non-blocking subprocess rather than a
  blocking call handed off to a thread. Fetching 20 repositories takes roughly as long as fetching the slowest one,
  not the sum of all of them. The same operations are also available synchronously for simple or single-repo use.
- **Typer-based CLI** — `smartgit repo …`, `smartgit project …`, and `smartgit config …`, each with `--help`.

## Requirements

- Python >= 3.13
- Git installed and available on `PATH`

## Installation

```bash
pip install smartgit
```

Or, for local development from a clone of this repository:

```bash
uv sync        # or: pip install -e .
```

This installs the `smartgit` console script (see `[project.scripts]` in `pyproject.toml`).

## Documentation

- [Configuration](docs/configuration.md) — config file resolution, layered properties, dotenv overrides.
- [CLI command reference](docs/cli-reference.md) — every `smartgit repo`/`project`/`config` command and option.
- [Logging](docs/logging.md) — log configuration, verbosity flags, environment variables.

## License

MIT — see [LICENSE](LICENSE).
