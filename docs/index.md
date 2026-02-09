---
hide:
  - navigation
---

<div class="hero" markdown>

# Build software with LLMs the right way

**Humans write specs. LLMs write code. Specwright enforces correctness.**

[![GitHub](https://img.shields.io/github/stars/burakdalgic/Specwright?style=social)](https://github.com/burakdalgic/Specwright)
[![PyPI](https://img.shields.io/pypi/v/specwright)](https://pypi.org/project/specwright/)
[![Python](https://img.shields.io/pypi/pyversions/specwright)](https://pypi.org/project/specwright/)
[![License](https://img.shields.io/github/license/burakdalgic/Specwright)](https://github.com/burakdalgic/Specwright/blob/main/LICENSE)

</div>

---

Specwright is a **specification-first Python framework** for LLM-assisted development. You define *what* your code should do — type signatures, docstrings, state machines, test requirements — and let LLMs handle *how*. The framework validates everything at decoration time and runtime, so you never have to blindly trust generated code.

```python
from specwright import spec

@spec
def calculate_score(base: int, multiplier: float) -> float:
    """Calculate a weighted score from a base value and multiplier."""
    return base * multiplier

calculate_score(100, 1.5)      # 150.0
calculate_score("bad", 1.5)    # raises InputValidationError
```

That's it. One decorator. Full type validation at runtime, docstring enforcement at decoration time, and machine-readable metadata for tooling.

---

## Key Features

- **Runtime type validation** — Arguments and return values are checked against type hints using Pydantic, catching bugs the moment they happen
- **Declarative error handling** — Map exception types to strategies (`"ignore"`, `"log"`, callables, or fallback values) without cluttering your logic
- **State machines with guardrails** — Define valid states and transitions; the framework prevents impossible state changes at runtime
- **Test requirement enforcement** — Declare what tests a function needs; a pytest plugin ensures they exist before the suite runs
- **CLI for scaffolding** — Generate projects, functions, state machines, and docs from the command line

---

## Install

```bash
pip install specwright
```

Requires Python 3.11+.

---

## Quick Example

```python
from specwright import spec, handle_errors, StateMachine, transition

# Type-safe functions with runtime validation
@spec
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y

# Declarative error handling
@handle_errors({
    ValueError: "ignore",
    KeyError: lambda e: f"missing: {e}",
})
@spec
def lookup(key: str) -> str:
    """Look up a value by key."""
    return DATA[key]

# State machines with enforced transitions
class Order(StateMachine):
    states = ["pending", "paid", "shipped"]
    initial_state = "pending"

    @transition(from_state="pending", to_state="paid")
    def pay(self, amount: float) -> str:
        return f"Paid ${amount:.2f}"

    @transition(from_state="paid", to_state="shipped")
    def ship(self, tracking: str) -> str:
        return f"Shipped: {tracking}"
```

---

<div class="grid cards" markdown>

-   :material-rocket-launch: **Get Started**

    Set up Specwright and write your first spec in under 5 minutes.

    [:octicons-arrow-right-24: Quickstart](getting-started/quickstart.md)

-   :material-book-open-variant: **Read the Guide**

    Deep dive into every feature — decorators, state machines, testing, CLI.

    [:octicons-arrow-right-24: User Guide](guide/spec-decorator.md)

-   :material-code-tags: **API Reference**

    Complete reference for every class, decorator, and exception.

    [:octicons-arrow-right-24: API Docs](api-reference/decorators.md)

-   :material-lightbulb-outline: **Philosophy**

    Why specification-first development changes the LLM workflow.

    [:octicons-arrow-right-24: Why Specwright](philosophy/why-specwright.md)

</div>
