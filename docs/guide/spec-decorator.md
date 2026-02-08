# @spec Decorator

The `@spec` decorator is the foundation of Specwright. It turns a function's type hints and docstring into an enforced contract — checked at decoration time and validated at every call.

## Basic Usage

```python
from specwright import spec

@spec
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y
```

This single decorator does three things:

1. **Decoration-time checks**: Validates that the function has a docstring and complete type annotations
2. **Runtime input validation**: Checks that arguments match declared types before the function runs
3. **Runtime output validation**: Checks that the return value matches the declared return type

## With and Without Parentheses

Both forms work:

```python
# Bare decorator
@spec
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y

# With parentheses (no-op, same effect)
@spec()
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y
```

## Configuration Options

```python
@spec(
    validate_inputs=True,     # Check argument types at runtime (default: True)
    validate_output=True,     # Check return type at runtime (default: True)
    require_docstring=True,   # Require a docstring at decoration time (default: True)
)
def my_function(x: int) -> int:
    """My function."""
    return x
```

### Disabling Input Validation

```python
@spec(validate_inputs=False)
def flexible_input(x: int) -> int:
    """Accept anything, validate output only."""
    return int(x)

flexible_input("42")  # No error — input validation is off
```

### Disabling Output Validation

```python
@spec(validate_output=False)
def in_progress(x: int) -> str:
    """Return type may not match during development."""
    return x  # No error — output validation is off
```

### Disabling Docstring Requirement

```python
@spec(require_docstring=False)
def internal_helper(x: int) -> int:
    return x * 2  # No error — docstring not required
```

## Decoration-Time Checks

These run once when the decorator is applied (at module import time):

### Docstring Enforcement

```python
@spec
def bad():  # (1)!
    return 42
```

1. Missing docstring and type hints

```
MissingDocstringError: Function 'bad' is missing a docstring.
All @spec-decorated functions must have a docstring describing their behavior.
```

### Type Hint Completeness

```python
@spec
def bad(x, y: int) -> int:  # (1)!
    """Add numbers."""
    return x + y
```

1. `x` is missing a type hint

```
MissingTypeHintError: Function 'bad' is missing type hints for: x.
All @spec-decorated functions must have complete type annotations.
```

The check also requires a return type annotation:

```python
@spec
def bad(x: int):  # (1)!
    """Do something."""
    return x
```

1. Missing `-> type` return annotation

```
MissingTypeHintError: Function 'bad' is missing type hints for: return.
```

!!! note "self and cls are skipped"
    Methods don't need type hints on `self` or `cls` — Specwright skips those automatically. `*args` and `**kwargs` are also skipped.

## Runtime Input Validation

When the function is called, Specwright validates each argument against its type hint using Pydantic's `TypeAdapter`:

```python
@spec
def greet(name: str, excited: bool) -> str:
    """Greet someone."""
    suffix = "!" if excited else "."
    return f"Hello, {name}{suffix}"

greet("Alice", True)     # "Hello, Alice!"
greet(42, True)          # InputValidationError
greet("Alice", "yes")    # InputValidationError
```

### Error Messages

```
InputValidationError: Input validation failed for 'greet':
  - Parameter 'name': expected <class 'str'>, got int (42)
```

Multiple violations are reported at once:

```
InputValidationError: Input validation failed for 'greet':
  - Parameter 'name': expected <class 'str'>, got int (42)
  - Parameter 'excited': expected <class 'bool'>, got str ('yes')
```

### Strict Type Checking

Specwright uses **strict** mode for type checking. This means:

- `bool` is **not** accepted for `int` (since `bool` is a subclass of `int` in Python, this is a common source of bugs)
- `int` **is** accepted for `float` (standard numeric promotion)

```python
@spec
def count(n: int) -> int:
    """Count to n."""
    return n

count(True)   # InputValidationError — bool rejected for int
count(5)      # Works fine
```

## Complex Type Support

Specwright handles generics, unions, optionals, and Pydantic models:

```python
from typing import Optional

@spec
def first_or_default(items: list[int], default: Optional[int] = None) -> int:
    """Return the first item, or default if the list is empty."""
    return items[0] if items else (default if default is not None else 0)

first_or_default([1, 2, 3])         # 1
first_or_default([], 42)            # 42
first_or_default(["a", "b"])        # InputValidationError
```

```python
@spec
def process(data: dict[str, list[int]]) -> list[int]:
    """Flatten all values from a dict of int lists."""
    return [v for vals in data.values() for v in vals]
```

## Metadata

Every `@spec`-decorated function gets a `__spec__` attribute containing a `SpecMetadata` dataclass:

```python
@spec
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

meta = greet.__spec__
meta.name          # "greet"
meta.qualname      # "greet"
meta.module        # "__main__"
meta.docstring     # "Greet someone by name."
meta.parameters    # {"name": <class 'str'>}
meta.return_type   # <class 'str'>
```

This metadata is:

- **Frozen** (immutable after creation)
- Used by `specwright docs` to generate API documentation
- Used by `specwright validate` to check test coverage
- Available for LLMs to read and understand function contracts

## Combining with Other Decorators

`@spec` composes naturally with `@handle_errors`, `@transition`, and `@requires_tests`. See [Error Handling](error-handling.md) and [State Machines](state-machines.md) for details.

!!! tip "Why this matters for LLM-assisted development"
    The `@spec` decorator creates a **verifiable contract**. When you ask an LLM to implement a function, the decorator ensures the implementation actually matches the declared interface — types are checked, docstrings are required, and metadata is preserved for tooling. The LLM can't silently return the wrong type or forget to document a function.

## Common Pitfalls

!!! warning "Don't forget the return type"
    ```python
    # Wrong — will raise MissingTypeHintError
    @spec
    def add(x: int, y: int):
        """Add numbers."""
        return x + y

    # Correct
    @spec
    def add(x: int, y: int) -> int:
        """Add numbers."""
        return x + y
    ```

!!! warning "Docstrings must be non-empty"
    ```python
    # Wrong — whitespace-only docstrings are rejected
    @spec
    def add(x: int, y: int) -> int:
        """   """
        return x + y
    ```

!!! warning "bool is not int"
    Specwright uses strict validation. `True` and `False` won't be accepted where `int` is expected:
    ```python
    @spec
    def count(n: int) -> int:
        """Count."""
        return n

    count(True)   # InputValidationError
    count(1)      # Fine
    ```
