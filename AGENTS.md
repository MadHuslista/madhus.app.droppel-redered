# AGENTS.md — CLI Tool Architecture & Design Guide

> "Good taste" in code is the ability to recognize the difference between a solution that
> merely works and one that is *right*. It's seeing the simple pattern hiding inside
> complexity, and having the discipline to reach for it.
> — Inspired by Linus Torvalds

This document codifies architectural principles, design patterns, and evaluation criteria
for building command-line tools with **elegance**, **robustness**, and **operational
excellence**. Use it as a lens to evaluate tool designs before implementation.

---

## Toolchain Rules 

- To review a rule, use `bash` command to read the file: `cat .augment/rules/<rule_file>`
- To review a template, use `bash` command to read the file: `cat .augment/templates/<template_file>`
- To review a standard, use `bash` command to read the file: `cat .augment/standards/<standard_file>`
- For each rule:
  - Before executing a rule, identify its dependencies (other rules, templates, standards, placeholders).
  - Validate that all dependencies are available in the appropriate directories.
  - Create/Update the placeholders at `<repo_root>/.augment/config/placeholders.env` with the correct values if needed.
  - If a dependency is still missing, FAIL and report to user.

## Part I: Core Philosophy

### The Three Pillars of Tool Design

```
                    ┌─────────────────┐
                    │   CORRECTNESS   │
                    │  Does it work?  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐          ┌────────▼────────┐
     │   OPERABILITY   │          │  MAINTAINTIC    │
     │ Can humans run  │          │  ABILITY        │
     │ it safely?      │          │ Can humans      │
     └─────────────────┘          │ change it?      │
                                  └─────────────────┘
```

**Correctness without operability** → A tool that works but can't be safely deployed.
**Correctness without maintainability** → A tool that works until requirements change.
**All three together** → A tool with *good taste*.

### The Principle of Least Surprise

A well-designed tool should behave as an experienced operator would expect. This means:

- Flags follow conventions (`-v` for verbose, `-q` for quiet, `-n` for dry-run)
- Destructive operations require confirmation (unless `--yes`)
- Errors explain *what went wrong* and *what to do about it*
- Default behaviors are safe; dangerous behaviors require explicit opt-in

### The Principle of Compositional Honesty

Every tool is a function: `Input → Processing → Output + Side Effects`

Good design makes each component **explicit and inspectable**:
- Inputs are validated and normalized at the boundary
- Processing is deterministic and testable in isolation
- Outputs are structured and predictable
- Side effects are centralized and controllable (including disable-able)

---

## Part II: Architectural Patterns

### Pattern 1: Configuration as a First-Class Citizen

**The Anti-Pattern (Global Variables):**
```python
# ❌ POOR TASTE: Configuration scattered as globals
SHARD_CAP = 500
LOG_LEVEL = "info"
DRY_RUN = False

def process_files():
    if DRY_RUN:  # Hidden dependency on global state
        ...
```

**Why it's wrong:**
- Testing requires monkeypatching or module reloading
- No validation until runtime (and often not even then)
- Impossible to trace where a value came from
- Can't run two configurations in the same process

**The Pattern (Configuration Object):**
```python
# ✅ GOOD TASTE: Configuration is explicit, immutable, validated
from dataclasses import dataclass
from typing import Literal
from pathlib import Path

@dataclass(frozen=True)
class Config:
    """Immutable, validated configuration object."""
    src: Path
    target: Path
    extensions: frozenset[str]
    shard_cap: int = 500
    shard_prefix: str = "shard"
    sort_by: Literal["size", "name"] = "size"
    sort_dir: Literal["asc", "desc"] = "asc"
    dry_run: bool = False
    yes: bool = False
    log_level: Literal["debug", "info", "warn", "error"] = "info"

    def __post_init__(self):
        # Validation happens once, at construction time
        if self.shard_cap < 1:
            raise ConfigError("shard_cap must be positive")
        if self.src == self.target:
            raise ConfigError("src and target must differ")
        if self.target.is_relative_to(self.src):
            raise ConfigError("target cannot be inside src (infinite recursion)")
```

