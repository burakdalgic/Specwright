"""Example: User account lifecycle with state machine.

Demonstrates a user account that can move between active, suspended,
and deactivated states, with on_enter/on_exit hooks for side effects.
"""

from specwright import StateMachine, transition


class UserAccount(StateMachine):
    states = ["active", "suspended", "deactivated"]
    initial_state = "active"
    track_history = True

    def __init__(self, username: str) -> None:
        super().__init__()
        self.username = username

    @transition(from_state="active", to_state="suspended")
    def suspend(self, reason: str) -> None:
        """Suspend the account for a given reason."""
        print(f"  Suspending {self.username}: {reason}")

    @transition(from_state="suspended", to_state="active")
    def reactivate(self) -> None:
        """Reactivate a suspended account."""
        print(f"  Reactivating {self.username}")

    @transition(from_state=["active", "suspended"], to_state="deactivated")
    def deactivate(self) -> None:
        """Permanently deactivate the account."""
        print(f"  Deactivating {self.username}")

    # --- Hooks ---

    def on_exit_active(self) -> None:
        print(f"  [hook] Recording last-active timestamp for {self.username}")

    def on_enter_suspended(self) -> None:
        print(f"  [hook] Sending suspension notice to {self.username}")

    def on_enter_active(self) -> None:
        print(f"  [hook] Welcome back, {self.username}!")

    def on_enter_deactivated(self) -> None:
        print(f"  [hook] Archiving data for {self.username}")


if __name__ == "__main__":
    # Suspend and reactivate
    alice = UserAccount("alice")
    print(f"State: {alice.state}")

    alice.suspend("policy violation")
    print(f"State: {alice.state}")

    alice.reactivate()
    print(f"State: {alice.state}")
    print(f"History: {alice.state_history}\n")

    # Deactivate from suspended
    bob = UserAccount("bob")
    bob.suspend("inactivity")
    bob.deactivate()
    print(f"Bob's state: {bob.state}")
    print(f"Bob's history: {bob.state_history}\n")

    # Cannot transition from deactivated
    try:
        bob.reactivate()
    except Exception as e:
        print(f"Expected error: {e}")
