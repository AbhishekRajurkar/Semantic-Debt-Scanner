import requests

class InventoryAPI:
    # FLAW 4: Tightly coupled to infra. No dependency injection for the HTTP client.
    # FLAW 5: Failure to handle non-deterministic output. Network calls fail, but there is no retry, timeout, or fallback logic.
    def fetch_stock(self, item_id):
        response = requests.get(f"https://api.inventory.internal/stock/{item_id}")
        return response.json()['stock_count'] # Will violently crash if network fails or JSON is malformed