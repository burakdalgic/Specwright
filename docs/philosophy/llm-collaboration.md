# LLM Collaboration

How to work effectively with LLMs using Specwright's specification-first approach.

## The Handoff Model

Specwright enables a clean handoff between human and LLM:

| Responsibility | Human | LLM |
|---------------|-------|-----|
| **What** the function does | Type hints, docstring | - |
| **How** it does it | - | Implementation |
| **What** to test | `@requires_tests` cases | Test implementations |
| **Error policy** | `@handle_errors` mapping | - |
| **Valid states** | `StateMachine` definition | Transition logic |

The human defines the contract. The LLM fulfills it. Specwright verifies the result.

## Workflow: Function Generation

### 1. Human Writes the Spec

```python
from specwright import spec, requires_tests

@requires_tests(
    happy_path=True,
    edge_cases=["empty_list", "single_item", "duplicates"],
    error_cases=["non_numeric", "mixed_types"],
)
@spec
def median(values: list[float]) -> float:
    """Calculate the median of a list of numbers.

    For even-length lists, returns the average of the two middle values.
    Raises ValueError for empty lists.
    """
    ...
```

### 2. LLM Sees the Spec

An LLM reading this function knows:

- **Input**: `list[float]`
- **Output**: `float`
- **Behavior**: Median calculation, with averaging for even-length lists
- **Error**: `ValueError` for empty lists
- **Required tests**: 6 specific test functions

### 3. LLM Writes the Implementation

```python
@requires_tests(
    happy_path=True,
    edge_cases=["empty_list", "single_item", "duplicates"],
    error_cases=["non_numeric", "mixed_types"],
)
@spec
def median(values: list[float]) -> float:
    """Calculate the median of a list of numbers.

    For even-length lists, returns the average of the two middle values.
    Raises ValueError for empty lists.
    """
    if not values:
        raise ValueError("Cannot calculate median of empty list")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]
```

### 4. Specwright Validates

- At decoration time: type hints and docstring are present
- At runtime: arguments are `list[float]`, return is `float`
- At test time: all 6 required test functions exist

## Workflow: State Machine Generation

### 1. Human Defines the States

```python
from specwright import StateMachine, transition, spec

class DocumentReview(StateMachine):
    states = ["draft", "submitted", "in_review", "approved", "rejected", "published"]
    initial_state = "draft"
    track_history = True
```

### 2. LLM Adds Transitions

```python
class DocumentReview(StateMachine):
    states = ["draft", "submitted", "in_review", "approved", "rejected", "published"]
    initial_state = "draft"
    track_history = True

    @transition(from_state="draft", to_state="submitted")
    @spec
    def submit(self, author: str) -> str:
        """Submit the document for review."""
        return f"Submitted by {author}"

    @transition(from_state="submitted", to_state="in_review")
    @spec
    def assign_reviewer(self, reviewer: str) -> str:
        """Assign a reviewer to the document."""
        return f"Assigned to {reviewer}"

    @transition(from_state="in_review", to_state="approved")
    @spec
    def approve(self, reviewer: str) -> str:
        """Approve the document."""
        return f"Approved by {reviewer}"

    @transition(from_state="in_review", to_state="rejected")
    @spec
    def reject(self, reviewer: str, reason: str) -> str:
        """Reject the document with a reason."""
        return f"Rejected by {reviewer}: {reason}"

    @transition(from_state=["rejected", "draft"], to_state="draft")
    @spec
    def revise(self, changes: str) -> str:
        """Revise the document."""
        return f"Revised: {changes}"

    @transition(from_state="approved", to_state="published")
    @spec
    def publish(self) -> str:
        """Publish the approved document."""
        return "Published"
```

### 3. Specwright Prevents Bugs

```python
doc = DocumentReview()
doc.publish()  # Can't publish a draft!
# InvalidTransitionError: Cannot transition from 'draft' to 'published'
# via 'publish'. Valid source state(s): approved
```

The LLM can't introduce a bug where a draft gets published without review — the state machine makes it structurally impossible.

## Tips for LLM Prompts

When asking an LLM to implement Specwright-decorated functions:

### Do: Include the Full Decorator Stack

```
Implement the following function. The decorators define the contract —
follow the type hints, docstring, and test requirements exactly.

@requires_tests(happy_path=True, edge_cases=["empty"])
@spec
def process(items: list[str]) -> dict:
    """Process a list of items into a frequency dict."""
    ...
```

### Do: Ask for Tests That Match Requirements

```
Also write the tests. The @requires_tests decorator expects these
test function names: test_process_happy_path, test_process_empty
```

### Don't: Let the LLM Change the Spec

The spec is the human's domain. If an LLM suggests changing type hints, adding parameters, or modifying the docstring, that's a conversation — not an automatic change.

## Using the CLI with LLMs

The `specwright new` command generates stubs that are perfect for LLM handoff:

```bash
specwright new function search_users \
    --params "query: str, limit: int" \
    --returns "list[dict]"
```

This creates `search_users.py` with the spec already defined. Hand the file to an LLM with:

```
Fill in the implementation for search_users.py. Follow the type hints
and docstring exactly. Also complete the test file test_search_users.py.
```

The LLM writes code, you run `specwright validate`, and the framework tells you if everything checks out.
