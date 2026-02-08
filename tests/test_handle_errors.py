"""Tests for the @handle_errors decorator."""

import logging

import pytest

from specwright import (
    HandlingStrategyError,
    InputValidationError,
    OutputValidationError,
    ValidationError,
    handle_errors,
    spec,
)


# --- Strategy: "ignore" ---


class TestIgnoreStrategy:
    def test_suppresses_exception(self) -> None:
        @handle_errors({ValueError: "ignore"})
        def fail() -> None:
            raise ValueError("boom")

        assert fail() is None

    def test_only_catches_specified_type(self) -> None:
        @handle_errors({ValueError: "ignore"})
        def fail() -> None:
            raise TypeError("boom")

        with pytest.raises(TypeError, match="boom"):
            fail()

    def test_no_exception_passes_through(self) -> None:
        @handle_errors({ValueError: "ignore"})
        def ok() -> int:
            return 42

        assert ok() == 42


# --- Strategy: "log" ---


class TestLogStrategy:
    def test_logs_and_reraises(self, caplog: pytest.LogCaptureFixture) -> None:
        @handle_errors({ValueError: "log"})
        def fail() -> None:
            raise ValueError("something broke")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match="something broke"):
                fail()

        assert "Error in" in caplog.text
        assert "something broke" in caplog.text

    def test_preserves_traceback_in_log(self, caplog: pytest.LogCaptureFixture) -> None:
        @handle_errors({RuntimeError: "log"})
        def fail() -> None:
            raise RuntimeError("trace me")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError):
                fail()

        assert "Traceback" in caplog.text
        assert "trace me" in caplog.text

    def test_log_includes_function_name(self, caplog: pytest.LogCaptureFixture) -> None:
        @handle_errors({ValueError: "log"})
        def my_named_func() -> None:
            raise ValueError("err")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                my_named_func()

        assert "my_named_func" in caplog.text


# --- Strategy: callable ---


class TestCallableStrategy:
    def test_lambda_handler(self) -> None:
        @handle_errors({ValueError: lambda e: f"caught: {e}"})
        def fail() -> str:
            raise ValueError("bad input")

        assert fail() == "caught: bad input"

    def test_function_handler(self) -> None:
        def on_key_error(exc: BaseException) -> str:
            return f"missing key: {exc}"

        @handle_errors({KeyError: on_key_error})
        def lookup(d: dict, k: str) -> str:
            return d[k]

        assert lookup({}, "x") == "missing key: 'x'"

    def test_handler_receives_exception_instance(self) -> None:
        received: list[BaseException] = []

        def capture(exc: BaseException) -> None:
            received.append(exc)

        @handle_errors({ValueError: capture})
        def fail() -> None:
            raise ValueError("catch me")

        fail()
        assert len(received) == 1
        assert isinstance(received[0], ValueError)
        assert str(received[0]) == "catch me"

    def test_handler_can_return_none(self) -> None:
        @handle_errors({ValueError: lambda e: None})
        def fail() -> None:
            raise ValueError("nope")

        assert fail() is None

    def test_handler_exception_propagates(self) -> None:
        def bad_handler(exc: BaseException) -> None:
            raise RuntimeError("handler failed")

        @handle_errors({ValueError: bad_handler})
        def fail() -> None:
            raise ValueError("original")

        with pytest.raises(RuntimeError, match="handler failed"):
            fail()


# --- Strategy: return value ---


class TestReturnValueStrategy:
    def test_returns_integer(self) -> None:
        @handle_errors({ValueError: -1})
        def parse(s: str) -> int:
            return int(s)

        assert parse("abc") == -1

    def test_returns_error_object(self) -> None:
        sentinel = ValidationError("bad data")

        @handle_errors({ValueError: sentinel})
        def fail() -> ValidationError:
            raise ValueError("oops")

        result = fail()
        assert result is sentinel

    def test_returns_dict(self) -> None:
        fallback = {"error": True, "message": "failed"}

        @handle_errors({KeyError: fallback})
        def fail() -> dict:
            raise KeyError("x")

        assert fail() == fallback

    def test_returns_none_value(self) -> None:
        @handle_errors({ValueError: None})
        def fail() -> None:
            raise ValueError("oops")

        assert fail() is None


