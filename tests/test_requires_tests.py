"""Tests for the @requires_tests decorator and pytest plugin."""

from __future__ import annotations

import warnings
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from specwright import (
    InvalidTestNameError,
    MissingTestsError,
    TestRequirements,
    requires_tests,
    spec,
)
from specwright.pytest_plugin import pytest_collection_modifyitems
from specwright.testing import _registry, get_registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_registry() -> None:  # type: ignore[misc]
    """Clear the global registry before each test."""
    _registry.clear()


def _decorate(
    *,
    happy_path: bool = True,
    edge_cases: list[str] | None = None,
    error_cases: list[str] | None = None,
):  # type: ignore[no-untyped-def]
    """Apply @requires_tests to a dummy function and return it."""

    @requires_tests(
        happy_path=happy_path,
        edge_cases=edge_cases,
        error_cases=error_cases,
    )
    def dummy(x: int) -> int:
        return x

    return dummy


def _make_pytest_function(name: str) -> pytest.Function:
    """Create a mock pytest.Function item with the given name."""
    item = MagicMock(spec=pytest.Function)
    item.name = name
    return item


def _make_config(enforcement: str = "strict") -> MagicMock:
    """Create a mock pytest.Config that returns the given enforcement level."""
    config = MagicMock()
    config.getini.return_value = enforcement
    return config


# ---------------------------------------------------------------------------
# TestRequirements dataclass
# ---------------------------------------------------------------------------


class TestTestRequirements:
    def test_expected_test_names_happy_path_only(self) -> None:
        fn = _decorate()
        reqs: TestRequirements = fn.__test_requirements__
        assert reqs.expected_test_names == ["test_dummy_happy_path"]

    def test_expected_test_names_with_edge_cases(self) -> None:
        fn = _decorate(edge_cases=["empty", "overflow"])
        reqs: TestRequirements = fn.__test_requirements__
        assert reqs.expected_test_names == [
            "test_dummy_happy_path",
            "test_dummy_empty",
            "test_dummy_overflow",
        ]

    def test_expected_test_names_with_error_cases(self) -> None:
        fn = _decorate(error_cases=["bad_input", "timeout"])
        reqs: TestRequirements = fn.__test_requirements__
        assert reqs.expected_test_names == [
            "test_dummy_happy_path",
            "test_dummy_bad_input",
            "test_dummy_timeout",
        ]

    def test_expected_test_names_no_happy_path(self) -> None:
        fn = _decorate(happy_path=False, edge_cases=["zero"])
        reqs: TestRequirements = fn.__test_requirements__
        assert reqs.expected_test_names == ["test_dummy_zero"]

    def test_expected_test_names_full(self) -> None:
        fn = _decorate(
            edge_cases=["empty"],
            error_cases=["invalid"],
        )
        reqs: TestRequirements = fn.__test_requirements__
        assert reqs.expected_test_names == [
            "test_dummy_happy_path",
            "test_dummy_empty",
            "test_dummy_invalid",
        ]

    def test_frozen(self) -> None:
        fn = _decorate()
        reqs: TestRequirements = fn.__test_requirements__
        with pytest.raises(AttributeError):
            reqs.happy_path = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# @requires_tests metadata storage
# ---------------------------------------------------------------------------


class TestMetadataStorage:
    def test_metadata_attached_to_function(self) -> None:
        fn = _decorate()
        assert hasattr(fn, "__test_requirements__")
        assert isinstance(fn.__test_requirements__, TestRequirements)

    def test_metadata_captures_function_name(self) -> None:
        fn = _decorate()
        assert fn.__test_requirements__.function_name == "dummy"

    def test_metadata_captures_module(self) -> None:
        fn = _decorate()
        assert fn.__test_requirements__.module is not None

    def test_metadata_defaults(self) -> None:
        fn = _decorate()
        reqs = fn.__test_requirements__
        assert reqs.happy_path is True
        assert reqs.edge_cases == ()
        assert reqs.error_cases == ()

    def test_metadata_custom_values(self) -> None:
        fn = _decorate(
            happy_path=False,
            edge_cases=["a", "b"],
            error_cases=["c"],
        )
        reqs = fn.__test_requirements__
        assert reqs.happy_path is False
        assert reqs.edge_cases == ("a", "b")
        assert reqs.error_cases == ("c",)


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_decorated_function_registered(self) -> None:
        _decorate()
        assert len(get_registry()) == 1

    def test_multiple_registrations(self) -> None:
        _decorate()
        _decorate()
        assert len(get_registry()) == 2

    def test_registry_returns_copy(self) -> None:
        _decorate()
        copy = get_registry()
        copy.clear()
        assert len(get_registry()) == 1


# ---------------------------------------------------------------------------
# Function wrapping
# ---------------------------------------------------------------------------


