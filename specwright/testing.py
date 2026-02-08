"""The @requires_tests decorator for enforcing test coverage requirements."""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class TestRequirements:
    """Metadata describing the test cases required for a function.

    Attributes:
        function_name: The simple name of the decorated function.
        qualname: The qualified name of the decorated function.
        module: The module where the function is defined.
        happy_path: Whether a happy-path test is required.
        edge_cases: List of edge-case scenario names to test.
        error_cases: List of error-case scenario names to test.
    """

    __test__ = False  # prevent pytest from collecting this as a test class

    function_name: str
    qualname: str
    module: str | None
    happy_path: bool
    edge_cases: tuple[str, ...] = field(default=())
    error_cases: tuple[str, ...] = field(default=())

    @property
    def expected_test_names(self) -> list[str]:
        """Return the list of test function names that must exist."""
        names: list[str] = []
        if self.happy_path:
            names.append(f"test_{self.function_name}_happy_path")
        for case in self.edge_cases:
            names.append(f"test_{self.function_name}_{case}")
        for case in self.error_cases:
            names.append(f"test_{self.function_name}_{case}")
        return names


# Global registry of all @requires_tests-decorated functions.
_registry: list[TestRequirements] = []


def get_registry() -> list[TestRequirements]:
    """Return a copy of the global test-requirements registry."""
    return list(_registry)


def requires_tests(
    *,
    happy_path: bool = True,
    edge_cases: list[str] | None = None,
    error_cases: list[str] | None = None,
) -> Callable[[F], F]:
    """Decorator that specifies required test scenarios for a function.

    The decorated function carries a ``__test_requirements__`` attribute
    with a :class:`TestRequirements` instance.  The companion pytest
    plugin (``specwright.pytest_plugin``) uses this metadata to verify
    that matching test functions exist.

    Test naming convention::

        test_{function_name}_happy_path   (when happy_path=True)
        test_{function_name}_{case_name}  (for each edge/error case)

    Args:
        happy_path: Whether a happy-path test is required (default ``True``).
        edge_cases: Names of edge-case scenarios to test.
        error_cases: Names of error-case scenarios to test.

    Example::

        @requires_tests(
            happy_path=True,
            edge_cases=["empty_input", "max_boundaries"],
            error_cases=["invalid_email", "negative_age"],
        )
        def create_user(email: str, age: int):
            ...
    """

    def decorator(func: F) -> F:
        reqs = TestRequirements(
            function_name=func.__name__,
            qualname=func.__qualname__,
            module=getattr(func, "__module__", None),
            happy_path=happy_path,
            edge_cases=tuple(edge_cases or []),
            error_cases=tuple(error_cases or []),
        )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        wrapper.__test_requirements__ = reqs  # type: ignore[attr-defined]
        _registry.append(reqs)
        return wrapper  # type: ignore[return-value]

    return decorator