# --- Handler matching ---


class TestHandlerMatching:
    def test_first_matching_handler_wins(self) -> None:
        @handle_errors(
            {
                ValueError: "first",
                Exception: "second",
            }
        )
        def fail() -> str:
            raise ValueError("test")

        assert fail() == "first"

    def test_subclass_matched_by_parent(self) -> None:
        @handle_errors({Exception: "caught"})
        def fail() -> str:
            raise ValueError("subclass")

        assert fail() == "caught"

    def test_unhandled_exception_propagates(self) -> None:
        @handle_errors({ValueError: "ignore"})
        def fail() -> None:
            raise TypeError("not handled")

        with pytest.raises(TypeError, match="not handled"):
            fail()

    def test_multiple_handlers(self) -> None:
        @handle_errors(
            {
                ValueError: "val_error",
                KeyError: "key_error",
                TypeError: "type_error",
            }
        )
        def fail(exc_type: type) -> str:
            raise exc_type("boom")

        assert fail(ValueError) == "val_error"
        assert fail(KeyError) == "key_error"
        assert fail(TypeError) == "type_error"


# --- Validation of handler config ---


class TestHandlerValidation:
    def test_non_exception_key_rejected(self) -> None:
        with pytest.raises(HandlingStrategyError, match="exception type"):
            handle_errors({"not_a_type": "ignore"})  # type: ignore[dict-item]

    def test_non_exception_class_key_rejected(self) -> None:
        with pytest.raises(HandlingStrategyError, match="exception type"):
            handle_errors({int: "ignore"})  # type: ignore[dict-item]

    def test_arbitrary_string_is_valid_return_value(self) -> None:
        @handle_errors({ValueError: "fallback_value"})
        def fail() -> str:
            raise ValueError("boom")

        assert fail() == "fallback_value"


# --- Preserves function metadata ---


class TestPreservesMetadata:
    def test_preserves_name(self) -> None:
        @handle_errors({ValueError: "ignore"})
        def my_func() -> None:
            raise ValueError

        assert my_func.__name__ == "my_func"

    def test_preserves_docstring(self) -> None:
        @handle_errors({ValueError: "ignore"})
        def my_func() -> None:
            """My docstring."""
            raise ValueError

        assert my_func.__doc__ == "My docstring."

    def test_preserves_module(self) -> None:
        @handle_errors({ValueError: "ignore"})
        def my_func() -> None:
            raise ValueError

        assert my_func.__module__ == __name__


# --- Combination with @spec ---


class TestCombinationWithSpec:
    def test_handle_errors_outside_spec(self) -> None:
        """@handle_errors catches exceptions that escape @spec."""

        @handle_errors({ValueError: "caught"})
        @spec
        def risky(x: int) -> str:
            """Do something risky."""
            raise ValueError("boom")

        assert risky(1) == "caught"

    def test_spec_validates_before_handle_errors(self) -> None:
        """@spec input validation fires before the function body runs."""

        @handle_errors({ValueError: "caught"})
        @spec
        def risky(x: int) -> str:
            """Do something risky."""
            raise ValueError("boom")

        # InputValidationError is NOT in the handlers, so it propagates
        with pytest.raises(InputValidationError):
            risky("bad")  # type: ignore[arg-type]

    def test_handle_errors_inside_spec(self) -> None:
        """@spec validates the return value produced by @handle_errors."""

        @spec
        @handle_errors({ValueError: 0})
        def risky(x: int) -> int:
            """Return an int or fall back to 0."""
            raise ValueError("boom")

        # handle_errors returns 0, spec validates 0 is int — passes
        assert risky(1) == 0

    def test_handle_errors_inside_spec_output_mismatch(self) -> None:
        """@spec catches type mismatch from handle_errors fallback value."""

        @spec
        @handle_errors({ValueError: "not_an_int"})
        def risky(x: int) -> int:
            """Return an int."""
            raise ValueError("boom")

        with pytest.raises(OutputValidationError):
            risky(1)

    def test_handle_errors_catches_input_validation(self) -> None:
        """@handle_errors can catch spec validation errors if configured."""

        @handle_errors({InputValidationError: "invalid input"})
        @spec
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        assert add("bad", 2) == "invalid input"  # type: ignore[arg-type]
