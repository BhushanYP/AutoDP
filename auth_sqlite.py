import sqlite3
import base64
import secrets
from hashlib import pbkdf2_hmac
import json

DB_FILE = "users.db"

# -------------------- DB Setup --------------------
def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            display_name TEXT,
            password TEXT,
            salt TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            username TEXT PRIMARY KEY,
            logs TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

import base64
import secrets
from hashlib import pbkdf2_hmac

# -------------------- Password Hashing --------------------
def _hash_password(password: str, salt: bytes = None):
    """
    Hash a password with a random salt.
    Returns (hashed_password, salt) as base64 strings.
    """
    if salt is None:
        salt = secrets.token_bytes(16)  # 16-byte random salt
    pwd_hash = pbkdf2_hmac("sha256", password.encode(), salt, 390000)
    return base64.b64encode(pwd_hash).decode(), base64.b64encode(salt).decode()

# -------------------- Create User --------------------
def create_user(username: str, display_name: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False, "Username already exists."
    pwd_hash, salt_b64 = _hash_password(password)
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, display_name, pwd_hash, salt_b64))
    conn.commit()
    conn.close()
    return True, "User created."

# -------------------- Verify User --------------------
def verify_user(username: str, password: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password, salt FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    stored_pwd, salt_b64 = row
    salt = base64.b64decode(salt_b64)
    trial_hash, _ = _hash_password(password, salt)
    return secrets.compare_digest(trial_hash, stored_pwd)

# -------------------- Fernet Key --------------------
def derive_fernet_key(password: str, salt_b64: str) -> str:
    """
    Derive a key for encrypting user logs (Fernet key) from password and salt.
    """
    salt = base64.b64decode(salt_b64)
    k = pbkdf2_hmac("sha256", password.encode(), salt, 390000, dklen=32)
    return base64.urlsafe_b64encode(k).decode()

import json

# -------------------- Save Logs --------------------
def save_logs(username, logs_dict):
    """
    Save a user's activity logs as JSON in the database.
    """
    conn = get_connection()
    c = conn.cursor()
    logs_json = json.dumps(logs_dict)
    # Insert or replace logs for this user
    c.execute("INSERT OR REPLACE INTO logs VALUES (?, ?)", (username, logs_json))
    conn.commit()
    conn.close()

# -------------------- Load Logs --------------------
def load_logs(username):
    """
    Load a user's activity logs from the database.
    Returns a dictionary.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT logs FROM logs WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    # If no logs exist yet, return empty structure
    return {"uploads": {}}

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Create users table if it doesn't exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            display_name TEXT,
            password TEXT,
            salt TEXT,
            logs TEXT
        )
    """)
    conn.commit()
    conn.close()