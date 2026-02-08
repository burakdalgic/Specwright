"""Tests for the StateMachine base class and @transition decorator."""

import pytest

from specwright import (
    InvalidStateError,
    InvalidTransitionError,
    StateMachine,
    TransitionMeta,
    spec,
    transition,
)


# --- Helpers ---


def make_simple_machine() -> type[StateMachine]:
    """Create a minimal state machine class for testing."""

    class Simple(StateMachine):
        states = ["a", "b", "c"]
        initial_state = "a"

        @transition(from_state="a", to_state="b")
        def go_b(self) -> str:
            return "went to b"

        @transition(from_state="b", to_state="c")
        def go_c(self) -> str:
            return "went to c"

        @transition(from_state=["a", "b"], to_state="c")
        def skip_to_c(self) -> str:
            return "skipped to c"

    return Simple


# --- Basic state transitions ---


class TestValidTransitions:
    def test_initial_state(self) -> None:
        Simple = make_simple_machine()
        sm = Simple()
        assert sm.state == "a"

    def test_single_transition(self) -> None:
        Simple = make_simple_machine()
        sm = Simple()
        result = sm.go_b()
        assert sm.state == "b"
        assert result == "went to b"

    def test_chained_transitions(self) -> None:
        Simple = make_simple_machine()
        sm = Simple()
        sm.go_b()
        sm.go_c()
        assert sm.state == "c"

    def test_transition_from_multiple_states(self) -> None:
        Simple = make_simple_machine()

        sm1 = Simple()
        sm1.skip_to_c()
        assert sm1.state == "c"

        sm2 = Simple()
        sm2.go_b()
        sm2.skip_to_c()
        assert sm2.state == "c"


# --- Invalid transitions ---


class TestInvalidTransitions:
    def test_wrong_current_state(self) -> None:
        Simple = make_simple_machine()
        sm = Simple()
        with pytest.raises(InvalidTransitionError, match="Cannot transition"):
            sm.go_c()  # requires state "b", but we're in "a"

    def test_error_message_includes_states(self) -> None:
        Simple = make_simple_machine()
        sm = Simple()
        with pytest.raises(
            InvalidTransitionError,
            match=r"from 'a' to 'c' via 'go_c'.*Valid source state\(s\): b",
        ):
            sm.go_c()

    def test_transition_after_reaching_terminal_state(self) -> None:
        Simple = make_simple_machine()
        sm = Simple()
        sm.go_b()
        sm.go_c()
        with pytest.raises(InvalidTransitionError):
            sm.go_b()  # no transition FROM "c" to "b"


# --- Method execution gating ---


class TestMethodExecution:
    def test_method_only_runs_on_valid_state(self) -> None:
        calls: list[str] = []

        class Machine(StateMachine):
            states = ["idle", "running"]
            initial_state = "idle"

            @transition(from_state="idle", to_state="running")
            def start(self) -> None:
                calls.append("started")

        sm = Machine()
        sm.start()
        assert calls == ["started"]

        with pytest.raises(InvalidTransitionError):
            sm.start()  # already running
        assert calls == ["started"]  # not called again

    def test_return_value_preserved(self) -> None:
        class Machine(StateMachine):
            states = ["off", "on"]
            initial_state = "off"

            @transition(from_state="off", to_state="on")
            def turn_on(self) -> dict:
                return {"powered": True}

        sm = Machine()
        assert sm.turn_on() == {"powered": True}

    def test_exception_prevents_state_change(self) -> None:
        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                raise RuntimeError("failed")

        sm = Machine()
        with pytest.raises(RuntimeError, match="failed"):
            sm.go()
        assert sm.state == "a"  # state unchanged


# --- State history ---


class TestStateHistory:
    def test_history_enabled(self) -> None:
        class Machine(StateMachine):
            states = ["a", "b", "c"]
            initial_state = "a"
            track_history = True

            @transition(from_state="a", to_state="b")
            def go_b(self) -> None:
                pass

            @transition(from_state="b", to_state="c")
            def go_c(self) -> None:
                pass

        sm = Machine()
        assert sm.state_history == ["a"]
        sm.go_b()
        assert sm.state_history == ["a", "b"]
        sm.go_c()
        assert sm.state_history == ["a", "b", "c"]

    def test_history_disabled_by_default(self) -> None:
        Simple = make_simple_machine()
        sm = Simple()
        sm.go_b()
        assert sm.state_history == []

    def test_history_returns_copy(self) -> None:
        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"
            track_history = True

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                pass

        sm = Machine()
        history = sm.state_history
        history.append("mutated")
        assert sm.state_history == ["a"]  # original unchanged


# --- on_enter / on_exit hooks ---


