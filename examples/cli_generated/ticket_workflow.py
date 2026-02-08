"""State machine: TicketWorkflow."""

from specwright import StateMachine, transition


class TicketWorkflow(StateMachine):
    """TODO: Describe the TicketWorkflow state machine."""

    states = ["open", "in_progress", "review", "closed"]
    initial_state = "open"
    track_history = True

    @transition(from_state="open", to_state="in_progress")
    def go_in_progress(self) -> str:
        """Transition from open to in_progress."""
        raise NotImplementedError("TODO: Implement go_in_progress")

    @transition(from_state="in_progress", to_state="review")
    def go_review(self) -> str:
        """Transition from in_progress to review."""
        raise NotImplementedError("TODO: Implement go_review")

    @transition(from_state="review", to_state="closed")
    def go_closed(self) -> str:
        """Transition from review to closed."""
        raise NotImplementedError("TODO: Implement go_closed")
