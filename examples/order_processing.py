"""Example: Order processing workflow with state machine.

Demonstrates a realistic order lifecycle managed by specwright's
StateMachine with history tracking, multiple source states,
and on_enter/on_exit hooks.
"""

from specwright import StateMachine, spec, transition


class OrderProcessor(StateMachine):
    states = ["pending", "paid", "shipped", "delivered", "cancelled"]
    initial_state = "pending"
    track_history = True

    def __init__(self, order_id: str) -> None:
        super().__init__()
        self.order_id = order_id

    @transition(from_state="pending", to_state="paid")
    @spec
    def pay(self, amount: float) -> str:
        """Process payment for the order."""
        return f"Order {self.order_id}: payment of ${amount:.2f} received"

    @transition(from_state="paid", to_state="shipped")
    @spec
    def ship(self, tracking: str) -> str:
        """Ship the order with a tracking number."""
        return f"Order {self.order_id}: shipped (tracking: {tracking})"

    @transition(from_state="shipped", to_state="delivered")
    @spec
    def deliver(self) -> str:
        """Mark the order as delivered."""
        return f"Order {self.order_id}: delivered"

    @transition(from_state=["pending", "paid"], to_state="cancelled")
    @spec
    def cancel(self, reason: str) -> str:
        """Cancel the order (only if not yet shipped)."""
        return f"Order {self.order_id}: cancelled ({reason})"

    def on_enter_paid(self) -> None:
        print(f"  [hook] Sending payment confirmation for {self.order_id}")

    def on_enter_shipped(self) -> None:
        print(f"  [hook] Sending shipping notification for {self.order_id}")

    def on_exit_pending(self) -> None:
        print(f"  [hook] Order {self.order_id} is no longer pending")


if __name__ == "__main__":
    # Happy path: pending -> paid -> shipped -> delivered
    order = OrderProcessor("ORD-001")
    print(order.pay(99.99))
    print(order.ship("TRACK-12345"))
    print(order.deliver())
    print(f"  History: {order.state_history}\n")

    # Cancellation path: pending -> cancelled
    order2 = OrderProcessor("ORD-002")
    print(order2.cancel("customer changed mind"))
    print(f"  History: {order2.state_history}\n")

    # Invalid transition attempt
    order3 = OrderProcessor("ORD-003")
    order3.pay(50.00)
    order3.ship("TRACK-99999")
    try:
        order3.cancel("too late")
    except Exception as e:
        print(f"  Expected error: {e}")
