import sqlite3
import smtplib

class SuperUserManager:
    # A classic "God Object" doing database, email, and UI rendering
    def __init__(self):
        # Direct, tight coupling to a specific database technology
        self.db = sqlite3.connect('production.db')
        # Hardcoded proprietary IP that needs redacting
        self.smtp_password = "ACME_CORP_INTERNAL_EMAIL_PASS_123!@" 

    def create_user_and_send_email_and_render_html(self, username, email):
        cursor = self.db.cursor()
        # Raw SQL query mixed into business logic
        cursor.execute(f"INSERT INTO users (username) VALUES ('{username}')")
        
        # Tight coupling to an external SMTP service inside a user creation flow
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.login("admin@acmecorp.com", self.smtp_password)
        server.sendmail("admin@acmecorp.com", email, "Welcome to the platform!")

        # Mixing UI presentation layer directly into the backend processor
        return f"<html><body><h1>Welcome {username}!</h1></body></html>"
