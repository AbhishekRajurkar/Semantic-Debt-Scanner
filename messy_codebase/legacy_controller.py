# FLAW 11: Absolute SRP Violation. Mixing HTML presentation, file system I/O, and business logic.
def render_user_profile(user_id):
    with open("/var/logs/profile_access.log", "a") as f:
        f.write(f"Accessed {user_id}\n")
    
    user_name = "John Doe" # Mock DB call
    return f"<html><body><h1>Profile: {user_name}</h1></body></html>"