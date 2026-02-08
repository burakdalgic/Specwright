"""Tests for specwright validation functions."""

import pytest

from specwright.exceptions import (
    InputValidationError,
    MissingDocstringError,
    MissingTypeHintError,
    OutputValidationError,
)
from specwright.validation import (
    validate_docstring,
    validate_inputs,
    validate_output,
    validate_type_hints,
)


# --- validate_docstring ---


class TestValidateDocstring:
    def test_valid_docstring(self) -> None:
        def func() -> None:
            """Has a docstring."""

        validate_docstring(func)  # should not raise

    def test_missing_docstring(self) -> None:
        def func() -> None:
            pass

        with pytest.raises(MissingDocstringError, match="missing a docstring"):
            validate_docstring(func)

    def test_whitespace_only_docstring(self) -> None:
        def func() -> None:
            """ """

        with pytest.raises(MissingDocstringError, match="missing a docstring"):
            validate_docstring(func)


# --- validate_type_hints ---


class TestValidateTypeHints:
    def test_complete_hints(self) -> None:
        def func(x: int, y: str) -> bool: ...

        hints = validate_type_hints(func)
        assert hints["x"] is int
        assert hints["y"] is str
        assert hints["return"] is bool

    def test_missing_param_hint(self) -> None:
        def func(x: int, y) -> bool:  # type: ignore[no-untyped-def]
            ...

        with pytest.raises(MissingTypeHintError, match="y"):
            validate_type_hints(func)

    def test_missing_return_hint(self) -> None:
        def func(x: int):  # type: ignore[no-untyped-def]
            ...

        with pytest.raises(MissingTypeHintError, match="return"):
            validate_type_hints(func)

    def test_missing_multiple_hints(self) -> None:
        def func(x, y):  # type: ignore[no-untyped-def]
            ...

        with pytest.raises(MissingTypeHintError, match="x.*y.*return"):
            validate_type_hints(func)

    def test_skips_self_and_cls(self) -> None:
        # Simulate a method signature with 'self'
        def func(self, x: int) -> None: ...

        hints = validate_type_hints(func)
        assert "self" not in hints

    def test_skips_var_positional_and_keyword(self) -> None:
        def func(x: int, *args: int, **kwargs: str) -> None: ...

        hints = validate_type_hints(func)
        assert "x" in hints

    def test_var_args_without_annotation_ok(self) -> None:
        def func(x: int, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            ...

        # Should not raise — *args and **kwargs are skipped
        validate_type_hints(func)

    def test_no_params_just_return(self) -> None:
        def func() -> int: ...

        hints = validate_type_hints(func)
        assert hints["return"] is int


# --- validate_inputs ---


class TestValidateInputs:
    def test_valid_inputs(self) -> None:
        def func(x: int, y: str) -> None: ...

        hints = {"x": int, "y": str, "return": type(None)}
        validate_inputs(func, hints, (42, "hello"), {})

    def test_invalid_input_type(self) -> None:
        def func(x: int, y: str) -> None: ...

        hints = {"x": int, "y": str, "return": type(None)}
        with pytest.raises(InputValidationError, match="Parameter 'x'"):
            validate_inputs(func, hints, ("not_an_int", "hello"), {})

    def test_multiple_invalid_inputs(self) -> None:
        def func(x: int, y: str) -> None: ...

        hints = {"x": int, "y": str, "return": type(None)}
        with pytest.raises(
            InputValidationError, match=r"(?s)Parameter 'x'.*Parameter 'y'"
        ):
            validate_inputs(func, hints, ("bad", 123), {})

    def test_kwargs_validation(self) -> None:
        def func(x: int, y: str) -> None: ...

        hints = {"x": int, "y": str, "return": type(None)}
        validate_inputs(func, hints, (), {"x": 42, "y": "hello"})

    def test_invalid_kwargs(self) -> None:
        def func(x: int) -> None: ...

        hints = {"x": int, "return": type(None)}
        with pytest.raises(InputValidationError, match="Parameter 'x'"):
            validate_inputs(func, hints, (), {"x": "not_int"})

    def test_wrong_number_of_args(self) -> None:
        def func(x: int) -> None: ...

        hints = {"x": int, "return": type(None)}
        with pytest.raises(InputValidationError, match="Argument binding failed"):
            validate_inputs(func, hints, (1, 2, 3), {})

    def test_default_values(self) -> None:
        def func(x: int, y: str = "default") -> None: ...

        hints = {"x": int, "y": str, "return": type(None)}
        validate_inputs(func, hints, (42,), {})

    def test_skips_self(self) -> None:
        def func(self, x: int) -> None:  # type: ignore[no-untyped-def]
            ...

        hints = {"x": int, "return": type(None)}
        validate_inputs(func, hints, ("self_obj", 42), {})

    def test_param_not_in_hints_skipped(self) -> None:
        def func(x: int, y: str) -> None: ...

        # Only provide hint for 'x', not 'y' — 'y' should be skipped
        hints = {"x": int, "return": type(None)}
        validate_inputs(func, hints, (42, "anything"), {})

    def test_bool_rejected_for_int(self) -> None:
        def func(x: int) -> None: ...

        hints = {"x": int, "return": type(None)}
        with pytest.raises(InputValidationError, match="Parameter 'x'"):
            validate_inputs(func, hints, (True,), {})


# --- validate_output ---


class TestValidateOutput:
    def test_valid_output(self) -> None:
        def func() -> int: ...

        hints = {"return": int}
        validate_output(func, hints, 42)

    def test_invalid_output(self) -> None:
        def func() -> int: ...

        hints = {"return": int}
        with pytest.raises(OutputValidationError, match="expected.*int"):
            validate_output(func, hints, "not_an_int")

    def test_none_return_type(self) -> None:
        def func() -> None: ...

        hints = {"return": type(None)}
        validate_output(func, hints, None)

    def test_none_return_type_violation(self) -> None:
        def func() -> None: ...

        hints = {"return": type(None)}
        with pytest.raises(OutputValidationError):
            validate_output(func, hints, 42)

    def test_no_return_hint_skips_validation(self) -> None:
        def func():  # type: ignore[no-untyped-def]
            ...

        validate_output(func, {}, "anything")
