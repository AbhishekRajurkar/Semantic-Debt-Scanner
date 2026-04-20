# FLAW 12: Global state mutation. Changing this dictionary in one part of the app will silently break other parts.
GLOBAL_APP_CONFIG = {
    "timeout": 30,
    "retry_attempts": 3
}

def override_timeout_for_testing():
    GLOBAL_APP_CONFIG["timeout"] = 9999