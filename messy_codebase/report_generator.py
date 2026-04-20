class UserData:
    def __init__(self):
        self._ssn_hash = "hashed_12345" # Intended to be private

class ReportGenerator:
    def generate_compliance_report(self, user_data: UserData):
        # FLAW 8: Broken Encapsulation. Accessing a protected/private member of another class directly.
        sensitive_data = user_data._ssn_hash
        print(f"Report data: {sensitive_data}")