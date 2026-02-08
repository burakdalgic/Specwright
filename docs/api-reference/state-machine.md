# State Machine API Reference

## StateMachine

```python
from specwright import StateMachine
```

Base class for state machines with validated transitions.

### Class Attributes (Required)

| Attribute | Type | Description |
|-----------|------|-------------|
| `states` | `list[str]` | List of valid state names |
| `initial_state` | `str` | Starting state (must be in `states`) |

### Class Attributes (Optional)

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `track_history` | `bool` | `False` | Record every state visited |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `state` | `str` | Current state |
| `state_history` | `list[str]` | Copy of all states visited (empty if `track_history=False`) |

### Class Validation

Subclasses are validated at definition time (`__init_subclass__`):

| Check | Exception |
|-------|-----------|
| `states` is non-empty | `InvalidStateError` |
| `initial_state` is defined | `InvalidStateError` |
| `initial_state` is in `states` | `InvalidStateError` |
| All transition `from_state` values are in `states` | `InvalidStateError` |
| All transition `to_state` values are in `states` | `InvalidStateError` |

### Lifecycle Hooks

Define methods matching these patterns to run code on state changes:

| Method Pattern | Called When |
|---------------|------------|
| `on_exit_{state_name}(self)` | After transition method succeeds, before state updates |
| `on_enter_{state_name}(self)` | After state updates to the new value |

### Example

```python
class Order(StateMachine):
    states = ["pending", "paid", "shipped"]
    initial_state = "pending"
    track_history = True

    @transition(from_state="pending", to_state="paid")
    def pay(self, amount: float) -> str:
        return f"Paid ${amount:.2f}"

    @transition(from_state="paid", to_state="shipped")
    def ship(self, tracking: str) -> str:
        return f"Shipped: {tracking}"

    def on_enter_paid(self):
        print("Payment received")

order = Order()
order.pay(99.99)          # "Paid $99.99"
order.state               # "paid"
order.state_history       # ["pending", "paid"]
```

---

## @transition

```python
from specwright import transition
```

Decorator that marks a method as a state transition.

### Signature

```python
@transition(from_state: str | list[str], to_state: str)
def method(self, ...):
    ...
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_state` | `str \| list[str]` | Valid source state(s) for this transition |
| `to_state` | `str` | Target state after successful execution |

### Behavior

1. Check that `self.state` is in `from_state` — raise `InvalidTransitionError` if not
2. Execute the decorated method
3. If the method raises, state is **unchanged** (no hooks run)
4. If the method succeeds:
    - Call `on_exit_{old_state}()` if defined
    - Update state to `to_state`
    - Append to history if `track_history=True`
    - Call `on_enter_{new_state}()` if defined
5. Return the method's return value

### Raises

| Exception | When |
|-----------|------|
| `InvalidTransitionError` | Current state is not in `from_state` |

### Attached Metadata

Decorated methods gain a `__transition__` attribute containing a `TransitionMeta` instance.

---

## TransitionMeta

```python
from specwright import TransitionMeta
```

Frozen dataclass stored on `@transition`-decorated methods.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `from_states` | `frozenset[str]` | Valid source states |
| `to_state` | `str` | Target state |

### Example

```python
class Machine(StateMachine):
    states = ["a", "b"]
    initial_state = "a"

    @transition(from_state="a", to_state="b")
    def go(self): pass

meta = Machine.go.__transition__
assert meta.from_states == frozenset({"a"})
assert meta.to_state == "b"
```
