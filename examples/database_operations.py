"""Example: Database operation with rollback on error.

Demonstrates @handle_errors wrapping a simulated database transaction,
automatically rolling back on failure and logging the error.
"""

from __future__ import annotations

from specwright import handle_errors, spec


# --- Simulated database layer ---


class DatabaseError(Exception):
    pass


class IntegrityError(DatabaseError):
    pass


class ConnectionError(DatabaseError):  # noqa: A001
    pass


class Database:
    """Simulated database with transaction support."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.committed = False
        self.rolled_back = False

    def insert(self, key: str, value: str) -> None:
        if key in self.data:
            raise IntegrityError(f"Duplicate key: {key}")
        self.data[key] = value

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True
        self.data.clear()


# --- Global DB instance for the example ---

db = Database()


# --- Handler that performs rollback ---


def rollback_and_report(exc: BaseException) -> dict[str, str]:
    """Roll back the transaction and return an error result."""
    db.rollback()
    return {"status": "error", "message": str(exc), "rolled_back": "true"}


# --- Spec-decorated database operation ---


@handle_errors(
    {
        IntegrityError: rollback_and_report,
        ConnectionError: rollback_and_report,
        DatabaseError: "log",
    }
)
@spec
def create_user(username: str, email: str) -> dict[str, str]:
    """Create a new user in the database."""
    db.insert(username, email)
    db.commit()
    return {"status": "ok", "username": username, "email": email}


if __name__ == "__main__":
    # Successful creation
    result = create_user("alice", "alice@example.com")
    print(f"First insert:  {result}")

    # Reset DB for next demo
    db = Database()

    # Duplicate key — triggers rollback
    db.insert("alice", "alice@example.com")
    result = create_user("alice", "alice-new@example.com")
    print(f"Duplicate key: {result}")
    print(f"  Rolled back: {db.rolled_back}")
