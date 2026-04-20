import sqlite3

# FLAW 6: Context Bloat. Passing a massive, raw HTTP Request dictionary just to get two fields.
# FLAW 7: Missing Input Validation. Directly inserting raw data into the system without sanitizing.
def register_new_user(raw_http_request_dict):
    username = raw_http_request_dict['body']['user']['name']
    age = raw_http_request_dict['body']['user']['age']
    
    db = sqlite3.connect('users.db')
    db.execute(f"INSERT INTO users VALUES ('{username}', {age})")