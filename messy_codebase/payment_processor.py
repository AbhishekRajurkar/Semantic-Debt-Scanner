import requests

def process_payment_and_update_inventory(item_id, amount, credit_card):
    # Hardcoded vendor API keys
    stripe_key = "sk_live_999999999999999999999999"
    
    # Direct HTTP request without an interface or abstraction layer
    res = requests.post(
        "https://api.stripe.com/charges", 
        headers={"Authorization": f"Bearer {stripe_key}"}, 
        data={"amount": amount, "cc": credit_card}
    )
    
    if res.status_code == 200:
        # Re-importing inside a function and direct DB manipulation
        import sqlite3
        conn = sqlite3.connect('inventory.db')
        conn.execute(f"UPDATE items SET stock = stock - 1 WHERE id = {item_id}")
        return True
    return False
