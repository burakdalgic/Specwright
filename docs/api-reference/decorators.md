# Decorators API Reference

## @spec

```python
from specwright import spec
```

Decorator that enforces specifications on functions. Performs decoration-time checks (docstring presence, type hint completeness) and runtime checks (input/output type validation).

### Signatures

```python
# Bare decorator
@spec
def func(x: int) -> int:
    """Docstring."""
    ...

# With options
@spec(validate_inputs=True, validate_output=True, require_docstring=True)
def func(x: int) -> int:
    """Docstring."""
    ...
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `validate_inputs` | `bool` | `True` | Check argument types at runtime |
| `validate_output` | `bool` | `True` | Check return type at runtime |
| `require_docstring` | `bool` | `True` | Require a docstring at decoration time |

### Raises

| Exception | When |
|-----------|------|
| `MissingDocstringError` | Function has no docstring (and `require_docstring=True`) |
| `MissingTypeHintError` | Function has incomplete type annotations |
| `InputValidationError` | Runtime argument type mismatch (and `validate_inputs=True`) |
| `OutputValidationError` | Runtime return type mismatch (and `validate_output=True`) |

### Attached Metadata

Decorated functions gain a `__spec__` attribute containing a `SpecMetadata` instance.

---

## SpecMetadata

```python
from specwright import SpecMetadata
```

Frozen dataclass containing metadata extracted from a `@spec`-decorated function.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Function's simple name |
| `qualname` | `str` | Function's qualified name |
| `module` | `str \| None` | Module where the function is defined |
| `docstring` | `str` | Function's docstring |
| `parameters` | `dict[str, Any]` | Mapping of parameter names to type hints |
| `return_type` | `Any` | Return type hint |

### Example

```python
@spec
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y

meta = add.__spec__
assert meta.name == "add"
assert meta.parameters == {"x": int, "y": int}
assert meta.return_type is int
```

---

## @handle_errors

```python
from specwright import handle_errors
```

Decorator for declarative error handling. Maps exception types to handling strategies.

### Signature

```python
@handle_errors(handlers: dict[type[BaseException], Any])
def func():
    ...
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `handlers` | `dict[type[BaseException], Any]` | Mapping of exception types to strategies |

### Strategies

| Strategy | Type | Behavior |
|----------|------|----------|
| `"ignore"` | `str` | Suppress exception, return `None` |
| `"log"` | `str` | Log with traceback, re-raise |
| callable | `Callable[[BaseException], Any]` | Call handler, return its result |
| any other value | `Any` | Return the value directly |

### Raises

| Exception | When |
|-----------|------|
| `HandlingStrategyError` | A handler key is not an exception type |

### Example

```python
@handle_errors({
    ValueError: "ignore",
    KeyError: lambda e: f"missing: {e}",
    RuntimeError: "log",
    ConnectionError: {"error": "offline"},
})
def process(data: dict) -> str:
    ...
```

---

## @requires_tests

```python
from specwright import requires_tests
```

Decorator that specifies required test scenarios for a function.

### Signature

```python
@requires_tests(
    happy_path: bool = True,
    edge_cases: list[str] | None = None,
    error_cases: list[str] | None = None,
)
def func():
    ...
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `happy_path` | `bool` | `True` | Require a `test_{name}_happy_path` test |
| `edge_cases` | `list[str] \| None` | `None` | Edge case scenario names |
| `error_cases` | `list[str] \| None` | `None` | Error case scenario names |

### Naming Convention

```
test_{function_name}_happy_path     (when happy_path=True)
test_{function_name}_{case_name}    (for each edge/error case)
```

### Attached Metadata

Decorated functions gain a `__test_requirements__` attribute containing a `TestRequirements` instance.

---

## TestRequirements

```python
from specwright import TestRequirements
```

Frozen dataclass describing the test cases required for a function.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `function_name` | `str` | Simple function name |
| `qualname` | `str` | Qualified function name |
| `module` | `str \| None` | Module where the function is defined |
| `happy_path` | `bool` | Whether a happy-path test is required |
| `edge_cases` | `tuple[str, ...]` | Edge case scenario names |
| `error_cases` | `tuple[str, ...]` | Error case scenario names |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `expected_test_names` | `list[str]` | Computed list of required test function names |

### Example

```python
@requires_tests(
    happy_path=True,
    edge_cases=["empty"],
    error_cases=["invalid"],
)
def process(x: int) -> int:
    return x

reqs = process.__test_requirements__
assert reqs.expected_test_names == [
    "test_process_happy_path",
    "test_process_empty",
    "test_process_invalid",
]
```
