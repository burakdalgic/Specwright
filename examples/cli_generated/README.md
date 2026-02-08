# CLI-Generated Examples

These files were generated using the `specwright` CLI. They show the
boilerplate that the tool produces, ready for an LLM (or a human) to
fill in the implementations.

## How they were created

```bash
# Generate a @spec-decorated function with test requirements
specwright new function calculate_score \
    --params "base: int, multiplier: float" \
    --returns float

# Generate a StateMachine subclass with sequential transitions
specwright new statemachine ticket_workflow \
    --states open,in_progress,review,closed
```

## Typical workflow

```bash
specwright init my_project          # scaffold a project
cd my_project
specwright new function do_thing    # generate function + test stubs
specwright new statemachine order   # generate state machine + test stubs
# ... fill in implementations ...
specwright validate                 # check test coverage
specwright docs                     # generate API docs
```
