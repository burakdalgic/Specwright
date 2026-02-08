"""Example: API endpoint with multiple error handlers.

Demonstrates how @handle_errors provides declarative error handling
for a simulated HTTP request handler, mapping domain exceptions to
appropriate HTTP-style responses.
"""

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


# --- Simulated data store ---

USERS = {
    1: {"name": "Alice", "role": "admin"},
    2: {"name": "Bob", "role": "viewer"},
}


# --- Handler functions ---


def bad_request(exc: BaseException) -> Response:
    """Convert validation errors to 400 responses."""
    return Response(400, f"Bad request: {exc}")


def not_found(exc: BaseException) -> Response:
    """Convert lookup failures to 404 responses."""
    return Response(404, f"Not found: {exc}")


# --- Endpoint ---


@handle_errors(
    {
        ValueError: bad_request,
        ValidationError: bad_request,
        NotFoundError: not_found,
        ForbiddenError: lambda e: Response(403, f"Forbidden: {e}"),
        Exception: lambda e: Response(500, f"Internal server error: {e}"),
    }
)
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
    # Successful lookup
    print(get_user(1))  # Response(status=200, body="User: Alice (admin)")

    # Not found
    print(get_user(99))  # Response(status=404, body="Not found: User 99")

    # Bad input
    print(get_user(-1))  # Response(status=400, body="Bad request: ...")

    # Inspect the spec metadata through the layers
    print(f"\nEndpoint spec: {get_user.__wrapped__.__spec__}")  # type: ignore[attr-defined]
