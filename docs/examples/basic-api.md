# Basic API Example

This example builds a type-safe API endpoint with declarative error handling, showing how `@spec` and `@handle_errors` work together.

## The Setup

Imagine a simple user lookup endpoint. We want:

- Type-validated inputs
- Clear error responses for different failure modes
- No scattered try/except blocks

## Step 1: Define Response Type

```python
from dataclasses import dataclass

@dataclass
class Response:
    status: int
    body: str
```

## Step 2: Define Error Handlers

```python
from specwright import ValidationError, handle_errors, spec

class NotFoundError(Exception):
    pass

class ForbiddenError(Exception):
    pass

def bad_request(exc: BaseException) -> Response:
    """Convert validation errors to 400 responses."""
    return Response(400, f"Bad request: {exc}")

def not_found(exc: BaseException) -> Response:
    """Convert lookup failures to 404 responses."""
    return Response(404, f"Not found: {exc}")
```

## Step 3: Build the Endpoint

```python
USERS = {
    1: {"name": "Alice", "role": "admin"},
    2: {"name": "Bob", "role": "viewer"},
}

@handle_errors({
    ValueError: bad_request,
    ValidationError: bad_request,
    NotFoundError: not_found,
    ForbiddenError: lambda e: Response(403, f"Forbidden: {e}"),
    Exception: lambda e: Response(500, f"Internal server error: {e}"),
})
@spec
def get_user(user_id: int) -> Response:
    """Look up a user by ID and return an HTTP-style response."""
    if user_id < 0:
        raise ValueError("user_id must be non-negative")

    user = USERS.get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id}")

    return Response(200, f"User: {user['name']} ({user['role']})")
```

## Step 4: See It in Action

```python
>>> get_user(1)
Response(status=200, body="User: Alice (admin)")

>>> get_user(99)
Response(status=404, body="Not found: User 99")

>>> get_user(-1)
Response(status=400, body="Bad request: user_id must be non-negative")

>>> get_user("bad")  # Type validation catches this
# InputValidationError: Input validation failed for 'get_user':
#   - Parameter 'user_id': expected <class 'int'>, got str ('bad')
```

Notice that `InputValidationError` is **not** in the handlers dict, so it propagates normally. The `@spec` decorator catches type mismatches before the function body even runs.

## What the Layers Do

```
get_user("bad")
  │
  ├─ @handle_errors: checks if exception matches handlers
  │    │
  │    └─ @spec: validates input types ← catches "bad" here
  │         │
  │         └─ function body: never reached
  │
  └─ InputValidationError propagates (not in handlers)
```

```
get_user(99)
  │
  ├─ @handle_errors: catches NotFoundError → Response(404, ...)
  │    │
  │    └─ @spec: validates input types (99 is int ✓)
  │         │
  │         └─ function body: raises NotFoundError
```

## Complete Source

The full example is at [`examples/api_endpoint.py`](https://github.com/specwright/specwright/blob/main/examples/api_endpoint.py).

```python
"""API endpoint with multiple error handlers."""

from dataclasses import dataclass
from specwright import ValidationError, handle_errors, spec


@dataclass
class Response:
    status: int
    body: str


class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


USERS = {
    1: {"name": "Alice", "role": "admin"},
    2: {"name": "Bob", "role": "viewer"},
}


def bad_request(exc: BaseException) -> Response:
    return Response(400, f"Bad request: {exc}")


def not_found(exc: BaseException) -> Response:
    return Response(404, f"Not found: {exc}")


@handle_errors({
    ValueError: bad_request,
    ValidationError: bad_request,
    NotFoundError: not_found,
    ForbiddenError: lambda e: Response(403, f"Forbidden: {e}"),
    Exception: lambda e: Response(500, f"Internal server error: {e}"),
})
@spec
def get_user(user_id: int) -> Response:
    """Look up a user by ID and return an HTTP-style response."""
    if user_id < 0:
        raise ValueError("user_id must be non-negative")

    user = USERS.get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id}")

    return Response(200, f"User: {user['name']} ({user['role']})")


if __name__ == "__main__":
    print(get_user(1))
    print(get_user(99))
    print(get_user(-1))
```

!!! tip "Why this matters for LLM-assisted development"
    The human defines the error policy (which exceptions map to which responses) and the type contract (int input, Response output). An LLM fills in the lookup logic. If the LLM forgets to handle an edge case, the error handlers catch it. If it returns the wrong type, `@spec` catches it. The error handling architecture is defined by the human, not left to the LLM.
