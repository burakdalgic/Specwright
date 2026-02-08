"""Example: What happens when required tests are missing (warn mode).

Run with::

    pytest examples/warn_mode_demo.py -p specwright.pytest_plugin \\
        -o specwright_test_enforcement=warn -W all

The plugin will warn about missing test functions but still let
the session proceed.
"""

from specwright import requires_tests


@requires_tests(
    happy_path=True,
    edge_cases=["empty_email", "long_email"],
    error_cases=["invalid_format", "duplicate_email"],
)
def register_user(email: str) -> dict:
    """Register a new user with the given email."""
    return {"email": email, "registered": True}


# Only a happy-path test exists — edge/error cases are missing.
def test_register_user_happy_path() -> None:
    result = register_user("alice@example.com")
    assert result == {"email": "alice@example.com", "registered": True}


if __name__ == "__main__":
    reqs = register_user.__test_requirements__
    print("Required test functions:")
    for name in reqs.expected_test_names:
        print(f"  {name}")

    print("\nOnly 'test_register_user_happy_path' exists.")
    print("In 'warn' mode the plugin would emit a warning for the rest.")
    print("In 'strict' mode the session would fail.")
