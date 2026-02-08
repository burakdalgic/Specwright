# Best Practices

Patterns and guidelines for getting the most out of Specwright.

## Writing Good Specs

### Be Specific in Docstrings

Docstrings are the primary way you communicate intent to both LLMs and other developers. Be specific about behavior, not just what the function "does":

```python
# Vague
@spec
def process(data: list[int]) -> list[int]:
    """Process the data."""
    ...

# Specific
@spec
def remove_outliers(data: list[int]) -> list[int]:
    """Remove values more than 2 standard deviations from the mean.

    Returns a new list with outliers removed. Does not modify the input.
    Raises ValueError if the list has fewer than 3 elements.
    """
    ...
```

### Use Precise Types

Prefer specific types over generic ones:

```python
# Too broad
@spec
def get_user(user_id: Any) -> dict:
    """Get a user."""
    ...

# Precise
@spec
def get_user(user_id: int) -> dict[str, str | int]:
    """Get a user by their numeric ID."""
    ...
```

### Declare Error Cases Explicitly

Use `@requires_tests` error cases to document what can go wrong:

```python
@requires_tests(
    happy_path=True,
    error_cases=["empty_list", "negative_values", "overflow"],
)
@spec
def aggregate(values: list[float]) -> float:
    """Sum all values, raising ValueError for empty lists or negatives."""
    ...
```

## State Machine Design

### Keep States Minimal

Every state should represent a meaningfully different condition:

```python
# Too many states
class Order(StateMachine):
    states = ["created", "pending", "waiting", "processing", "almost_done", "done"]
    ...

# Clear, meaningful states
class Order(StateMachine):
    states = ["pending", "paid", "shipped", "delivered"]
    ...
```

### Use Hooks for Side Effects

Keep transition methods focused on core logic. Use hooks for notifications, logging, and other side effects:

```python
class Order(StateMachine):
    states = ["pending", "paid", "shipped"]
    initial_state = "pending"

    @transition(from_state="pending", to_state="paid")
    def pay(self, amount: float) -> str:
        # Core logic only
        return f"Paid ${amount:.2f}"

    def on_enter_paid(self):
        # Side effects in hooks
        send_confirmation_email(self.order_id)
        update_analytics("payment_received")
```

### Always Call super().__init__()

If you override `__init__`, always call super:

```python
class Order(StateMachine):
    states = ["pending", "paid"]
    initial_state = "pending"

    def __init__(self, order_id: str):
        super().__init__()  # Required!
        self.order_id = order_id
```

## Error Handling Patterns

### Specific Before General

Order handlers from most specific to most general:

```python
@handle_errors({
    FileNotFoundError: lambda e: None,     # Most specific
    PermissionError: lambda e: None,
    OSError: "log",                         # Less specific
    Exception: lambda e: "unknown error",   # Catch-all
})
def read_config(path: str) -> dict | str | None:
    ...
```

### Match Return Types

When using `@spec` with `@handle_errors`, ensure fallback values match the declared return type:

```python
# Good — fallback matches return type
@spec
@handle_errors({ValueError: 0})
def parse_int(s: str) -> int:
    """Parse string to int."""
    return int(s)

# Bad — fallback is str but return type is int
@spec
@handle_errors({ValueError: "error"})
def parse_int(s: str) -> int:
    """Parse string to int."""
    return int(s)
# OutputValidationError when ValueError is caught
```

## Testing Patterns

### Name Tests Consistently

Follow the `test_{function}_{scenario}` convention:

```python
def test_create_user_happy_path():
    """Normal successful creation."""

def test_create_user_empty_email():
    """Edge case: empty email string."""

def test_create_user_invalid_age():
    """Error case: negative age."""
```

### Test One Thing Per Function

Each test should verify a single behavior:

```python
# Good — one assertion per test
def test_create_user_happy_path():
    result = create_user("alice@example.com", 30)
    assert result["email"] == "alice@example.com"

def test_create_user_returns_id():
    result = create_user("alice@example.com", 30)
    assert "id" in result

# Avoid — testing multiple unrelated things
def test_create_user_everything():
    result = create_user("alice@example.com", 30)
    assert result["email"] == "alice@example.com"
    assert "id" in result
    with pytest.raises(ValueError):
        create_user("bad", -1)
```

### Use Strict Enforcement in CI

Set `strict` mode in your CI configuration:

```toml
# pyproject.toml
[tool.pytest.ini_options]
specwright_test_enforcement = "strict"
```

Use `off` or `warn` during local development when you're iterating.

## Project Organization

### One Function Per File (For Generated Code)

When using `specwright new function`, each function gets its own file. This makes it easy to hand individual files to LLMs:

```
my_project/
  create_user.py
  delete_user.py
  search_users.py
  tests/
    test_create_user.py
    test_delete_user.py
    test_search_users.py
```

### Group Related State Machines

State machines that model the same domain can share a module:

```
my_project/
  order_workflow.py       # OrderProcessor, PaymentStateMachine
  tests/
    test_order_workflow.py
```

### Validate Early, Validate Often

Run `specwright validate` as part of your development loop:

```bash
# After implementing
specwright validate --path .

# In CI
specwright validate --path . && pytest tests/
```

## Antipatterns

!!! danger "Don't disable all validation"
    ```python
    # Defeats the purpose of @spec
    @spec(validate_inputs=False, validate_output=False, require_docstring=False)
    def func(x):
        return x
    ```

!!! danger "Don't catch SpecwrightError in production"
    ```python
    # Hides real bugs
    try:
        result = my_function(data)
    except SpecwrightError:
        pass  # Silently ignoring type violations
    ```

!!! danger "Don't skip test requirements"
    ```python
    # If you declare test requirements, write the tests
    @requires_tests(happy_path=True, edge_cases=["empty"])
    @spec
    def process(x: list) -> list:
        """Process."""
        ...
    # Don't just set enforcement = "off" to make the error go away
    ```
