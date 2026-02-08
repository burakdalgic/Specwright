# CLI API Reference

## specwright

```bash
specwright [OPTIONS] COMMAND [ARGS]...
```

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help and exit |

---

## specwright init

Scaffold a new Specwright project.

```bash
specwright init [PROJECT_NAME]
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `my_specwright_project` | Name of the project directory to create |

### Behavior

Creates a directory with:

| File | Description |
|------|-------------|
| `pyproject.toml` | Poetry config with specwright dependency |
| `.specwright.toml` | Specwright configuration (strict enforcement) |
| `README.md` | Project readme |
| `{name}/__init__.py` | Python package with sample `@spec` function |
| `tests/__init__.py` | Test directory |
| `examples/` | Examples directory |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Project created successfully |
| `1` | Directory already exists |

---

## specwright new function

Generate a `@spec`-decorated function with optional test file.

```bash
specwright new function NAME [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `NAME` | Function name (must be a valid Python identifier) |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--params TEXT` | *(prompted)* | Parameter list (e.g. `"x: int, y: str"`) |
| `--returns TEXT` | *(prompted)* | Return type (e.g. `"int"`) |
| `--tests / --no-tests` | `--tests` | Generate test file |
| `--output-dir PATH` | `.` | Output directory |

### Generated Files

| File | Contents |
|------|----------|
| `{name}.py` | `@spec`-decorated function stub |
| `test_{name}.py` | Test file with happy path stub |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Files created successfully |
| `1` | Invalid name or file already exists |

---

## specwright new statemachine

Generate a `StateMachine` subclass with sequential transitions.

```bash
specwright new statemachine NAME [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `NAME` | Class name in snake_case (converted to PascalCase for the class) |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--states TEXT` | *(prompted)* | Comma-separated state names |
| `--initial TEXT` | *(first state)* | Initial state |
| `--tests / --no-tests` | `--tests` | Generate test file |
| `--output-dir PATH` | `.` | Output directory |

### Generated Files

| File | Contents |
|------|----------|
| `{name}.py` | `StateMachine` subclass with transitions |
| `test_{name}.py` | Test file with transition tests |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Files created successfully |
| `1` | Invalid name, initial state not in states, or file exists |

---

## specwright validate

Scan a project and validate specs, test coverage, and state machine definitions.

```bash
specwright validate [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--path PATH` | `.` | Project root to scan |

### Checks Performed

1. Every `@spec`-decorated function has at least one `test_{name}_*` test function
2. All `@requires_tests` expected test names exist
3. All states in each `StateMachine` are reachable from the initial state

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed (or no specs found) |
| `1` | One or more issues found |

---

## specwright docs

Generate Markdown API documentation from `@spec` metadata.

```bash
specwright docs [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--path PATH` | `.` | Project root to scan |
| `--output PATH` | *(stdout)* | Output file |
| `--diagram / --no-diagram` | `--no-diagram` | Include DOT state diagrams |

### Output Format

- Functions grouped by module
- Parameter tables (name, type)
- Return type
- Required tests from `@requires_tests`
- State machine transition tables
- Optional Graphviz DOT diagrams

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Documentation generated successfully |
