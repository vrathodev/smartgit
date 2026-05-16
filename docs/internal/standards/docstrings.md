# SmartGit — Docstring & Comment Conventions

Derived from actual code in `smartgit.core._SmartRepo.py`.
All examples are real or minimally adapted from that file.

---

## 1. File Header

Every `.py` source file starts with a fixed-width 120-character banner.
See [`copyright.md`](copyright.md) for the full specification and template.

---

## 2. Module Level

No module-level docstring. The file banner serves that role.

The module body starts immediately after the banner with:
1. Standard library imports
2. Third-party imports
3. Internal project imports
4. A blank line
5. Module-level constants (e.g. logger)

```python
# Logger instance
LOGGER = getSmartLogger()
```

Module-level constants get a single `# ` comment above them if their purpose is not obvious.

---

## 3. Class Docstring

Single-line summary only. Use an em-dash (`--`) to separate the class name from its role description.
No blank line between the opening `"""` and the text.

```python
class SmartRepo(Repo):
    """
    SmartRepo -- Async + sync Git operations capable SmartGit primitive
    """
```

Do not include attribute lists, examples, or notes in the class docstring.
Those belong in `__init__` or method docstrings.

### Dataclass

Same pattern — one-line summary describing what the dataclass represents.

```python
@dataclass(frozen=True)
class GitCMD:
    """
    Represents a Git command with its arguments.
    """
```

---

## 4. `__init__` Docstring

Describes what the constructor does, not what the class is.
Parameters use the same `:param name:` style as all other methods.

```python
def __init__(self, inRepoConfig: Optional[RepoConfig], **kwargs):
    """
    Initializes the SmartRepo with the RepoConfig

    :param inRepoConfig:    [Optional] Repository configuration to initialize the SmartRepo with.
    """
```

---

## 5. Method Docstring — Structure

```
"""
<One-line summary sentence.>
[blank line if params/returns/raises follow]
:param paramName:    <description>
:param paramName:    <[Optional] description.> Defaults to <value>
:returns: <description>
:raises ExceptionType: <when this is raised>
"""
```

### Rules

| Rule | Detail |
|------|--------|
| Summary | Imperative mood, no trailing period, capitalised |
| Blank line | Required between summary and `:param` block |
| No blank line | When there are no params (property-style one-liners) |
| Alignment | Parameter descriptions aligned to a common column (see §5.1) |
| Optional params | Prefixed `[Optional]`, suffix `Defaults to <value>` |
| Required params | No prefix |

### 5.1 Parameter column alignment

All `:param` descriptions in a method are aligned to the same column.
The column is determined by the longest parameter name + its leading whitespace.

```python
def _create_branch(
    self,
    inBranchName: str,
    inStartPoint: str,
    inPushRemote: bool = False,
    inRemoteName: str = SG_VAL_REMOTE_NAME_DEFAULT
):
    """
    Creates a new branch from the specified start point (commit hash or branch name or tag)

    :param inBranchName:    Name of the new branch to create
    :param inStartPoint:    to start the new branch from
    :param inPushRemote:    Whether to push the new branch to remote (optional) Defaults to False
    :param inRemoteName:    Name of the remote to push to (optional) Defaults to 'origin'
    """
```

### 5.2 Multi-line parameter description

When a description wraps, align the continuation to the description column (not `:param`).

```python
:param inBranch:            Branch to check out (optional)
                            Defaults to remote and local HEAD, for new and existing repositories respectively
```

### 5.3 `:returns:` and `:raises:`

```python
:returns: The initialized SmartRepo instance
:raises Exception: If clone operation fails
```

---

## 6. Property Docstring

Simple properties (return a stored field, obvious from the name) carry **no docstring**.

```python
@property
def config(self) -> RepoConfig:
    return self.__mRepoConfig

@property
def name(self) -> str:
    return os.path.basename(self.path)
```

