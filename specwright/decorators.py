"""The @spec and @handle_errors decorators for enforcing function specifications."""

from __future__ import annotations

import functools
import inspect
import logging
from dataclasses import dataclass
from typing import Any, Callable, TypeVar, overload

from .exceptions import HandlingStrategyError
from .validation import (
    validate_docstring,
    validate_inputs as check_inputs,
    validate_output as check_output,
    validate_type_hints,
)

F = TypeVar("F", bound=Callable[..., Any])

_VALID_STRING_STRATEGIES = frozenset({"ignore", "log"})
_RAISE = object()


@dataclass(frozen=True)
class SpecMetadata:
    """Metadata extracted from a @spec-decorated function.

    Attributes:
        name: The function's simple name.
        qualname: The function's qualified name.
        module: The module where the function is defined.
        docstring: The function's docstring.
        parameters: Mapping of parameter names to their type hints.
        return_type: The function's return type hint.
    """

    name: str
    qualname: str
    module: str | None
    docstring: str
    parameters: dict[str, Any]
    return_type: Any


# ---------------------------------------------------------------------------
# @spec decorator
# ---------------------------------------------------------------------------


@overload
def spec(func: F, /) -> F: ...


@overload
def spec(
    *,
    validate_inputs: bool = ...,
    validate_output: bool = ...,
    require_docstring: bool = ...,
) -> Callable[[F], F]: ...


def spec(
    func: Any = None,
    /,
    *,
    validate_inputs: bool = True,
    validate_output: bool = True,
    require_docstring: bool = True,
) -> Any:
    """Decorator that enforces specifications on functions.

    Performs decoration-time checks (docstring presence, type hint completeness)
    and runtime checks (input/output type validation).

    Can be used with or without arguments::

        @spec
        def add(x: int, y: int) -> int:
            \"\"\"Add two integers.\"\"\"
            return x + y

        @spec(validate_output=False)
        def add(x: int, y: int) -> int:
            \"\"\"Add two integers.\"\"\"
            return x + y

    Args:
        validate_inputs: Whether to validate input types at runtime.
        validate_output: Whether to validate the return type at runtime.
        require_docstring: Whether to require a docstring.
    """

    def decorator(fn: F) -> F:
        if require_docstring:
            validate_docstring(fn)

        hints = validate_type_hints(fn)
        metadata = _build_metadata(fn, hints)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if validate_inputs:
                check_inputs(fn, hints, args, kwargs)
            result = fn(*args, **kwargs)
            if validate_output:
                check_output(fn, hints, result)
            return result

        wrapper.__spec__ = metadata  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator


def _build_metadata(
    func: Callable[..., Any], hints: dict[str, Any]
) -> SpecMetadata:
    """Build SpecMetadata from a function and its resolved type hints."""
    sig = inspect.signature(func)
    params = {name: hints[name] for name in sig.parameters if name in hints}
    return SpecMetadata(
        name=func.__name__,
        qualname=func.__qualname__,
        module=getattr(func, "__module__", None),
        docstring=func.__doc__ or "",
        parameters=params,
        return_type=hints.get("return", inspect.Parameter.empty),
    )


# ---------------------------------------------------------------------------
# @handle_errors decorator
# ---------------------------------------------------------------------------


def handle_errors(
    handlers: dict[type[BaseException], Any],
) -> Callable[[F], F]:
    """Decorator for declarative error handling.

    Maps exception types to handling strategies so that error-handling
    policy is declared alongside (or separately from) function logic.

    Strategies:
        ``"ignore"``
            Suppress the exception and return ``None``.
        ``"log"``
            Log the exception with its full traceback, then re-raise it.
        *callable*
            Call ``strategy(exception)`` and return its result.
        *any other value*
            Return that value directly.

    Example::

        @handle_errors({
            ValueError: "ignore",
            KeyError: lambda e: f"missing: {e}",
            RuntimeError: "log",
        })
        def process(data: dict) -> str:
            ...

    Args:
        handlers: Mapping of exception types to handling strategies.

    Raises:
        HandlingStrategyError: If a handler key is not an exception type or
            a string strategy is unrecognised.
    """
    _validate_handlers(handlers)
    catchable = tuple(handlers.keys())

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except catchable as e:
                for exc_type, strategy in handlers.items():
                    if isinstance(e, exc_type):
                        result = _apply_strategy(strategy, e, fn)
                        if result is _RAISE:
                            raise
                        return result
                raise  # pragma: no cover — unreachable, but safe

        return wrapper  # type: ignore[return-value]

    return decorator


def _validate_handlers(handlers: dict[type[BaseException], Any]) -> None:
    """Validate handler configuration at decoration time."""
    for exc_type in handlers:
        if not isinstance(exc_type, type) or not issubclass(exc_type, BaseException):
            raise HandlingStrategyError(
                f"Handler key must be an exception type, "
                f"got {type(exc_type).__name__}: {exc_type!r}"
            )


def _apply_strategy(
    strategy: Any,
    exception: BaseException,
    func: Callable[..., Any],
) -> Any:
    """Execute a handling strategy and return the result.

    Returns the ``_RAISE`` sentinel when the exception should be re-raised
    (used by the ``"log"`` strategy).
    """
    if strategy == "ignore":
        return None
    if strategy == "log":
        logger = logging.getLogger(func.__module__ or __name__)
        logger.exception(
            "Error in '%s': %s",
            func.__qualname__,
            exception,
        )
        return _RAISE
    if callable(strategy):
        return strategy(exception)
    return strategy
