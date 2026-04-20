# Clean file, used to trigger the duplication flaw elsewhere.
import re

def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"

def validate_email_format(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))