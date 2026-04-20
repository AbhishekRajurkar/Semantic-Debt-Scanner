import sqlite3

class OrderWorkflow:
    # FLAW 9: Method doing too much. It calculates totals, updates the DB, AND handles external shipping logic.
    def process_checkout(self, cart_items):
        total = sum([item.price for item in cart_items])
        total_with_tax = total * 1.08
        
        db = sqlite3.connect('orders.db')
        db.execute(f"INSERT INTO orders VALUES ({total_with_tax})")
        
        print("Contacting FedEx API to generate shipping label...")
        return total_with_tax