class TestFunctionWrapping:
    def test_preserves_function_name(self) -> None:
        fn = _decorate()
        assert fn.__name__ == "dummy"

    def test_preserves_return_value(self) -> None:
        fn = _decorate()
        assert fn(42) == 42

    def test_preserves_arguments(self) -> None:
        @requires_tests(happy_path=True)
        def add(a: int, b: int) -> int:
            return a + b

        assert add(1, 2) == 3


# ---------------------------------------------------------------------------
# Combination with @spec
# ---------------------------------------------------------------------------


class TestCombinationWithSpec:
    def test_requires_tests_outside_spec(self) -> None:
        @requires_tests(happy_path=True)
        @spec
        def greet(name: str) -> str:
            """Say hello."""
            return f"hi {name}"

        assert greet("world") == "hi world"
        assert hasattr(greet, "__test_requirements__")
        assert hasattr(greet, "__spec__")

    def test_spec_outside_requires_tests(self) -> None:
        @spec
        @requires_tests(happy_path=True)
        def greet(name: str) -> str:
            """Say hello."""
            return f"hi {name}"

        assert greet("world") == "hi world"
        assert hasattr(greet, "__spec__")


# ---------------------------------------------------------------------------
# Pytest plugin — strict mode (unit tests)
# ---------------------------------------------------------------------------


class TestPluginStrictMode:
    def test_missing_tests_raises_in_strict(self) -> None:
        _decorate(edge_cases=["empty"])  # registers: test_dummy_happy_path, test_dummy_empty
        items = [_make_pytest_function("test_dummy_happy_path")]
        config = _make_config("strict")
        session = MagicMock()

        with pytest.raises(MissingTestsError, match="test_dummy_empty"):
            pytest_collection_modifyitems(session=session, config=config, items=items)

    def test_all_tests_present_passes_strict(self) -> None:
        _decorate(edge_cases=["empty"])
        items = [
            _make_pytest_function("test_dummy_happy_path"),
            _make_pytest_function("test_dummy_empty"),
        ]
        config = _make_config("strict")
        session = MagicMock()

        # Should not raise
        pytest_collection_modifyitems(session=session, config=config, items=items)

    def test_report_includes_function_name(self) -> None:
        _decorate()
        items: list[pytest.Item] = []  # no tests at all
        config = _make_config("strict")
        session = MagicMock()

        with pytest.raises(MissingTestsError, match="dummy"):
            pytest_collection_modifyitems(session=session, config=config, items=items)


# ---------------------------------------------------------------------------
# Pytest plugin — warn mode
# ---------------------------------------------------------------------------


class TestPluginWarnMode:
    def test_missing_tests_warns(self) -> None:
        _decorate()
        items: list[pytest.Item] = []
        config = _make_config("warn")
        session = MagicMock()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            pytest_collection_modifyitems(session=session, config=config, items=items)

        assert len(w) == 1
        assert "Missing required tests" in str(w[0].message)

    def test_warn_mode_does_not_raise(self) -> None:
        _decorate()
        items: list[pytest.Item] = []
        config = _make_config("warn")
        session = MagicMock()

        # Should NOT raise — just warns
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            pytest_collection_modifyitems(session=session, config=config, items=items)


# ---------------------------------------------------------------------------
# Pytest plugin — off mode
# ---------------------------------------------------------------------------


class TestPluginOffMode:
    def test_no_enforcement_when_off(self) -> None:
        _decorate()
        items: list[pytest.Item] = []
        config = _make_config("off")
        session = MagicMock()

        # Should not raise or warn
        pytest_collection_modifyitems(session=session, config=config, items=items)


# ---------------------------------------------------------------------------
# Pytest plugin — empty registry
# ---------------------------------------------------------------------------


class TestPluginEmptyRegistry:
    def test_no_registered_functions(self) -> None:
        items = [_make_pytest_function("test_something")]
        config = _make_config("strict")
        session = MagicMock()

        # No @requires_tests functions — nothing to check
        pytest_collection_modifyitems(session=session, config=config, items=items)


# ---------------------------------------------------------------------------
# Naming convention
# ---------------------------------------------------------------------------


class TestNamingConvention:
    def test_expected_names_follow_convention(self) -> None:
        fn = _decorate(
            edge_cases=["empty_input", "null_values"],
            error_cases=["invalid_email"],
        )
        reqs = fn.__test_requirements__
        names = reqs.expected_test_names
        for name in names:
            assert name.startswith("test_dummy_")

    def test_names_deterministic(self) -> None:
        fn = _decorate(edge_cases=["a", "b"], error_cases=["c"])
        reqs = fn.__test_requirements__
        assert reqs.expected_test_names == reqs.expected_test_names
