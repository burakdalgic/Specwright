# Your First Spec

This walkthrough builds a real function from scratch, showing every check Specwright performs along the way.

## The Goal

We'll build a function that calculates a letter grade from a numeric score.

## Step 1: Start with the Spec

Before writing any logic, define the contract:

```python
from specwright import spec

@spec
def letter_grade(score: float) -> str:
    """Convert a numeric score (0-100) to a letter grade (A/B/C/D/F)."""
    ...
```

Even with `...` as the body, Specwright has already validated:

- All parameters have type annotations (`score: float`)
- The return type is declared (`-> str`)
- A docstring exists describing the behavior

If any of these are missing, you get an immediate error — not at runtime, but at **decoration time** when the module loads.

## Step 2: See Decoration-Time Checks

What happens without a docstring?

```python
@spec
def letter_grade(score: float) -> str:
    return "A"
```

```
MissingDocstringError: Function 'letter_grade' is missing a docstring.
All @spec-decorated functions must have a docstring describing their behavior.
```

Without type hints?

```python
@spec
def letter_grade(score) -> str:
    """Convert a score to a grade."""
    return "A"
```

```
MissingTypeHintError: Function 'letter_grade' is missing type hints for: score.
All @spec-decorated functions must have complete type annotations.
```

These checks happen once, when the decorator runs. They're free at runtime.

## Step 3: Implement the Function

Now fill in the logic:

```python
from specwright import spec

@spec
def letter_grade(score: float) -> str:
    """Convert a numeric score (0-100) to a letter grade (A/B/C/D/F)."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
```

## Step 4: Runtime Validation in Action

```python
>>> letter_grade(95.0)
'A'

>>> letter_grade(72)    # int is accepted for float
'C'

>>> letter_grade("ninety")
# InputValidationError: Input validation failed for 'letter_grade':
#   - Parameter 'score': expected <class 'float'>, got str ('ninety')
```

## Step 5: Add Error Handling

What if callers pass scores outside the valid range? Add `@handle_errors`:

```python
from specwright import spec, handle_errors

@handle_errors({
    ValueError: lambda e: "Invalid"
})
@spec
def letter_grade(score: float) -> str:
    """Convert a numeric score (0-100) to a letter grade (A/B/C/D/F)."""
    if not 0 <= score <= 100:
        raise ValueError(f"Score must be 0-100, got {score}")
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
```

```python
>>> letter_grade(150.0)
'Invalid'
```

## Step 6: Declare Test Requirements

Tell Specwright what tests this function needs:

```python
from specwright import spec, handle_errors, requires_tests

@requires_tests(
    happy_path=True,
    edge_cases=["boundary_90", "boundary_60", "zero_score"],
    error_cases=["negative_score", "over_100"],
)
@handle_errors({ValueError: lambda e: "Invalid"})
@spec
def letter_grade(score: float) -> str:
    """Convert a numeric score (0-100) to a letter grade (A/B/C/D/F)."""
    ...
```

Check what tests are expected:

```python
>>> letter_grade.__test_requirements__.expected_test_names
['test_letter_grade_happy_path',
 'test_letter_grade_boundary_90',
 'test_letter_grade_boundary_60',
 'test_letter_grade_zero_score',
 'test_letter_grade_negative_score',
 'test_letter_grade_over_100']
```

The pytest plugin will verify all six test functions exist before the suite runs.

## The Full Picture

```python
from specwright import spec, handle_errors, requires_tests

@requires_tests(
    happy_path=True,
    edge_cases=["boundary_90", "boundary_60", "zero_score"],
    error_cases=["negative_score", "over_100"],
)
@handle_errors({ValueError: lambda e: "Invalid"})
@spec
def letter_grade(score: float) -> str:
    """Convert a numeric score (0-100) to a letter grade (A/B/C/D/F)."""
    if not 0 <= score <= 100:
        raise ValueError(f"Score must be 0-100, got {score}")
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
```

Three decorators, each with a clear role:

1. `@requires_tests` — declares **what to test**
2. `@handle_errors` — declares **how to handle failures**
3. `@spec` — declares **what the function is** and enforces it

!!! tip "Why this matters for LLM-assisted development"
    This is the Specwright workflow: a human writes the three-decorator stack defining the contract (types, behavior, error handling, test requirements). An LLM fills in the implementation. The framework enforces correctness at every level — decoration time, runtime, and test time. The human never has to read the implementation to trust it.
