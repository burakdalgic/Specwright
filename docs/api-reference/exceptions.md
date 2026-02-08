# Exceptions API Reference

All Specwright exceptions inherit from `SpecwrightError`, making it easy to catch any framework error.

## Hierarchy

```
SpecwrightError (base)
├── SpecError (specification violations)
│   ├── InputValidationError
│   ├── OutputValidationError
│   ├── MissingDocstringError
│   └── MissingTypeHintError
├── HandlingStrategyError
├── ValidationError
├── InvalidTransitionError
├── InvalidStateError
├── MissingTestsError
└── InvalidTestNameError
```

## Exception Reference

### SpecwrightError

```python
from specwright import SpecwrightError
```

Base exception for all Specwright errors. Catch this to handle any framework-level error:

```python
try:
    result = my_function(bad_input)
except SpecwrightError as e:
    print(f"Specwright error: {e}")
```

---

### SpecError

```python
from specwright import SpecError
```

Base exception for specification validation errors. Parent of all `@spec`-related errors.

---

### InputValidationError

```python
from specwright import InputValidationError
```

Raised when function arguments violate declared type specifications.

```python
@spec
def add(x: int, y: int) -> int:
    """Add."""
    return x + y

add("one", 2)
# InputValidationError: Input validation failed for 'add':
#   - Parameter 'x': expected <class 'int'>, got str ('one')
```

---

### OutputValidationError

```python
from specwright import OutputValidationError
```

Raised when a function's return value violates the declared return type.

```python
@spec
def bad() -> int:
    """Should return int."""
    return "not an int"

bad()
# OutputValidationError: Output validation failed for 'bad':
#   expected <class 'int'>, got str ('not an int')
```

---

### MissingDocstringError

```python
from specwright import MissingDocstringError
```

Raised at decoration time when a `@spec`-decorated function lacks a docstring.

---

### MissingTypeHintError

```python
from specwright import MissingTypeHintError
```

Raised at decoration time when a `@spec`-decorated function has incomplete type annotations.

---

### HandlingStrategyError

```python
from specwright import HandlingStrategyError
```

Raised when an invalid error handling strategy is configured (e.g., a non-exception type as a handler key).

---

### ValidationError

```python
from specwright import ValidationError
```

General-purpose validation error for use as a return value or exception in application code.

---

### InvalidTransitionError

```python
from specwright import InvalidTransitionError
```

Raised when an invalid state transition is attempted.

```python
order = OrderProcessor()
order.ship("TRACK-123")
# InvalidTransitionError: Cannot transition from 'pending' to 'shipped'
# via 'ship'. Valid source state(s): paid
```

---

### InvalidStateError

```python
from specwright import InvalidStateError
```

Raised at class definition time when a state machine references an invalid state.

---

### MissingTestsError

```python
from specwright import MissingTestsError
```

Raised by the pytest plugin (in strict mode) when required tests are missing.

---

### InvalidTestNameError

```python
from specwright import InvalidTestNameError
```

Raised when a test case name doesn't follow the `test_{function_name}_{case_name}` naming convention.
