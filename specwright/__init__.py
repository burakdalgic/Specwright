"""Specwright: A specification-first framework for LLM-assisted development."""

from .decorators import SpecMetadata, handle_errors, spec
from .exceptions import (
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
from .state_machine import StateMachine, TransitionMeta, transition
from .testing import TestRequirements, requires_tests

__version__ = "0.1.0"

__all__ = [
    "HandlingStrategyError",
    "InputValidationError",
    "InvalidStateError",
    "InvalidTestNameError",
    "InvalidTransitionError",
    "MissingDocstringError",
    "MissingTestsError",
    "MissingTypeHintError",
    "OutputValidationError",
    "SpecError",
    "SpecMetadata",
    "SpecwrightError",
    "StateMachine",
    "TestRequirements",
    "TransitionMeta",
    "ValidationError",
    "__version__",
    "handle_errors",
    "requires_tests",
    "spec",
    "transition",
]
