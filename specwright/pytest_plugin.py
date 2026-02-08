"""Pytest plugin for enforcing @requires_tests coverage.

The plugin is registered automatically via the ``pytest11`` entry point
when specwright is installed.  It can also be loaded explicitly with
``pytest -p specwright.pytest_plugin``.

Configuration (``pyproject.toml``)::

    [tool.pytest.ini_options]
    specwright_test_enforcement = "strict"   # "strict" | "warn" | "off"

In **strict** mode (the default), missing tests cause the session to fail.
In **warn** mode, warnings are emitted but tests still pass.
In **off** mode, the check is skipped entirely.
"""

from __future__ import annotations

import warnings

import pytest

from .exceptions import MissingTestsError
from .testing import get_registry


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register specwright ini-file options."""
    parser.addini(
        "specwright_test_enforcement",
        help="Enforcement level: strict, warn, or off (default: strict)",
        default="strict",
    )


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """After test collection, verify required tests exist."""
    enforcement = config.getini("specwright_test_enforcement")
    if enforcement == "off":
        return

    registry = get_registry()
    if not registry:
        return

    # Build a set of all collected test function names.
    collected_names: set[str] = set()
    for item in items:
        if isinstance(item, pytest.Function):
            collected_names.add(item.name)

    # Check each registered function's requirements.
    missing_by_func: dict[str, list[str]] = {}
    for reqs in registry:
        missing = [
            name for name in reqs.expected_test_names if name not in collected_names
        ]
        if missing:
            missing_by_func[reqs.qualname] = missing

    if not missing_by_func:
        return

    # Format a human-readable report.
    lines: list[str] = ["Missing required tests:"]
    for qualname, names in sorted(missing_by_func.items()):
        lines.append(f"  {qualname}:")
        for name in names:
            lines.append(f"    - {name}")
    report = "\n".join(lines)

    if enforcement == "strict":
        raise MissingTestsError(report)
    else:
        warnings.warn(report, stacklevel=1)
