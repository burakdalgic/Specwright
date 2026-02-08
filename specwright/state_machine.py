"""State machine base class for managing state transitions with validation."""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from .exceptions import InvalidStateError, InvalidTransitionError

F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class TransitionMeta:
    """Metadata stored on a @transition-decorated method."""

    from_states: frozenset[str]
    to_state: str


def transition(
    *, from_state: str | list[str], to_state: str
) -> Callable[[F], F]:
    """Decorator that marks a method as a state transition.

    The decorated method will only execute when the instance's current
    state is one of the allowed ``from_state`` values.  On success the
    state is automatically updated to ``to_state``.

    Args:
        from_state: A single state name or list of valid source states.
        to_state: The target state after successful execution.
    """
    from_states = (
        frozenset([from_state]) if isinstance(from_state, str) else frozenset(from_state)
    )
    meta = TransitionMeta(from_states=from_states, to_state=to_state)

    def decorator(method: F) -> F:
        @functools.wraps(method)
        def wrapper(self: StateMachine, *args: Any, **kwargs: Any) -> Any:
            if self.state not in meta.from_states:
                expected = ", ".join(sorted(meta.from_states))
                raise InvalidTransitionError(
                    f"Cannot transition from '{self.state}' to "
                    f"'{meta.to_state}' via '{method.__name__}'. "
                    f"Valid source state(s): {expected}"
                )

            result = method(self, *args, **kwargs)

            # Transition succeeded — run hooks and update state
            old_state = self._state

            on_exit = getattr(self, f"on_exit_{old_state}", None)
            if callable(on_exit):
                on_exit()

            self._state = meta.to_state

            if self.track_history:
                self._state_history.append(meta.to_state)

            on_enter = getattr(self, f"on_enter_{meta.to_state}", None)
            if callable(on_enter):
                on_enter()

            return result

        wrapper.__transition__ = meta  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator


class StateMachine:
    """Base class for state machines with validated transitions.

    Subclasses must define:

    - ``states``: list of valid state names.
    - ``initial_state``: the starting state (must be in ``states``).

    Optional class attributes:

    - ``track_history``: set to ``True`` to record every state visited.

    Subclasses that override ``__init__`` must call ``super().__init__()``.
    """

    states: list[str]
    initial_state: str
    track_history: bool = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "states"):
            _validate_state_machine_class(cls)

    def __init__(self) -> None:
        self._state: str = self.initial_state
        self._state_history: list[str] = (
            [self.initial_state] if self.track_history else []
        )

    @property
    def state(self) -> str:
        """The current state."""
        return self._state

    @property
    def state_history(self) -> list[str]:
        """List of all states visited (requires ``track_history = True``)."""
        return list(self._state_history)


def _validate_state_machine_class(cls: type[StateMachine]) -> None:
    """Validate a StateMachine subclass at definition time."""
    states = cls.states

    if not states:
        raise InvalidStateError(
            f"StateMachine '{cls.__name__}' must define at least one state."
        )

    state_set = set(states)

    if not hasattr(cls, "initial_state"):
        raise InvalidStateError(
            f"StateMachine '{cls.__name__}' must define 'initial_state'."
        )

    if cls.initial_state not in state_set:
        raise InvalidStateError(
            f"Initial state '{cls.initial_state}' is not in the defined "
            f"states for '{cls.__name__}': {states}"
        )

    for attr_name in dir(cls):
        attr = getattr(cls, attr_name, None)
        meta = getattr(attr, "__transition__", None)
        if meta is None:
            continue

        invalid_from = meta.from_states - state_set
        if invalid_from:
            raise InvalidStateError(
                f"Transition '{attr_name}' in '{cls.__name__}' references "
                f"invalid from_state(s): {sorted(invalid_from)}"
            )

        if meta.to_state not in state_set:
            raise InvalidStateError(
                f"Transition '{attr_name}' in '{cls.__name__}' references "
                f"invalid to_state: '{meta.to_state}'"
            )