Properties with non-trivial logic or a non-obvious return shape get a docstring.

```python
@cached_property
def remote_branches(self) -> FrozenSet[str]:
    """
    Returns a frozen set of remote branch names in the repository
    """
```

No `:param` or `:returns:` tags — the type annotation on the property is sufficient.

---

## 7. Private Methods (`_method` prefix)

Same docstring format as public methods. No special treatment.
Private methods implement the core logic; public methods are thin wrappers that call them.

```python
def _fetch(self, inRemote: Optional[str] = None, inSkipTags: bool = False):
    """
    Fetches from the remote(s)
    :param inRemote: [Optional] Name of the remote, default fetches from all remotes
    :param inSkipTags: [Optional] Should skip fetching the tags
    """
```

Note: when there are only optional parameters with short descriptions, the blank line between
summary and `:param` block may be omitted.

---

## 8. Async Counterparts

Async method docstrings are identical to their sync counterpart, with `(async)` appended
to the summary line only when needed for disambiguation.

```python
async def afetch(self, inRemote: Optional[str] = None, inSkipTags: bool = False):
    """
    Fetches from the remote(s) (async)
    :param inRemote: [Optional] Name of the remote, default fetches from all remotes
    :param inSkipTags: [Optional] Should skip fetching the tags
    """
```

Naming convention: async counterparts use `a` prefix (e.g. `afetch`, `apull`, `aprune`) or
`async_` prefix for longer names (e.g. `async_create_branch`, `async_delete_branch`).

---

## 9. Classmethod Docstring

Same body structure as instance methods. Always include `:returns:`.

```python
@classmethod
def from_config(cls, inRepoName: str) -> Self:
    """
    Initializes a SmartRepo from the configuration for the given repository name

    :param inRepoName: Name of the repository
    :returns: The initialized SmartRepo instance
    """
```

For `smart_init`-style classmethods with multiple numbered steps, use an indented numbered list
in the summary section:

```python
@classmethod
def smart_init(cls, inRepoName: str, inRepoConfig: RepoConfig, inBranch: str = None) -> Self:
    """
    Initializes a SmartRepo by
        1. Locating the repository at prop.GIT_ROOT/inRepoName if exists
        2. Cloning the repository from prop.GIT_REMOTE_BASE_URL/inRepoName
        3. Switching to the specified branch if provided
        4. Submodule Initialization if prop.GIT_SUBMODULE_INIT enabled

    :param inRepoName:          Name of the Repository
    :param inRepoConfig:        Configuration of the Repository
    :param inBranch:            Branch to check out (optional)
                                Defaults to remote and local HEAD, for new and existing repositories respectively
    :raises Exception: If clone operation fails
    """
```

---

## 10. Inline Comments

Use `# ` (hash + single space) style. Place the comment on its own line above the code it describes,
not at the end of the line.

```python
# Filter empty args (e.g., from conditional --prune flags)
object.__setattr__(self, 'args', tuple(a.strip() for a in args if not isNoneOrEmpty(a)))
```

End-of-line comments are only used for very short clarifications where a separate line would interrupt
the flow (rare).

---

## Summary Table

| Docstring target              | Format        | Blank line before params | `:returns:` | `:raises:`       |
|-------------------------------|---------------|--------------------------|-------------|------------      |
| Class / dataclass             | Single-line   | N/A                      | No          | No               |
| `__init__`                    | Multi-line    | Yes                      | No          | Optional         |
| Public method                 | Multi-line    | Yes                      | When useful | When applicable  |
| Private method (`_`)          | Multi-line    | Omit if short            | No          | Optional         |
| Async method (`a` / `async_`) | Same as sync  | Same as sync             | Same        | Same             |
| Classmethod                   | Multi-line    | Yes                      | Always      | When applicable  |
| Property (non-trivial)        | One-liner     | No                       | No          | No               |
| Property (simple accessor)    | None          | —                        | —           | —                |
