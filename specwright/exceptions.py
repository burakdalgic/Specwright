"""Custom exceptions for specwright specification violations."""


class SpecwrightError(Exception):
    """Base exception for all specwright errors."""


class SpecError(SpecwrightError):
    """Base exception for specification validation errors."""


class InputValidationError(SpecError):
    """Raised when function arguments violate the declared type specifications."""


class OutputValidationError(SpecError):
    """Raised when a function's return value violates the declared return type."""


class MissingDocstringError(SpecError):
    """Raised when a @spec-decorated function lacks a required docstring."""


class MissingTypeHintError(SpecError):
    """Raised when a @spec-decorated function has incomplete type annotations."""


class HandlingStrategyError(SpecwrightError):
    """Raised when an invalid error handling strategy is configured."""


class ValidationError(SpecwrightError):
    """General-purpose validation error for use as a return value or exception."""


class InvalidTransitionError(SpecwrightError):
    """Raised when an invalid state transition is attempted."""


class InvalidStateError(SpecwrightError):
    """Raised when a state machine references an invalid state."""


class MissingTestsError(SpecwrightError):
    """Raised when required tests are missing for a @requires_tests function."""


class InvalidTestNameError(SpecwrightError):
    """Raised when a test case name doesn't follow the naming convention."""
