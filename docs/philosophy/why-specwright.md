# Why Specwright

## The Problem

Modern software development increasingly involves LLMs generating code. This creates a fundamental trust problem: **how do you know the generated code is correct?**

The traditional answer — code review — doesn't scale. Reviewing LLM-generated code line by line defeats the purpose of using LLMs. And automated testing alone isn't enough, because someone still needs to decide *what* to test.

## The Approach

Specwright inverts the problem. Instead of reviewing generated code, you **define contracts that the code must satisfy**, and the framework enforces those contracts automatically.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Human     │     │    LLM      │     │  Specwright  │
│             │     │             │     │             │
│ Writes:     │────▶│ Writes:     │────▶│ Enforces:   │
│ - Types     │     │ - Logic     │     │ - Types     │
│ - Docstring │     │ - Algorithm │     │ - Contracts │
│ - States    │     │ - Tests     │     │ - States    │
│ - Tests req │     │             │     │ - Coverage  │
└─────────────┘     └─────────────┘     └─────────────┘
```

The human stays in control of **what** the software does. The LLM handles **how**. The framework bridges the two.

## Three Layers of Enforcement

### Layer 1: Decoration Time

When a module is imported, Specwright validates:

- Every `@spec` function has complete type annotations
- Every `@spec` function has a docstring
- Every `StateMachine` subclass has valid states and transitions

These checks catch structural problems immediately — before any code runs.

### Layer 2: Runtime

When functions are called, Specwright validates:

- Input arguments match declared type hints
- Return values match declared return types
- State transitions are valid for the current state

These checks catch behavioral problems as they happen.

### Layer 3: Test Time

When `pytest` collects tests, Specwright validates:

- Every `@requires_tests` function has the expected test functions
- Test names follow the naming convention

This catches coverage gaps before the test suite runs.

## Why Not Just Use Type Checkers?

Tools like mypy catch type errors **statically** — at analysis time. Specwright catches them **dynamically** — at runtime. Both are valuable, but they serve different purposes:

| Feature | mypy | Specwright |
|---------|------|------------|
| **When** | Static analysis | Runtime |
| **Catches** | Type mismatches in your code | Type mismatches in generated or dynamic code |
| **Requires** | Running a separate tool | Nothing — works at import time |
| **Complex types** | Full support | Full support (via Pydantic) |
| **Documentation** | No | Yes — docstrings enforced, metadata generated |
| **State machines** | No | Yes — validated transitions |
| **Test requirements** | No | Yes — enforced coverage |

Specwright and mypy are **complementary**. Use both.

## Why Not Just Write Tests?

Tests verify specific scenarios. Specwright enforces **structural invariants**:

- "This function always takes an int and returns a str" (not just in the test cases you wrote)
- "This state machine never transitions from shipped to cancelled" (not just when you test it)
- "This function has tests for all edge cases" (not just the ones you remember)

Tests tell you "this specific input produces this specific output." Specwright tells you "this function's contract is always satisfied."

## The Specification-First Workflow

1. **Define the spec** — Type hints, docstrings, state machines, test requirements
2. **Generate the implementation** — Ask an LLM, or write it yourself
3. **Run and validate** — Specwright enforces the spec at every level
4. **Iterate** — If the implementation is wrong, the spec catches it

This workflow works because specs are **concise** (a few lines of type hints and a docstring) but **powerful** (they constrain the entire behavior of the function). You write 5 lines of spec, the LLM writes 50 lines of implementation, and Specwright ensures the 50 lines satisfy the 5.