**The Layered Loading Pattern:**
```python
def load_config(cli_args: Namespace) -> Config:
    """
    Configuration precedence (highest wins):
    1. CLI arguments
    2. Environment variables
    3. Config file (~/.config/tool/config.toml)
    4. Built-in defaults
    """
    defaults = get_defaults()
    file_config = load_config_file()
    env_config = load_from_env()
    cli_config = vars(cli_args)
    
    merged = {**defaults, **file_config, **env_config, **cli_config}
    return Config(**merged)
```

---

### Pattern 2: The Functional Core, Imperative Shell

This is perhaps the most important architectural pattern for tool design.

```
┌─────────────────────────────────────────────────────────────┐
│                     IMPERATIVE SHELL                        │
│  (CLI parsing, file I/O, network, user interaction)         │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                 FUNCTIONAL CORE                     │   │
│   │   (Pure functions, deterministic, no side effects)  │   │
│   │                                                     │   │
│   │   Input Data ──► Transformations ──► Output Data    │   │
│   │                                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:**
```python
# ═══════════════════════════════════════════════════════════
# FUNCTIONAL CORE (planner.py) — Pure, testable, no I/O
# ═══════════════════════════════════════════════════════════

@dataclass(frozen=True)
class FileRecord:
    path: Path
    size: int
    extension: str

@dataclass(frozen=True)
class ShardAssignment:
    source: Path
    target: Path
    shard_index: int

