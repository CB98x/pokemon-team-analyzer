# Learnings — Building the Pokémon Team Analyzer

A reference document of every concept, command, and SWE principle I encountered building this project. Organized by topic so I can come back later when I forget something specific.

---

## 1. Development environment & dependency management

### Virtual environments

A **virtual environment (venv)** is a sandboxed Python install scoped to one project. Without it, every `pip install` dumps into the system Python and every project shares the same pile — guaranteed conflicts when Project A wants `requests 2.28` and Project B wants `requests 2.31`.

**venv is Python-specific.** The concept (per-project dependency isolation) is universal, but each language has its own tool:
- Python: `venv`, `virtualenv`, `conda`, `poetry`, `uv`
- Node.js: `node_modules` per project (automatic)
- Ruby: `rbenv`, `bundler`
- Rust: handled by `cargo` automatically

**venv vs pip — different tools that work together.** `pip` is a package manager (installs packages from PyPI). `venv` is an isolation tool (creates a folder with a private Python that pip installs into). When venv is active, `pip` and `python` are redirected to the venv's copies. When inactive, they point to system Python.

**The setup workflow:**
```bash
python3 -m venv venv              # create the venv folder
source venv/Scripts/activate      # Git Bash on Windows
# (or `venv\Scripts\Activate.ps1` on PowerShell)
# (or `source venv/bin/activate` on Mac/Linux)
pip install requests pytest
pip freeze > requirements.txt     # snapshot installed packages
```

**Decoding `python3 -m venv venv`**: `-m` runs a module as a script. The first `venv` is the module name; the second `venv` is the folder name to create.

**Decoding `source venv/Scripts/activate`**: `source` runs a script in the *current* shell so it can modify environment variables. Without `source`, the script would run in a sub-shell and its changes would vanish.

**The signal venv is active**: `(venv)` appears at the start of your prompt.

**Critical habit**: venv activation is **per-terminal-session**. Every new terminal you open, your first command is `source venv/Scripts/activate`. Build the muscle memory.

**Why `pip freeze > requirements.txt` after activation matters**: with venv active, `pip freeze` lists only this project's packages. Without venv active, it lists every package on your whole system — useless for reproducibility.

### Windows vs Unix paths

`venv/Scripts/activate` on Windows; `venv/bin/activate` on Mac/Linux. Historical Windows convention vs Unix convention. Matters because tutorials are split across both — copying the wrong one gets "file not found." Now I know to check which OS the tutorial assumed.

### Reproducibility

Anyone (including future-me on a new laptop) should be able to clone the repo, run `pip install -r requirements.txt`, and get the exact same setup. That's the *whole point* of `requirements.txt`. A bloated requirements file with random system packages breaks the promise.

### Package managers

Each OS has one. Use it to install CLI tools cleanly instead of downloading random .exe files:
- **winget** (Windows): `winget install jqlang.jq`
- **apt** (Debian/Ubuntu): `apt install jq`
- **brew** (Mac): `brew install jq`

Package managers live at the OS layer — they work from any shell on that OS. Package IDs use `publisher.package-name` format (`jqlang.jq`, `GitHub.cli`) — explicit IDs guarantee reproducibility in scripts and READMEs.

**Use `winget search <name>`** to find package IDs without guessing.

---

## 2. The terminal, shell, and CLI

### Terminal vs Shell vs CLI tool

Often used interchangeably but technically distinct:

