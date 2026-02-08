"""Example: Using @spec with basic Python types.

This demonstrates the simplest use case — a function with primitive
type annotations validated at runtime by specwright.
"""

from specwright import spec


@spec
def add(x: int, y: int) -> int:
    """Add two integers and return the result."""
    return x + y


@spec
def greet(name: str, excited: bool) -> str:
    """Build a greeting string for the given name."""
    suffix = "!" if excited else "."
    return f"Hello, {name}{suffix}"


@spec
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


if __name__ == "__main__":
    # Happy-path usage
    print(add(2, 3))  # 5
    print(greet("Alice", True))  # Hello, Alice!
    print(divide(10, 3))  # 3.333...

    # Inspect stored spec metadata
    meta = add.__spec__
    print(f"\nSpec metadata for '{meta.name}':")
    print(f"  Parameters: {meta.parameters}")
    print(f"  Return type: {meta.return_type}")
    print(f"  Docstring: {meta.docstring}")
