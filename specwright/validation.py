"""Runtime type validation for specwright specifications."""

from __future__ import annotations

import inspect
from typing import Any, get_type_hints

from pydantic import TypeAdapter, ValidationError as PydanticValidationError

from .exceptions import (
    InputValidationError,
    MissingDocstringError,
    MissingTypeHintError,
    OutputValidationError,
)

_SKIP_PARAMS = frozenset({"self", "cls"})


def validate_docstring(func: Any) -> None:
    """Validate that a function has a non-empty docstring.

    Raises:
        MissingDocstringError: If the function has no docstring or only whitespace.
    """
    if not func.__doc__ or not func.__doc__.strip():
        raise MissingDocstringError(
            f"Function '{func.__qualname__}' is missing a docstring. "
            f"All @spec-decorated functions must have a docstring "
            f"describing their behavior."
        )


def validate_type_hints(func: Any) -> dict[str, Any]:
    """Validate that a function has complete type annotations.

    Returns:
        The resolved type hints dictionary.

    Raises:
        MissingTypeHintError: If any parameters or the return type lack annotations.
    """
    hints = get_type_hints(func)
    sig = inspect.signature(func)

    missing: list[str] = []
    for name, param in sig.parameters.items():
        if name in _SKIP_PARAMS:
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if name not in hints:
            missing.append(name)

    if "return" not in hints:
        missing.append("return")

    if missing:
        raise MissingTypeHintError(
            f"Function '{func.__qualname__}' is missing type hints for: "
            f"{', '.join(missing)}. "
            f"All @spec-decorated functions must have complete type annotations."
        )

    return hints


def validate_inputs(
    func: Any, hints: dict[str, Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> None:
    """Validate function arguments against their declared type hints.

    Raises:
        InputValidationError: If any argument doesn't match its type hint.
    """
    sig = inspect.signature(func)
    try:
        bound = sig.bind(*args, **kwargs)
    except TypeError as e:
        raise InputValidationError(
            f"Argument binding failed for '{func.__qualname__}': {e}"
        ) from e
    bound.apply_defaults()

    errors: list[str] = []
    for name, value in bound.arguments.items():
        if name in _SKIP_PARAMS:
            continue
        if name not in hints:
            continue
        try:
            adapter = TypeAdapter(hints[name])
            adapter.validate_python(value, strict=True)
        except PydanticValidationError:
            errors.append(
                f"  - Parameter '{name}': expected {hints[name]}, "
                f"got {type(value).__name__} ({value!r})"
            )

    if errors:
        raise InputValidationError(
            f"Input validation failed for '{func.__qualname__}':\n"
            + "\n".join(errors)
        )


def validate_output(func: Any, hints: dict[str, Any], result: Any) -> None:
    """Validate a function's return value against its declared return type.

    Raises:
        OutputValidationError: If the return value doesn't match the return type hint.
    """
    if "return" not in hints:
        return

    return_type = hints["return"]
    try:
        adapter = TypeAdapter(return_type)
        adapter.validate_python(result, strict=True)
    except PydanticValidationError:
        raise OutputValidationError(
            f"Output validation failed for '{func.__qualname__}': "
            f"expected {return_type}, got {type(result).__name__} ({result!r})"
        )
