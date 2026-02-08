"""Example: How specwright reports specification violations.

Demonstrates the clear, actionable error messages produced when
a function violates its declared spec at decoration time or runtime.
"""

from specwright import (
    InputValidationError,
    MissingDocstringError,
    MissingTypeHintError,
    OutputValidationError,
    spec,
)


# --- 1. Missing docstring (caught at decoration time) ---

def demo_missing_docstring() -> None:
    """Show what happens when a @spec function has no docstring."""
    try:
        @spec
        def add(x: int, y: int) -> int:
            return x + y
    except MissingDocstringError as e:
        print(f"[MissingDocstringError] {e}\n")


# --- 2. Missing type hints (caught at decoration time) ---

def demo_missing_type_hints() -> None:
    """Show what happens when type hints are incomplete."""
    try:
        @spec
        def add(x, y) -> int:  # type: ignore[no-untyped-def]
            """Add two numbers."""
            return x + y
    except MissingTypeHintError as e:
        print(f"[MissingTypeHintError] {e}\n")


# --- 3. Input validation error (caught at call time) ---

def demo_input_validation() -> None:
    """Show what happens when wrong argument types are passed."""
    @spec
    def multiply(x: int, y: int) -> int:
        """Multiply two integers."""
        return x * y

    try:
        multiply("three", 4)  # type: ignore[arg-type]
    except InputValidationError as e:
        print(f"[InputValidationError] {e}\n")


# --- 4. Output validation error (caught at call time) ---

def demo_output_validation() -> None:
    """Show what happens when the return value violates the spec."""
    @spec
    def get_name(user_id: int) -> str:
        """Look up a user's name by ID."""
        return user_id  # Bug: returns int instead of str  # type: ignore[return-value]

    try:
        get_name(42)
    except OutputValidationError as e:
        print(f"[OutputValidationError] {e}\n")


if __name__ == "__main__":
    demo_missing_docstring()
    demo_missing_type_hints()
    demo_input_validation()
    demo_output_validation()