def compute_shard_plan(
    files: Sequence[FileRecord],
    config: Config,
) -> list[ShardAssignment]:
    """
    Pure function: same inputs ALWAYS produce same outputs.
    No file I/O, no side effects, trivially testable.
    """
    sorted_files = sort_files(files, config.sort_by, config.sort_dir)
    
    assignments = []
    for idx, file in enumerate(sorted_files):
        shard_num = (idx // config.shard_cap) + 1
        shard_name = f"{config.shard_prefix}_{shard_num}"
        target = config.target / file.extension / shard_name / file.path.name
        assignments.append(ShardAssignment(file.path, target, shard_num))
    
    return assignments


# ═══════════════════════════════════════════════════════════
# IMPERATIVE SHELL (executor.py) — Side effects live here
# ═══════════════════════════════════════════════════════════

def execute_plan(
    plan: list[ShardAssignment],
    fs: FileSystemOps,  # Injected dependency!
) -> ExecutionResult:
    """
    All side effects go through the `fs` interface.
    Inject RealFS for production, MockFS for testing, DryRunFS for preview.
    """
    created_dirs: set[Path] = set()
    created_links: list[tuple[Path, Path]] = []
    
    for assignment in plan:
        if assignment.target.parent not in created_dirs:
            fs.mkdir(assignment.target.parent)
            created_dirs.add(assignment.target.parent)
        
        fs.symlink(assignment.source, assignment.target)
        created_links.append((assignment.source, assignment.target))
    
    return ExecutionResult(dirs=created_dirs, links=created_links)
```

**Why this matters:**
- The core logic (`compute_shard_plan`) can be tested with zero mocking
- The shell (`execute_plan`) is thin and obvious
- Dry-run is trivial: inject a different `fs` implementation
- Debugging is simple: inspect the plan before execution

---

### Pattern 3: Explicit Side Effect Interfaces

**The Anti-Pattern:**
```python
# ❌ POOR TASTE: Side effects scattered throughout
def process():
    files = os.listdir(src)           # Side effect: filesystem read
    print(f"Found {len(files)}")      # Side effect: console output
    os.makedirs(target, exist_ok=True) # Side effect: filesystem write
    log.info("Created directory")      # Side effect: logging
```

**The Pattern:**
```python
# ✅ GOOD TASTE: Side effects through explicit interfaces
from typing import Protocol

class FileSystem(Protocol):
    """Abstract interface for filesystem operations."""
    def scandir(self, path: Path) -> Iterator[DirEntry]: ...
    def mkdir(self, path: Path) -> None: ...
    def symlink(self, src: Path, dst: Path) -> None: ...
    def exists(self, path: Path) -> bool: ...
    def stat(self, path: Path) -> os.stat_result: ...

class RealFileSystem:
    """Production implementation — actually touches disk."""
    def mkdir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
    # ...

class DryRunFileSystem:
    """Preview implementation — logs intentions, touches nothing."""
    def __init__(self, logger: Logger):
        self.logger = logger
        self.would_create: list[Path] = []
    
    def mkdir(self, path: Path) -> None:
        self.logger.info(f"[DRY-RUN] Would create: {path}")
        self.would_create.append(path)
    # ...

class InMemoryFileSystem:
    """Testing implementation — fast, isolated, inspectable."""
    def __init__(self):
        self.files: dict[Path, bytes] = {}
        self.dirs: set[Path] = set()
    # ...
```

---

### Pattern 4: The Validation → Plan → Execute Pipeline

Never interleave validation with execution. Separate them completely.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   VALIDATE   │────►│     PLAN     │────►│   EXECUTE    │
│              │     │              │     │              │
│ Can we run?  │     │ What will    │     │ Do it (or    │
│ Check ALL    │     │ we do?       │     │ pretend)     │
│ preconditions│     │ Compute ALL  │     │              │
│              │     │ operations   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │ FAIL FAST          │ INSPECTABLE        │ ATOMIC
       │ if invalid         │ (--dry-run)        │ or rollback
       ▼                    ▼                    ▼
   Exit with            Print plan          Commit or
   clear error          if requested        abort entirely
```

```python
def main(config: Config) -> int:
    # Phase 1: Validate everything before touching anything
    issues = validate(config)
    if issues:
        for issue in issues:
            log.error(issue)
        return 1
    
    # Phase 2: Compute the complete plan
    files = scan_directory(config.src, config.extensions)
    plan = compute_shard_plan(files, config)
    
    # Phase 3: Preview if requested
    if config.dry_run:
        print_plan(plan)
        return 0
    
    # Phase 4: Confirm if interactive
    if not config.yes:
        if not confirm(f"Create {len(plan)} symlinks?"):
            return 1
    
    # Phase 5: Execute atomically
    result = execute_with_rollback(plan, config)
    
    # Phase 6: Write audit log
    write_execution_log(result, config)
    
    return 0
```

---

### Pattern 5: Structured Error Handling

**The Anti-Pattern:**
```python
# ❌ POOR TASTE: Generic exceptions, no context
try:
    process_files()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
```

**The Pattern:**
```python
# ✅ GOOD TASTE: Typed exceptions with context and remediation
class ToolError(Exception):
    """Base class for all tool errors."""
    exit_code: int = 1
    
    def user_message(self) -> str:
        """Human-readable error message."""
        return str(self)
    
    def remediation(self) -> str | None:
        """Suggested fix, if known."""
        return None

class ConfigError(ToolError):
    """User provided invalid configuration."""
    exit_code = 2
    
class ValidationError(ToolError):
    """Pre-flight validation failed."""
    exit_code = 3
    
    def __init__(self, check: str, details: str, fix: str | None = None):
        self.check = check
        self.details = details
        self.fix = fix
        super().__init__(f"{check}: {details}")
    
    def remediation(self) -> str | None:
        return self.fix

class StateConflictError(ValidationError):
    """Target exists with incompatible state."""
    exit_code = 4
    
    def __init__(self, target: Path, expected: str, actual: str):
        super().__init__(
            check="State conflict",
            details=f"{target} has {actual}, expected {expected}",
            fix=f"Remove {target} or use --force to overwrite"
        )

# Usage in main:
def main() -> int:
    try:
        return run(parse_args())
    except ToolError as e:
        log.error(e.user_message())
        if remedy := e.remediation():
            log.info(f"Suggestion: {remedy}")
        return e.exit_code
    except KeyboardInterrupt:
        log.warn("Interrupted by user")
        return 130  # Standard Unix convention
```

---

## Part III: CLI Design Principles

### Required Flags for Filesystem-Mutating Tools

| Flag | Short | Purpose | Notes |
|------|-------|---------|-------|
| `--dry-run` | `-n` | Preview without executing | **NON-NEGOTIABLE** |
| `--yes` | `-y` | Skip confirmation prompts | Enables automation |
| `--verbose` | `-v` | Increase output detail | Stackable: `-vvv` |
| `--quiet` | `-q` | Suppress non-error output | For scripting |
| `--force` | `-f` | Override safety checks | Use sparingly |
| `--help` | `-h` | Show usage | Auto-generated |
| `--version` | `-V` | Show version | Include git hash |

### Input Normalization at the Boundary

All input normalization happens **once**, at the CLI boundary:

```python
def normalize_extensions(raw: list[str]) -> frozenset[str]:
    """
    Normalize extension input to canonical form.
    
    Accepts:
      - ".mp4" or "mp4" (with/without dot)
      - "mp4,jpg,png" (comma-separated)
      - "mp4 jpg png" (space-separated)
      - ["mp4", "jpg"] (already split)
    
    Returns:
      frozenset of lowercase extensions without dots: {"mp4", "jpg", "png"}
    """
    extensions = set()
    for item in raw:
        for ext in re.split(r'[,\s]+', item.strip()):
            normalized = ext.strip().lstrip('.').lower()
            if normalized:
                extensions.add(normalized)
    return frozenset(extensions)


def normalize_path(raw: str, relative_to: Path | None = None) -> Path:
    """
    Normalize path input to absolute canonical form.
    
    Handles:
      - Absolute paths: /usr/local → unchanged
      - Home expansion: ~/docs → /home/user/docs
      - Relative paths: ./data → resolved against relative_to or cwd
    
    Returns:
      Absolute, resolved Path with symlinks resolved.
    """
    path = Path(raw).expanduser()
    
    if not path.is_absolute():
        base = relative_to or Path.cwd()
        path = base / path
    
    return path.resolve()
```

### Help Text That Actually Helps

```python
HELP_EPILOG = """
Examples:
  # Basic usage: shard all .mp4 files
  %(prog)s --src ~/Videos --target ~/Organized --ext mp4

  # Multiple extensions, sorted by name descending
  %(prog)s --src ./data --target ./out --ext mp4,mkv,avi --sort name --sort-dir desc

  # Process by file type (all video formats)
  %(prog)s --src ./media --target ./out --type video

  # Preview without making changes
  %(prog)s --src ./data --target ./out --ext mp4 --dry-run

  # Non-interactive (for scripts/CI)
  %(prog)s --src ./data --target ./out --ext mp4 --yes

Configuration:
  Default values can be overridden via:
    1. ~/.config/file-sharder/config.toml
    2. Environment variables (FILE_SHARDER_SHARD_CAP, etc.)
    3. Command-line flags (highest priority)

Exit Codes:
  0  Success
  1  General error
  2  Configuration error
  3  Validation failed
  4  State conflict (target exists with different config)
  130  Interrupted (Ctrl+C)
"""
```

---

## Part IV: Testing Patterns

### The Testing Pyramid for Tools

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲        Few: Slow, brittle, but realistic
                 ╱──────╲
                ╱        ╲
               ╱Integration╲    Some: Test component interactions
              ╱────────────╲
             ╱              ╲
            ╱     Unit       ╲  Many: Fast, isolated, exhaustive
           ╱──────────────────╲
```

### Unit Testing the Functional Core

```python
# tests/test_planner.py — Tests pure logic, no mocking needed

def test_shard_assignment_respects_cap():
    files = [FileRecord(Path(f"file_{i}.mp4"), size=100, extension="mp4") 
             for i in range(1500)]
    config = Config(shard_cap=500, ...)
    
    plan = compute_shard_plan(files, config)
    
    shard_counts = Counter(a.shard_index for a in plan)
    assert all(count <= 500 for count in shard_counts.values())
    assert set(shard_counts.keys()) == {1, 2, 3}


def test_sorting_by_size_ascending():
    files = [
        FileRecord(Path("big.mp4"), size=1000, extension="mp4"),
        FileRecord(Path("small.mp4"), size=100, extension="mp4"),
        FileRecord(Path("medium.mp4"), size=500, extension="mp4"),
    ]
    config = Config(sort_by="size", sort_dir="asc", ...)
    
    plan = compute_shard_plan(files, config)
    
    sizes = [f.size for f in get_files_in_order(plan, files)]
    assert sizes == [100, 500, 1000]
```

### Integration Testing with Fake Filesystem

```python
# tests/test_executor.py — Tests I/O logic with fake implementations

def test_execute_creates_symlinks():
    fs = InMemoryFileSystem()
    fs.add_file(Path("/src/video.mp4"), size=1000)
    
    plan = [ShardAssignment(
        source=Path("/src/video.mp4"),
        target=Path("/out/mp4/shard_1/video.mp4"),
        shard_index=1
    )]
    
    execute_plan(plan, fs)
    
    assert fs.is_symlink(Path("/out/mp4/shard_1/video.mp4"))
    assert fs.readlink(Path("/out/mp4/shard_1/video.mp4")) == Path("/src/video.mp4")
```

---

## Part V: Anti-Pattern Reference

### Anti-Pattern #1: Flat Package Layout

```python
# ❌ Package at project root — import behavior is unpredictable
project/
├── my_tool/          # Package lives at root
│   └── __init__.py
├── tests/
└── pyproject.toml

# When you run `python` from project/, this happens:
>>> import my_tool  # Imports from local dir, NOT installed package!

# ✅ src/ layout — forces installation, predictable imports
project/
├── src/
│   └── my_tool/      # Package inside src/
│       └── __init__.py
├── tests/
└── pyproject.toml

# Now `import my_tool` ONLY works after `pip install -e .`
# Tests always run against the installed version
```

**Why it matters:** The flat layout lets you accidentally test code that isn't 
actually in your package. You'll discover this in CI when imports fail, or worse,
in production when files you thought were included are missing.

---

### Anti-Pattern #2: The Boolean Trap

```python
# ❌ What does `True, False, True` mean?
process_files(True, False, True)

# ✅ Self-documenting
process_files(recursive=True, follow_symlinks=False, include_hidden=True)

# ✅ Even better: use a config object
process_files(config)
```

### Anti-Pattern #3: Silent Failure

```python
# ❌ Swallows errors, debugging nightmare
def safe_delete(path):
    try:
        os.remove(path)
    except:
        pass

# ✅ Explicit about failure modes
def delete_file(path: Path) -> DeleteResult:
    try:
        path.unlink()
        return DeleteResult.success(path)
    except FileNotFoundError:
        return DeleteResult.not_found(path)
    except PermissionError as e:
        return DeleteResult.permission_denied(path, e)
```

### Anti-Pattern #4: Stringly Typed

```python
# ❌ Errors only caught at runtime, deep in execution
def process(sort: str, direction: str):
    if sort == "siez":  # Typo undetected
        ...

# ✅ Errors caught at definition time
from typing import Literal

SortStrategy = Literal["size", "name", "date"]
SortDirection = Literal["asc", "desc"]

def process(sort: SortStrategy, direction: SortDirection):
    ...
```

### Anti-Pattern #5: God Function

```python
# ❌ 500-line function that does everything
def main():
    # Parse args (50 lines)
    # Validate config (100 lines)
    # Scan files (80 lines)
    # Sort files (30 lines)
    # Create directories (40 lines)
    # Create symlinks (60 lines)
    # Write log (50 lines)
    # Handle errors (90 lines)

# ✅ Composed of focused functions
def main():
    config = load_config(parse_args())
    validate(config).raise_if_invalid()
    plan = compute_plan(scan(config.src), config)
    execute(plan, filesystem_for(config))
```

### Anti-Pattern #6: Premature Optimization

```python
# ❌ "Optimized" but unreadable, probably not even faster
files = [f for d in dirs for f in os.scandir(d) if f.is_file() and 
         f.name.split('.')[-1].lower() in exts and f.stat().st_size > 0]

# ✅ Clear intent, profile before optimizing
def find_matching_files(root: Path, extensions: set[str]) -> Iterator[FileRecord]:
    """Recursively find files matching given extensions."""
    for entry in os.scandir(root):
        if entry.is_dir(follow_symlinks=False):
            yield from find_matching_files(Path(entry.path), extensions)
        elif entry.is_file():
            ext = Path(entry.name).suffix.lstrip('.').lower()
            if ext in extensions:
                yield FileRecord(
                    path=Path(entry.path),
                    size=entry.stat().st_size,
                    extension=ext
                )
```

---

## Part VI: Evaluation Checklist

### Pre-Implementation Review

- [ ] Using `src/` layout (not flat layout)?
- [ ] Is the input/output contract clearly defined?
- [ ] Are all side effects identified and controllable?
- [ ] Is there a validation phase separate from execution?
- [ ] Is there a planning phase that can be inspected (--dry-run)?
- [ ] Are error cases categorized with clear remediation?
- [ ] Is configuration separated from code?
- [ ] Can this run unattended (--yes flag)?
- [ ] Is the operation idempotent?
- [ ] Is there an atomicity/rollback strategy?

### Code Review Criteria

- [ ] Functions have single, clear responsibility
- [ ] Pure functions are separated from side-effectful ones
- [ ] Dependencies are injected, not imported/hardcoded
- [ ] Error types are specific and actionable
- [ ] Input normalization happens at the boundary
- [ ] Logging is leveled and structured
- [ ] Tests cover the functional core exhaustively
- [ ] Help text includes examples

### Post-Implementation Validation

- [ ] `--help` output is clear and complete
- [ ] `--dry-run` shows exactly what would happen
- [ ] Running twice produces identical results (idempotent)
- [ ] Errors include remediation suggestions
- [ ] Ctrl+C leaves system in clean state
- [ ] Exit codes are meaningful and documented

---

## Appendix: Module Structure Template (src Layout)

**Always use the `src/` layout** for production tools. This is the 
[PyPA recommended approach](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).

### Why `src/` Layout Over Flat Layout?

**The Flat Layout Anti-Pattern:**
```
# ❌ POOR TASTE: Package at project root
my_tool/                    # Project root
├── my_tool/                # Package (same name = confusion)
│   ├── __init__.py
│   └── cli.py
├── tests/
└── pyproject.toml
```

**Why it's wrong:**
- Python may import from project root instead of installed package
- Tests might pass locally but fail after installation
- Accidental imports of unpackaged files (README, config)
- CWD pollution: `import my_tool` behavior depends on where you run Python

**The `src/` Layout Pattern:**
```
# ✅ GOOD TASTE: Clean separation via src/ directory
project_root/
├── pyproject.toml          # Package metadata & build config
├── README.md
├── .github/
│   └── workflows/
│       └── ci.yml          # CI/CD pipeline
├── src/
│   └── my_tool/            # All importable code lives here
│       ├── __init__.py
│       ├── __main__.py     # Entry: `python -m my_tool`
│       ├── cli.py          # Argument parsing, help text
│       ├── config.py       # Config dataclass, validation, loading
│       ├── core/
│       │   ├── __init__.py
│       │   ├── scanner.py  # File discovery (imperative)
│       │   ├── planner.py  # Plan computation (pure)
│       │   └── executor.py # Plan execution (imperative)
│       ├── validation.py   # Pre-flight checks
│       ├── logging.py      # Logger setup, progress reporting  
│       ├── errors.py       # Exception hierarchy
│       ├── types.py        # Shared type definitions
│       └── interfaces/
│           ├── __init__.py
│           ├── filesystem.py   # FS protocol + implementations
│           └── progress.py     # Progress protocol + implementations
└── tests/                  # Tests OUTSIDE src/ (not packaged)
    ├── unit/
    │   ├── test_planner.py     # Pure logic tests
    │   └── test_config.py      # Config validation tests
    ├── integration/
    │   └── test_executor.py    # Tests with fake FS
    └── e2e/
        └── test_cli.py         # Full subprocess tests
```

### Benefits of `src/` Layout

| Benefit | Explanation |
|---------|-------------|
| **Import safety** | Forces `pip install -e .` — tests run against *installed* code, not local edits |
| **Clean packages** | Only `src/` contents get packaged; no README or config in your wheel |
| **No CWD pollution** | Python won't accidentally import project root files |
| **Clear boundaries** | Code vs tests vs config are unambiguous |
| **CI/CD parity** | Local dev environment matches production installation |

### Development Workflow

```bash
# Create virtual environment and install in editable mode
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"    # Install package + dev dependencies

# Run tests (against installed package, not source)
pytest tests/

# Run the tool
python -m my_tool --help

# Or via entry point (if defined in pyproject.toml)
my-tool --help
```

### pyproject.toml Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-tool"
version = "0.1.0"
description = "A well-designed CLI tool"
requires-python = ">=3.11"
dependencies = [
    "rich>=13.0",  # Progress bars, pretty printing
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

[project.scripts]
my-tool = "my_tool.cli:main"  # Entry point

[tool.hatch.build.targets.wheel]
packages = ["src/my_tool"]
```

---

*"Perfection is achieved not when there is nothing more to add,
but when there is nothing left to take away."*
— Antoine de Saint-Exupéry