class TestHooks:
    def test_on_enter_called(self) -> None:
        calls: list[str] = []

        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                pass

            def on_enter_b(self) -> None:
                calls.append("entered b")

        sm = Machine()
        sm.go()
        assert calls == ["entered b"]

    def test_on_exit_called(self) -> None:
        calls: list[str] = []

        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                pass

            def on_exit_a(self) -> None:
                calls.append("exited a")

        sm = Machine()
        sm.go()
        assert calls == ["exited a"]

    def test_hook_order(self) -> None:
        calls: list[str] = []

        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                calls.append("method")

            def on_exit_a(self) -> None:
                calls.append("exit_a")

            def on_enter_b(self) -> None:
                calls.append("enter_b")

        sm = Machine()
        sm.go()
        assert calls == ["method", "exit_a", "enter_b"]

    def test_hooks_not_called_on_failure(self) -> None:
        calls: list[str] = []

        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                raise ValueError("boom")

            def on_exit_a(self) -> None:
                calls.append("exit_a")

            def on_enter_b(self) -> None:
                calls.append("enter_b")

        sm = Machine()
        with pytest.raises(ValueError):
            sm.go()
        assert calls == []

    def test_hooks_not_called_on_invalid_transition(self) -> None:
        calls: list[str] = []

        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="b", to_state="a")
            def go_back(self) -> None:
                pass

            def on_exit_b(self) -> None:
                calls.append("exit_b")

            def on_enter_a(self) -> None:
                calls.append("enter_a")

        sm = Machine()
        with pytest.raises(InvalidTransitionError):
            sm.go_back()
        assert calls == []

    def test_on_exit_sees_old_state(self) -> None:
        captured_state: list[str] = []

        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                pass

            def on_exit_a(self) -> None:
                # State should still be "a" during on_exit
                captured_state.append(self.state)

        sm = Machine()
        sm.go()
        assert captured_state == ["a"]

    def test_on_enter_sees_new_state(self) -> None:
        captured_state: list[str] = []

        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                pass

            def on_enter_b(self) -> None:
                captured_state.append(self.state)

        sm = Machine()
        sm.go()
        assert captured_state == ["b"]


# --- Class-level validation ---


class TestClassValidation:
    def test_invalid_initial_state(self) -> None:
        with pytest.raises(InvalidStateError, match="Initial state 'z'"):

            class Bad(StateMachine):
                states = ["a", "b"]
                initial_state = "z"

    def test_empty_states(self) -> None:
        with pytest.raises(InvalidStateError, match="at least one state"):

            class Bad(StateMachine):
                states = []
                initial_state = "a"

    def test_missing_initial_state(self) -> None:
        with pytest.raises(InvalidStateError, match="must define 'initial_state'"):

            class Bad(StateMachine):
                states = ["a", "b"]

    def test_transition_references_invalid_from_state(self) -> None:
        with pytest.raises(InvalidStateError, match="invalid from_state"):

            class Bad(StateMachine):
                states = ["a", "b"]
                initial_state = "a"

                @transition(from_state="x", to_state="b")
                def go(self) -> None:
                    pass

    def test_transition_references_invalid_to_state(self) -> None:
        with pytest.raises(InvalidStateError, match="invalid to_state"):

            class Bad(StateMachine):
                states = ["a", "b"]
                initial_state = "a"

                @transition(from_state="a", to_state="z")
                def go(self) -> None:
                    pass

    def test_subclass_inherits_and_extends(self) -> None:
        class Base(StateMachine):
            states = ["a", "b", "c"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go_b(self) -> None:
                pass

        class Child(Base):
            @transition(from_state="b", to_state="c")
            def go_c(self) -> None:
                pass

        sm = Child()
        sm.go_b()
        sm.go_c()
        assert sm.state == "c"


# --- TransitionMeta ---


class TestTransitionMeta:
    def test_metadata_attached(self) -> None:
        Simple = make_simple_machine()
        assert hasattr(Simple.go_b, "__transition__")
        meta = Simple.go_b.__transition__
        assert isinstance(meta, TransitionMeta)
        assert meta.from_states == frozenset({"a"})
        assert meta.to_state == "b"

    def test_metadata_frozen(self) -> None:
        Simple = make_simple_machine()
        meta = Simple.go_b.__transition__
        with pytest.raises(AttributeError):
            meta.to_state = "z"  # type: ignore[misc]


# --- Preserves function metadata ---


class TestPreservesMetadata:
    def test_preserves_name(self) -> None:
        Simple = make_simple_machine()
        assert Simple.go_b.__name__ == "go_b"

    def test_preserves_docstring(self) -> None:
        class Machine(StateMachine):
            states = ["a", "b"]
            initial_state = "a"

            @transition(from_state="a", to_state="b")
            def go(self) -> None:
                """My transition docstring."""

        assert Machine.go.__doc__ == "My transition docstring."


# --- Combination with @spec ---


class TestCombinationWithSpec:
    def test_transition_outside_spec(self) -> None:
        """@transition wraps @spec — spec validates types, transition validates state."""

        class Machine(StateMachine):
            states = ["idle", "done"]
            initial_state = "idle"

            @transition(from_state="idle", to_state="done")
            @spec
            def finish(self, result: str) -> str:
                """Complete the task."""
                return f"done: {result}"

        sm = Machine()
        assert sm.finish("ok") == "done: ok"
        assert sm.state == "done"

    def test_spec_validates_types_through_transition(self) -> None:
        from specwright import InputValidationError

        class Machine(StateMachine):
            states = ["idle", "done"]
            initial_state = "idle"

            @transition(from_state="idle", to_state="done")
            @spec
            def finish(self, result: str) -> str:
                """Complete the task."""
                return f"done: {result}"

        sm = Machine()
        with pytest.raises(InputValidationError):
            sm.finish(123)  # type: ignore[arg-type]
        assert sm.state == "idle"  # state unchanged on validation error


# --- Custom __init__ ---


class TestCustomInit:
    def test_subclass_with_custom_init(self) -> None:
        class Machine(StateMachine):
            states = ["off", "on"]
            initial_state = "off"

            def __init__(self, name: str) -> None:
                super().__init__()
                self.name = name

            @transition(from_state="off", to_state="on")
            def turn_on(self) -> None:
                pass

        sm = Machine("test")
        assert sm.name == "test"
        assert sm.state == "off"
        sm.turn_on()
        assert sm.state == "on"
