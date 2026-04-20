class BillingService:
    def __init__(self):
        self.charges_processed = []

    # FLAW 1: Duplication (Re-implementing format_currency from utils.py)
    def to_dollars(self, val):
        return f"${val:,.2f}"

    # FLAW 2: Broken Idempotency. Calling this twice with the same order_id will charge the user twice.
    def charge_user(self, user_id, order_id, amount):
        print(f"Charging {user_id} {self.to_dollars(amount)}")
        self.charges_processed.append(order_id)
        return True