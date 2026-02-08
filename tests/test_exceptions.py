"""Tests for specwright exception hierarchy."""

from specwright import (
    HandlingStrategyError,
    InputValidationError,
    InvalidStateError,
    InvalidTestNameError,
    InvalidTransitionError,
    MissingDocstringError,
    MissingTestsError,
    MissingTypeHintError,
    OutputValidationError,
    SpecError,
    SpecwrightError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_specwright_error_is_root(self) -> None:
        assert issubclass(SpecwrightError, Exception)
        assert issubclass(SpecError, SpecwrightError)
        assert issubclass(HandlingStrategyError, SpecwrightError)
        assert issubclass(ValidationError, SpecwrightError)
        assert issubclass(InvalidTransitionError, SpecwrightError)
        assert issubclass(InvalidStateError, SpecwrightError)
        assert issubclass(MissingTestsError, SpecwrightError)
        assert issubclass(InvalidTestNameError, SpecwrightError)

    def test_spec_error_subtypes(self) -> None:
        assert issubclass(InputValidationError, SpecError)
        assert issubclass(OutputValidationError, SpecError)
        assert issubclass(MissingDocstringError, SpecError)
        assert issubclass(MissingTypeHintError, SpecError)

    def test_all_inherit_from_specwright_error(self) -> None:
        for exc_class in (
            SpecError,
            InputValidationError,
            OutputValidationError,
            MissingDocstringError,
            MissingTypeHintError,
            HandlingStrategyError,
            ValidationError,
            InvalidTransitionError,
            InvalidStateError,
            MissingTestsError,
            InvalidTestNameError,
        ):
            assert issubclass(exc_class, SpecwrightError)

    def test_exceptions_carry_messages(self) -> None:
        msg = "something went wrong"
        for exc_class in (
            SpecwrightError,
            SpecError,
            InputValidationError,
            OutputValidationError,
            MissingDocstringError,
            MissingTypeHintError,
            HandlingStrategyError,
            ValidationError,
            InvalidTransitionError,
            InvalidStateError,
            MissingTestsError,
            InvalidTestNameError,
        ):
            exc = exc_class(msg)
            assert str(exc) == msg
