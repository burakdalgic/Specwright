# CLI Usage

Specwright includes a command-line tool for scaffolding projects, generating code, validating coverage, and producing documentation.

## Overview

```bash
specwright --help
```

| Command | Description |
|---------|-------------|
| `specwright init` | Scaffold a new project |
| `specwright new function` | Generate a @spec-decorated function |
| `specwright new statemachine` | Generate a StateMachine subclass |
| `specwright validate` | Check specs and test coverage |
| `specwright docs` | Generate API documentation |

## specwright init

Scaffold a complete project with the right structure:

```bash
specwright init my_project
```

Creates:

```
my_project/
  pyproject.toml          # Poetry config with specwright dependency
  .specwright.toml        # Specwright configuration
  README.md
  my_project/
    __init__.py           # Sample @spec function
  tests/
    __init__.py
  examples/
```

### Default Project Name

```bash
specwright init
# Creates my_specwright_project/
```

### What's in the Generated Files

**pyproject.toml** — Pre-configured with specwright as a dependency and pytest settings:

```toml
[tool.poetry.dependencies]
python = "^3.11"
specwright = "^0.1.0"

[tool.pytest.ini_options]
testpaths = ["tests"]
specwright_test_enforcement = "strict"
```

**`__init__.py`** — A sample `@spec` function to get you started:

```python
from specwright import spec

@spec
def hello(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"
```

**.specwright.toml** — Project-level configuration:

```toml
[specwright]
test_enforcement = "strict"
test_pattern = "test_*.py"
```

!!! warning "Existing directory"
    `init` will refuse to overwrite an existing directory:
    ```bash
    $ specwright init my_project
    Error: 'my_project' already exists.
    ```

## specwright new function

Generate a `@spec`-decorated function and its test file:

```bash
specwright new function calculate_score \
    --params "base: int, multiplier: float" \
    --returns float
```

Creates two files:

**`calculate_score.py`**:
```python
from specwright import spec

@spec
def calculate_score(base: int, multiplier: float) -> float:
    """TODO: Describe what calculate_score does."""
    ...
```

**`test_calculate_score.py`**:
```python
from calculate_score import calculate_score

def test_calculate_score_happy_path():
    result = calculate_score(0, 0.0)
    # TODO: Add assertions
    ...
```

### Interactive Mode

Omit `--params` and `--returns` to be prompted:

```bash
$ specwright new function greet
Parameters (e.g. 'x: int, y: str') [x: int]: name: str, excited: bool
Return type [int]: str
Created greet.py
Created test_greet.py
```

### Options

| Flag | Description |
|------|-------------|
| `--params` | Parameter list (e.g. `"x: int, y: str"`) |
| `--returns` | Return type (e.g. `"int"`) |
| `--no-tests` | Skip test file generation |
| `--output-dir` | Output directory (default: `.`) |

### Test File Placement

If a `tests/` directory exists in the output directory, the test file goes there:

```bash
$ ls
tests/
$ specwright new function calc --params "x: int" --returns int
Created calc.py
Created tests/test_calc.py    # Placed in tests/
```

### Validation

Invalid Python identifiers are rejected:

```bash
$ specwright new function 123bad
Error: '123bad' is not a valid Python identifier.
```

Existing files are not overwritten:

```bash
$ specwright new function calc --params "x: int" --returns int
Error: 'calc.py' already exists.
```

## specwright new statemachine

Generate a `StateMachine` subclass with sequential transitions:

```bash
specwright new statemachine order_processor \
    --states pending,paid,shipped,delivered
```

Creates **`order_processor.py`** with a class `OrderProcessor` containing transitions between consecutive states (`pending` -> `paid` -> `shipped` -> `delivered`).

### Options

| Flag | Description |
|------|-------------|
| `--states` | Comma-separated state names |
| `--initial` | Initial state (default: first state) |
| `--no-tests` | Skip test file generation |
| `--output-dir` | Output directory (default: `.`) |

### Interactive Mode

Omit `--states` to be prompted:

```bash
$ specwright new statemachine workflow
States (comma-separated) [idle,running,done]: open,review,merged,closed
Created workflow.py
Created test_workflow.py
```

### Custom Initial State

```bash
specwright new statemachine machine --states off,on --initial off
```

The initial state must be in the states list:

```bash
$ specwright new statemachine machine --states a,b --initial z
Error: Initial state 'z' not in states: ['a', 'b']
```

## specwright validate

Scan a project and check that all `@spec`-decorated functions have tests and state machines are well-formed:

```bash
specwright validate --path .
```

### What It Checks

1. **Test coverage** — Every `@spec`-decorated function should have at least one `test_<name>_*` function
2. **@requires_tests compliance** — All required test names from `@requires_tests` decorators must exist
3. **State machine reachability** — All states should be reachable from the initial state via transitions

### Output

```
┌────────────────────────────┬────────┐
│ Check                      │ Status │
├────────────────────────────┼────────┤
│ Tests for add              │ pass   │
│ Tests for multiply         │ FAIL   │
│ SM OrderProcessor reacha…  │ pass   │
└────────────────────────────┴────────┘

1 issue(s) found:
  x No tests found for 'multiply' (expected test_multiply_*)
```

Exit code is `1` if any issues are found, `0` if everything passes.

### No Specs Found

If the scanned directory has no `@spec` functions or state machines:

```bash
$ specwright validate --path .
No spec'd functions or state machines found.
```

## specwright docs

Generate Markdown API documentation from `@spec` metadata:

```bash
specwright docs --path .
```

### Output to File

```bash
specwright docs --path . --output API.md
```

### Include State Diagrams

```bash
specwright docs --path . --diagram
```

This generates DOT-format state diagrams for each `StateMachine` class found.

### Generated Format

The output includes:

- Function name and docstring
- Parameter table (name, type)
- Return type
- Required tests (from `@requires_tests`)
- State machine states, transitions table, and optional diagrams

## Workflow

The typical Specwright workflow:

```bash
# 1. Scaffold a project
specwright init my_project
cd my_project

# 2. Generate components
specwright new function process_payment \
    --params "amount: float, currency: str" \
    --returns dict
specwright new statemachine order_flow \
    --states pending,paid,shipped,delivered

# 3. Fill in implementations (you or an LLM)

# 4. Validate coverage
specwright validate

# 5. Generate docs
specwright docs --output API.md
```

!!! tip "Why this matters for LLM-assisted development"
    The CLI generates the spec scaffolding — type hints, docstrings, test stubs, state machine structure. An LLM can then fill in the implementations, guided by the spec. The `validate` command ensures nothing was forgotten, and `docs` produces documentation directly from the code's metadata.
