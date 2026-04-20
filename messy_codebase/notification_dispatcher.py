class NotificationDispatcher:
    # FLAW 3: Broken Polymorphism. Instead of an INotification interface with a .send() method, 
    # it uses a rigid if/elif chain checking object types.
    def dispatch(self, message_type, user, payload):
        if message_type == "EMAIL":
            print(f"Sending email to {user.email}: {payload}")
        elif message_type == "SMS":
            print(f"Sending SMS to {user.phone}: {payload}")
        elif message_type == "PUSH":
            print(f"Sending Push to device {user.device_id}: {payload}")
        else:
            raise ValueError("Unknown notification type")