- **Terminal** = the window/program showing text and taking typed input (Git Bash window, VS Code's integrated terminal, Windows Terminal)
- **Shell** = the program *inside* the terminal that interprets your commands (bash, zsh, PowerShell, cmd)
- **CLI tool** = any program you invoke by typing its name (`git`, `python`, `pip`, `code`)

Three layers. You type CLI tools into a shell running inside a terminal.

**`code` is a launcher, not "VS Code's CLI"** — it's a tiny program that opens the regular GUI VS Code from the terminal. Many GUI apps ship CLI launchers (`code`, `cursor`, `subl`, `chrome`).

### Why Git Bash on Windows

Production servers run Linux. The commands you'll run on them — `ls`, `grep`, `cat`, `chmod`, `ssh`, `curl`, pipes, redirects — are bash/Linux conventions. Git Bash gives you those on Windows. PowerShell has different command names (`Get-ChildItem` instead of `ls`). The Linux-flavored shell transfers everywhere — Mac, Linux servers, Docker, CI/CD, AWS.

### Essential commands

| Command | What it does |
|---|---|
| `pwd` | Print working directory (where am I?) |
| `cd <path>` | Change directory |
| `ls` | List files; `ls -a` includes hidden dotfiles |
| `mkdir <name>` | Create folder |
| `touch <file>` | Create empty file; accepts multiple names |
| `mv <old> <new>` | Move or rename |
| `cat <file>` | Print file contents |
| `explorer .` | Open File Explorer in current dir (Windows) |
| `~` | Shorthand for home directory (`C:\Users\<you>` on Windows) |

### The PATH variable

**PATH** is a single string of folders separated by `:` (Unix/Git Bash) or `;` (Windows native). When you type a command, the shell searches each folder in order; **first match wins**.

This is how venv "shadows" system Python: activation prepends the venv's folder to PATH so its `python` is found before the system's.

**PATH is the #1 cause** of "command not found," "wrong version of X," and "works here but not there" bugs. Knowing how to inspect it is foundational debugging:

```bash
echo $PATH                  # the whole string (ugly)
echo $PATH | tr ':' '\n'    # one folder per line (readable)
where jq    # Windows: where does this command resolve from?
which jq    # Mac/Linux: same
```

### Environment variables are read at process start

When a shell starts, it reads PATH once. If you install a new tool, the existing terminal can't see it — restart the terminal (or sometimes the whole editor) to pick up the change. "Just restart it" solves a lot of mystery behavior.

### Silent success convention

Unix tools that have nothing meaningful to report say nothing — they just return a clean prompt. No "OK!" or "done!" Loud commands are the exception. (Caveat: silence can also mean "no results found" — like `where jq` printing nothing when jq isn't on PATH.)

### Pipes & the Unix philosophy

The pipe `|` sends the output of one command as input to the next. Foundation of Unix composition:

```bash
cat log.txt | grep ERROR | sort | uniq -c | sort -rn | head -10
```

Small tools doing one thing well, glued together with pipes. **The Unix philosophy**: composability beats monolithic do-it-all tools.

The redirect operator `>` catches a stream and writes it to a file: `command > file`. Bridge between stream-based tools and file-based tools.

### Yak-shaving — recognize the rabbit hole

Going to do task A requires installing tool B, which requires fixing PATH issue C, which requires restarting D. Senior engineers recognize this and bail. Time-box sidequests. If something installs in 30 seconds, great; if it's eaten 15 minutes, ask whether it's actually on the critical path.

---

## 3. VS Code workflow

- **`Ctrl+\`** toggles the integrated terminal — most-used shortcut.
- **VS Code can hold one workspace folder + arbitrary external files** as tabs simultaneously.
- **Split editor** (`Ctrl+\`) — view two files side-by-side. Essential for following docs while coding.
- **The dot on a tab** = unsaved changes.
- **Restricted mode** — safety feature for unfamiliar folders; trust folders you created yourself.
- **VS Code's status bar (bottom-left)** shows the current branch with a `*` if uncommitted changes exist.
- **`code <file-or-folder>`** in terminal opens VS Code at that location.

### File creation: terminal-first beats GUI

For five files, one command beats five right-clicks:
```bash
touch analyzer.py main.py test_analyzer.py .gitignore README.md
```

Beyond speed: terminal commands are *scriptable, shareable, paste-able into a README, and work on remote servers where there's no GUI*. **GUIs are for exploring; terminals are for doing.**

---

## 4. APIs, HTTP, and JSON exploration

### curl — talking to APIs from the terminal

`curl` = "client for URL." Sends HTTP requests, prints responses. Universal "talk to anything over HTTP" tool. Common uses:
- API exploration (`curl https://api.com/endpoint`)
- Downloading files (`curl -O https://example.com/file.zip`)
- Testing server availability
- Scripting any HTTP interaction

**`curl -s`** suppresses progress output. Critical when piping curl into other commands.

### JSON exploration recipe

For an unfamiliar JSON file, don't dump and scroll — ask small targeted questions:

```bash
jq 'keys' file.json                    # top-level keys
jq 'map_values(type)' file.json        # what type is each field?
jq '.field | length' file.json         # how big is something?
jq '.field[0]' file.json               # show me ONE example
jq '.field[].subfield' file.json       # drill into specifics
```

**jq path syntax**: `.field` for dict key, `[]` to iterate a list, dot-chained. `.stats[].stat.name` ≈ Python's `data["stats"][i]["stat"]["name"]`.

**jq has an internal pipe `|`** — chains filters inside one invocation (different from the shell pipe outside the quotes).

### JSON → Python access translation

This is one of the most-used skills in API work. Translate by walking outside-in:

- See `{ }` → it's a dict → use `["key"]`
- See `[ ]` → it's a list → use `[index]` (or loop)

```python
# JSON:
# { "drivers": [{"name": "George", "number": 63}, ...] }
data["drivers"][1]["number"]    # → 12 for the second driver
```

`t` in `for t in data["types"]` IS each item in the list. Not a separate thing.

### Senior move with big data

Build a mental model with small questions before writing code. Beats scrolling forever. Always know your data shape (write down the path: `data["stats"][0]["stat"]["name"]`) before consuming it.

---

## 5. Python language patterns

### Dict operations

```python
d["key"]                    # fetch; raises KeyError if missing
d.get("key")                # fetch; returns None if missing
d.get("key", 0)             # fetch with fallback
d.items()                   # iterate (key, value) pairs
{k: f(v) for k, v in d.items()}    # dict comprehension
for k in d:                 # iterating a dict gives its keys
```

Default value in `.get()` should match what comes next: `0` for sums, `[]` for extending, `""` for concatenating, `False` for boolean checks.

### List operations

```python
lst.append(x)               # add one item
lst.extend(other_list)      # add each item of another list (flattens)
[f(x) for x in lst]         # list comprehension
sorted(lst)                 # returns a new sorted list
```

**Lists are 0-indexed.** First item is `[0]`.

### Sets

Unordered, deduplicated:
```python
s = set()
s.add(x)              # silently ignores duplicates
set(list)             # dedupe a list
sorted(my_set)        # turn back into a sorted list
```

### Strings

**`"".join(list)` is faster than `+=`** because strings are immutable — `+=` creates a new string each time. For N items, `+=` is N copies; `.join()` is one allocation. Habit: accumulate fragments in a list, join at the end.

**f-string formatting:**
```python
f"{x:>10}"        # right-align, width 10
f"{x:<10}"        # left-align
f"{x:^10}"        # center
f"{x:.2f}"        # 2 decimal places
```

Used for column alignment in CLI output.

### The `sys` module

For talking to the Python interpreter and OS, not for APIs:

| | Purpose |
|---|---|
| `sys.argv` | Command-line args; `argv[0]` is script name, `argv[1:]` is user input |
| `sys.exit(code)` | Quit with status code |
| `sys.stdin / stdout / stderr` | Standard streams; used for piping |
| `sys.path` | Folders Python searches for `import` |
| `sys.platform` | OS detection: `"win32"`, `"linux"`, `"darwin"` |

### The `time` module

For low-level time (seconds, sleeping, timestamps). For dates/calendars, use `datetime` instead.

```python
start = time.time()                # seconds since epoch
elapsed_ms = (time.time() - start) * 1000

time.sleep(2)                      # blocking pause
time.perf_counter()                # higher precision for benchmarking
```

### Aggregation pattern

You'll write this loop a thousand times:
1. Initialize accumulators (dicts/lists/sets/counters)
2. Loop through input
3. Update each accumulator per item
4. After the loop, compute final values

Different data types capture different invariants: list keeps duplicates, set deduplicates, dict provides keyed lookup.

---

## 6. Error handling

### Tight try/except

Wrap **only the line(s) that can throw the exception you're catching**. Don't wrap whole functions — that hides bugs. The pattern:

```python
try:
    response = requests.get(url, timeout=5)   # only this line
except requests.RequestException as e:
    logger.error("Network error: %s", e)
    raise

if response.status_code == 404:       # checks AFTER the try
    raise ValueError(...)
```

### HTTP failure ≠ Python exception

A 404 is a *successful* HTTP request that returned "not found." Check status codes with `if`; catch network failures with `try/except`. They're different categories.

### `raise` vs `return` for failures

Use **raise** for "this function didn't do its job" — exceptions propagate automatically; failure is loud.
Use **return** for "this function did its job, here's the result."

If you return success/failure as data, every caller has to remember to check it. Forget one, and bugs sneak through silently.

### Common Python exception types

| Exception | When |
|---|---|
| `ValueError` | Right type, wrong value (`int("abc")`) |
| `TypeError` | Wrong type entirely (`"a" + 5`) |
| `KeyError` | Dict key doesn't exist |
| `IndexError` | List index out of range |
| `AttributeError` | Object lacks that method/property |
| `FileNotFoundError` | File doesn't exist |
| `ZeroDivisionError` | Divided by zero |
| `RuntimeError` | Generic "something went wrong" |

Plus library-specific: `requests.RequestException`, `json.JSONDecodeError`.

### Exit codes

Unix programs return a number to the OS on exit:
- `0` = success
- `1` = generic failure (often "user error")
- `2` = often "system error" (network, etc.)

The shell uses these for chaining: `cmd1 && cmd2` only runs `cmd2` if `cmd1` returned 0. Same logic powers CI/CD pipelines.

---

## 7. Logging & observability

### What `logger` is

An **object** — instance of Python's `Logger` class. Not a dict or table. Created per file:

```python
import logging
logger = logging.getLogger(__name__)
```

`__name__` gives each file its own logger, lettable on/off independently.

### Levels (least to most severe)

| Level | When to use |
|---|---|
| DEBUG | Diagnostic info; variable values; off in production |
| INFO | Normal operations |
| WARNING | Unexpected but recoverable |
| ERROR | Something failed |
| CRITICAL | Program can't continue |

Set a threshold; everything at or above prints. In dev, DEBUG. In prod, INFO or WARNING.

### Why not just `print`?

Logging has levels, timestamps, module names, configurable destinations (file, network, monitoring services), and goes to stderr (separable from program output). Industry standard. `print` is for one-off scripts.

### Standard pattern

**In libraries** — get a logger, just use it. Don't configure.
```python
logger = logging.getLogger(__name__)
logger.info("Doing the thing")
```

**In the application entry point** — configure once.
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

### Use `%s` not f-strings in log messages

```python
logger.info("Fetching %s", name)        # ✓ formatted only if message emits
logger.info(f"Fetching {name}")         # ✗ formats unconditionally
```

For tiny strings it doesn't matter. For DEBUG logs in hot loops, the difference is real.

### Logs vs stdout

- **Logs** explain what the program is doing (for operators/debugging).
- **stdout** is the program's actual product (the data the user asked for).

Don't mix them. A CLI report goes to stdout via `print`. Logs go to stderr via the logger.

### Metrics: what to count

A simple in-memory metrics dict can track:
- `api_calls_total` — how many requests sent
- `api_calls_failed` — how many failed
- `api_latency_ms_total` — cumulative latency for averaging
- `teams_analyzed` — units of work completed

Logs tell the story of one request; metrics tell the aggregate. Both matter. Real systems export metrics to CloudWatch / Datadog / Prometheus.

---

## 8. Testing with pytest

### Why tests exist

**Executable specifications**. Run them every time you change code — green means you didn't break anything. Without tests, every change is scary. With tests, refactoring is safe.

### pytest auto-discovery

By naming convention:
- Files matching `test_*.py` (or `*_test.py`)
- Functions matching `test_*` inside them

No registration boilerplate. Name it right, pytest finds it.

### Arrange / Act / Assert

Every test:
1. **Arrange** — build inputs
2. **Act** — call the function
3. **Assert** — check the output

### `assert` is built-in Python

```python
assert x == y            # equal
assert x in collection   # membership
assert "fire" in result["types"]
```

pytest catches `AssertionError` and reports the failure. No `assertEquals` or `assertIn` needed.

### `pytest.raises` for testing exceptions

```python
with pytest.raises(ValueError, match="3–6 Pokémon"):
    analyze_team(too_small_team)
```

Confirms the right exception fires with the right message.

### Mocking — replace external dependencies

```python
@patch("analyzer.requests.get")
def test_fetch_pokemon_success(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": "pikachu", ...}
    mock_get.return_value = mock_response

    result = fetch_pokemon("pikachu")
    assert result["name"] == "pikachu"
```

`@patch("module.thing")` replaces `module.thing` with a Mock during the test. `Mock()` is a generic fake object. `mock.method.return_value = X` configures what a method returns when called.

### Unit tests vs integration tests

| | Unit | Integration |
|---|---|---|
| Tests | One function in isolation | Whole system end-to-end |
| Hits real services? | NO — mocks them | YES — hits real APIs |
| Run frequency | Every code change | Nightly, pre-release |

Unit tests should fail only when **your code** is wrong, never when external services are slow or down. Real projects have both kinds, separated.

---

## 9. Git fundamentals

### Three states of change

```
Working directory  →  Staging  →  Commit history  →  Remote (GitHub)
   (your files)      (git add)    (git commit)       (git push)
```

Staging exists so commits can be *logical units* — pick which changes go together. Fixed a bug AND added a feature? Two separate commits.

### Daily commands

```bash
git status                          # ALWAYS run; source of truth
git add .                           # stage everything
git commit -m "Descriptive message"
git push                            # send to remote
git log --oneline -5                # last 5 commits
git remote -v                       # what remotes am I connected to?
```

### Setup vs recurring

- **Setup** (run once per project): `git init`, `git remote add origin`, `git push -u`
- **Recurring** (run constantly): `git status`, `add`, `commit`, `push`, `pull`

If you find yourself running setup commands repeatedly, something's off.

### `origin` and `main` vs `origin/main`

- **`origin`** = nickname your local git uses for the remote's URL
- **`main`** = YOUR LOCAL main branch
- **`origin/main`** = the remote's main branch (specifically, your local's cached copy of it from the last `fetch`)

Both sides have branches named `main`. They mirror each other but can drift.

### Fetch vs pull vs merge

- **`git fetch`** = download remote changes, don't apply them
- **`git merge`** = apply changes to current branch
- **`git pull`** = fetch + merge in one step

`git fetch <remote> <branch>` — remote name first, branch second. (`git fetch origin main`.)

### `.gitignore` before first commit

`.gitignore` filters at staging time, so write it BEFORE `git add .`. Otherwise you commit `venv/` (hundreds of MB) and have to clean up.

### Commit messages matter

Future-you (and teammates) read them to understand history. "Stuff" tells you nothing. "Fix divide-by-zero in analyze_team for empty teams" tells you everything. Worth the 5 extra seconds.

---

## 10. Branches & pull requests

### Why feature branches

`main` should always be working/deployable. Build new things on feature branches. Merge to main only when done. If a feature turns out bad, delete the branch — `main` is untouched.

### Branch workflow

```bash
git checkout main
git pull                                  # sync with remote first
git checkout -b feature/<descriptive-name>
# (edit, save)
git add .
git commit -m "..."
git push -u origin feature/<name>         # -u sets tracking on first push
```

After first `-u` push, plain `git push` works on this branch.

### Branch naming conventions

`feature/...`, `bugfix/...`, `hotfix/...`, `chore/...`. The slash isn't a folder; it's just a naming pattern GitHub groups visually. Names describe the *change*, not the file.

### `gh` — GitHub CLI

Install once: `winget install GitHub.cli`. Authenticate: `gh auth login` (also covers `git` auth).

```bash
gh pr create --fill              # auto-fills from latest commit message
gh pr list                       # all open PRs
gh pr view <N>                   # read PR details
gh pr diff <N>                   # see the diff
gh pr checkout <N>               # switch local to a PR's branch
gh pr review <N> --approve
gh pr merge --squash --delete-branch    # merge + clean up
```

### PR vs commit identifiers

- **Commits** get **hashes** (`4bef5b7`) — for machines
- **PRs/issues** get **numbers** (`#42`) — for humans
- **Branches** get **names** — for humans
- **Tags/releases** get **versions** — for humans

`#42` in a commit message or PR description auto-links on GitHub. `Closes #42` in a PR description auto-closes issue 42 when merged.

### Squash merging

Collapses all the messy commits on a feature branch into one tidy commit on main. Keeps main history clean — one commit per feature instead of N work-in-progress commits.

---

## 11. Reading CLI output & resolving conflicts

### Structure of CLI errors

1. **Status marker** (`X`, `error:`, `fatal:`) → something is wrong
2. **Line after** → what
3. **Below** → suggested fix (often literal commands)
4. **Everything else** → context; skim

`fatal:` in git = total failure; nothing happened. Usually a typo or setup issue.

### Reading `git push` output

The last meaningful line is the result. `4bef5b7..3e3587a  main -> main` = "remote's main moved from this commit to that one." `..` means a range of commits.

### Merge conflicts

Conflict = both branches changed the same lines of the same file; git can't auto-pick.

**Conflict markers** in the file:
```
<<<<<<< HEAD
my current branch's version
=======
the incoming version
>>>>>>> origin/main
```

Edit to keep what you want, delete all three markers, save.

VS Code shows clickable buttons above each conflict: **Accept Current / Accept Incoming / Accept Both**. Faster than hand-editing.

### Resolution flow

```bash
git add <resolved-files>
git status                       # confirms "all conflicts fixed"
git commit                       # no -m needed; git auto-writes merge message
git push
```

### `|MERGING` in the prompt

Git is mid-merge with unresolved conflicts. Don't switch branches or do other work until resolved. Press Enter in the terminal to refresh the prompt display if it looks stale — prompts render once per command, not live.

### `git status` is the source of truth

UI buttons and prompt text can lag. `git status` always tells you the actual state from git's brain. When confused, run it.

### #1 cause of merge conflicts for solo devs

Editing the same file in two places (e.g., locally + on GitHub web editor) without syncing. **Habit: `git pull` before starting any work session.** Cheap if nothing to pull; saves you when there is.

---

## 12. Cross-cutting SWE principles

### Phased code construction

Real engineers don't write the final form first. The phases:

1. **Happy path** — make it work for the normal case
2. **Error handling** — what can go wrong? Handle each
3. **Logging** — add observability
4. **Metrics** — add aggregate visibility
5. **Polish** — docstrings, type hints, constants, comments

Each phase makes the previous one better, not redo-from-scratch. Adding metrics before the function works is a junior trap.

### How to read existing code

Top-to-bottom is the worst way. Code in a file is *layered*, not *sequential*. To understand a function:

1. Read the docstring/comments first
2. Find the return statement — what does it produce?
3. Find the inputs
4. Skim the happy path, ignoring try/except, logs, metrics
5. Now layer in error handling
6. Last, logs and metrics — these are for operators

### Convention over configuration

`requirements.txt`, `README.md`, `.gitignore`, `origin`, `main` — standard names let tools find them automatically and other devs instantly know what they are. Deviating costs compatibility for no benefit.

### Single responsibility

Each variable, function, file tracks one thing. `stat_totals` accumulates numbers; `all_types` collects types (list, allows duplicates); `weaknesses` collects uniques (set, auto-dedupes). Different data types capture different invariants. Independently inspectable, independently debuggable.

### Defensive coding

`.get(key, default)` instead of `[key]` when missing keys are possible. Tight try/except around the exact line that can fail. Validate input at function boundaries (fail fast, fail loud).

### Documentation for future-you

Commit messages, PR descriptions, READMEs, comments-with-why-not-what — all of these are letters to future-you and your teammates. Write them as if you'll be debugging this code at 3am in two years. (You might be.)

### The "result envelope" pattern

A function that does aggregation returns one dict with all its computed values:
```python
return {
    "team_size": len(team),
    "names": [...],
    "average_stats": averages,
    "types": sorted(set(all_types)),
    "weak_against": sorted(weaknesses),
}
```

Caller uses it as a unit. Common at the end of analysis functions.

### Naming for portfolios

- `<thing>-<noun>` for tools (`pokemon-team-analyzer`)
- `<noun>-api` for backend services
- `<framework>-<thing>` when framework is the point

Avoid initials, version numbers in names, buzzwords without substance.

### GitHub discoverability ≠ repo name

It's driven by **topics, About description, README content, pinned-on-profile status**. Repo name just makes the link readable.

### Yak-shaving discipline

If a sidequest has eaten more than ~15 minutes and isn't on the critical path, bail and come back later. Senior engineers recognize the rabbit hole; juniors disappear into it for an afternoon.

### Logs vs metrics — operator vs aggregate

Logs tell the story of one request (debugging). Metrics tell the aggregate (dashboarding). Both matter. Different audiences, different tools.

### Test categorization

Unit (mocked, fast, every commit) vs integration (real services, slow, run rarely). Never mixed. Tests should fail only when your code is wrong.

### Always run `git pull` before starting work

Especially after a break, after a weekend, after switching machines, after editing on GitHub directly. The cheapest habit that prevents merge conflicts.

---

## What I'd do differently next time

- Set up `.gitignore` immediately after `git init`, before the first `git add .`.
- Branch from the start. Never commit directly to `main`, even on day one.
- Run `git pull` before starting every work session, especially before creating a new feature branch.
- Don't edit on GitHub web AND locally without syncing in between.
- Pick a meaningful repo name from the start, not a default with random suffixes.
- Read CLI errors top-to-bottom carefully before searching online — the answer is often in the message itself.

---

## What this project did NOT cover (next things to learn)

- Building a long-running web service (FastAPI / Flask) instead of a one-shot CLI
- Talking to a database (SQLite, Postgres, DynamoDB)
- Deploying to a real server (Render, Fly.io, AWS Lambda)
- Containerization (Docker)
- CI/CD pipelines (GitHub Actions)
- Async Python (`asyncio`)
- System design fundamentals
- Reading and contributing to an unfamiliar codebase
