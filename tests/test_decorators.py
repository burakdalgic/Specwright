"""Tests for the @spec decorator and SpecMetadata."""

import pytest

from specwright import (
    InputValidationError,
    MissingDocstringError,
    MissingTypeHintError,
    OutputValidationError,
    SpecMetadata,
    spec,
)


# --- Basic usage ---


class TestSpecBasicUsage:
    def test_bare_decorator(self) -> None:
        @spec
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        assert add(1, 2) == 3

    def test_decorator_with_parens(self) -> None:
        @spec()
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        assert add(1, 2) == 3

    def test_preserves_function_name(self) -> None:
        @spec
        def my_function(x: int) -> int:
            """Identity."""
            return x

        assert my_function.__name__ == "my_function"

    def test_preserves_docstring(self) -> None:
        @spec
        def my_function(x: int) -> int:
            """My docstring."""
            return x

        assert my_function.__doc__ == "My docstring."

    def test_preserves_module(self) -> None:
        @spec
        def my_function(x: int) -> int:
            """Identity."""
            return x

        assert my_function.__module__ == __name__


# --- SpecMetadata ---


class TestSpecMetadata:
    def test_metadata_attached(self) -> None:
        @spec
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        assert hasattr(add, "__spec__")
        assert isinstance(add.__spec__, SpecMetadata)

    def test_metadata_fields(self) -> None:
        @spec
        def greet(name: str, excited: bool) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        meta = greet.__spec__
        assert meta.name == "greet"
        assert "greet" in meta.qualname
        assert meta.docstring == "Greet someone."
        assert meta.parameters == {"name": str, "excited": bool}
        assert meta.return_type is str

    def test_metadata_is_frozen(self) -> None:
        @spec
        def func(x: int) -> int:
            """Identity."""
            return x

        with pytest.raises(AttributeError):
            func.__spec__.name = "changed"  # type: ignore[misc]


# --- Decoration-time validation ---


class TestDecorationTimeChecks:
    def test_missing_docstring_at_decoration(self) -> None:
        with pytest.raises(MissingDocstringError, match="missing a docstring"):

            @spec
            def func(x: int) -> int:
                return x

    def test_missing_type_hints_at_decoration(self) -> None:
        with pytest.raises(MissingTypeHintError, match="missing type hints"):

            @spec
            def func(x) -> int:  # type: ignore[no-untyped-def]
                """Has docstring."""
                return x

    def test_missing_return_type_at_decoration(self) -> None:
        with pytest.raises(MissingTypeHintError, match="return"):

            @spec
            def func(x: int):  # type: ignore[no-untyped-def]
                """Has docstring."""
                return x

    def test_require_docstring_false(self) -> None:
        @spec(require_docstring=False)
        def func(x: int) -> int:
            return x

        assert func(1) == 1


# --- Runtime input validation ---


class TestInputValidation:
    def test_valid_inputs(self) -> None:
        @spec
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        assert add(1, 2) == 3

    def test_invalid_input_raises(self) -> None:
        @spec
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        with pytest.raises(InputValidationError, match="Parameter 'x'"):
            add("bad", 2)  # type: ignore[arg-type]

    def test_invalid_kwarg_raises(self) -> None:
        @spec
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        with pytest.raises(InputValidationError, match="Parameter 'y'"):
            add(1, y="bad")  # type: ignore[arg-type]

    def test_validate_inputs_false(self) -> None:
        @spec(validate_inputs=False, validate_output=False)
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        # Should not raise even with wrong types
        result = add("1", "2")  # type: ignore[arg-type]
        assert result == "12"  # string concatenation

    def test_bool_rejected_for_int(self) -> None:
        @spec
        def double(x: int) -> int:
            """Double it."""
            return x * 2

        with pytest.raises(InputValidationError, match="Parameter 'x'"):
            double(True)  # type: ignore[arg-type]

    def test_default_values_work(self) -> None:
        @spec
        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone."""
            return f"{greeting}, {name}!"

        assert greet("World") == "Hello, World!"
        assert greet("World", "Hi") == "Hi, World!"


# --- Runtime output validation ---


class TestOutputValidation:
    def test_valid_output(self) -> None:
        @spec
        def to_str(x: int) -> str:
            """Convert to string."""
            return str(x)

        assert to_str(42) == "42"

    def test_invalid_output_raises(self) -> None:
        @spec
        def bad_func(x: int) -> str:
            """Should return str but returns int."""
            return x  # type: ignore[return-value]

        with pytest.raises(OutputValidationError, match="expected.*str"):
            bad_func(42)

    def test_none_return(self) -> None:
        @spec
        def side_effect(x: int) -> None:
            """Do something with no return value."""
            _ = x

        assert side_effect(1) is None

    def test_validate_output_false(self) -> None:
        @spec(validate_output=False)
        def bad_func(x: int) -> str:
            """Should return str but returns int."""
            return x  # type: ignore[return-value]

        # Should not raise even with wrong return type
        assert bad_func(42) == 42


# --- Complex types ---


class TestComplexTypes:
    def test_list_of_ints(self) -> None:
        @spec
        def sum_list(numbers: list[int]) -> int:
            """Sum a list of ints."""
            return sum(numbers)

        assert sum_list([1, 2, 3]) == 6

    def test_list_of_wrong_type(self) -> None:
        @spec
        def sum_list(numbers: list[int]) -> int:
            """Sum a list of ints."""
            return sum(numbers)

        with pytest.raises(InputValidationError, match="Parameter 'numbers'"):
            sum_list(["a", "b"])  # type: ignore[list-item]

    def test_dict_type(self) -> None:
        @spec
        def get_value(data: dict[str, int], key: str) -> int:
            """Get a value from a dict."""
            return data[key]

        assert get_value({"a": 1}, "a") == 1

    def test_optional_type(self) -> None:
        @spec
        def maybe(x: int | None) -> int:
            """Return x or 0."""
            return x if x is not None else 0

        assert maybe(42) == 42
        assert maybe(None) == 0

    def test_list_return_type(self) -> None:
        @spec
        def make_list(n: int) -> list[int]:
            """Make a list of ints."""
            return list(range(n))

        assert make_list(3) == [0, 1, 2]

    def test_invalid_list_return(self) -> None:
        @spec
        def make_list(n: int) -> list[int]:
            """Make a list of ints."""
            return list(range(n)) + ["oops"]  # type: ignore[list-item]

        with pytest.raises(OutputValidationError):
            make_list(2)


# --- Edge cases ---


class TestEdgeCases:
    def test_no_args_function(self) -> None:
        @spec
        def get_answer() -> int:
            """Return the answer."""
            return 42

        assert get_answer() == 42

    def test_kwargs_only(self) -> None:
        @spec
        def func(*, x: int, y: int) -> int:
            """Add keyword-only args."""
            return x + y

        assert func(x=1, y=2) == 3

    def test_mixed_args_and_kwargs(self) -> None:
        @spec
        def func(x: int, *, y: int) -> int:
            """Mix positional and keyword-only args."""
            return x + y

        assert func(1, y=2) == 3

    def test_float_accepts_int(self) -> None:
        @spec
        def half(x: float) -> float:
            """Halve it."""
            return x / 2

        # int should be accepted for float annotations
        assert half(4) == 2.0
