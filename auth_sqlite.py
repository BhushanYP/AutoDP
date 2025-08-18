# auth_sqlite.py
import sqlite3
import base64
import secrets
import time
import json
from hashlib import pbkdf2_hmac

DB_FILE = "users.db"

# ---- Try to use Argon2id (recommended). Fallback to PBKDF2 if unavailable. ----
try:
    from argon2 import PasswordHasher, exceptions as argon2_exceptions
    PH = PasswordHasher()  # default params are solid for most apps
    HAS_ARGON2 = True
except Exception:
    PH = None
    HAS_ARGON2 = False


# =========================
# DB SETUP & MIGRATIONS
# =========================
def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def _col_exists(c, table, col):
    c.execute(f"PRAGMA table_info({table})")
    return any(row[1] == col for row in c.fetchall())

def init_db():
    """
    Create tables if missing and migrate schema safely without losing data.
    """
    conn = get_connection()
    c = conn.cursor()

    # --- users table (base) ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            display_name TEXT,
            password TEXT,
            salt TEXT
        )
    """)

    # Add new columns if they don't exist (online migrations).
    # password_algo: 'argon2' or 'pbkdf2'
    if not _col_exists(c, "users", "password_algo"):
        c.execute("ALTER TABLE users ADD COLUMN password_algo TEXT")

    # failed_attempts: count consecutive failures
    if not _col_exists(c, "users", "failed_attempts"):
        c.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0")

    # lock_until: unix timestamp until which login is blocked
    if not _col_exists(c, "users", "lock_until"):
        c.execute("ALTER TABLE users ADD COLUMN lock_until INTEGER DEFAULT 0")

    # meta timestamps (optional)
    if not _col_exists(c, "users", "created_at"):
        c.execute("ALTER TABLE users ADD COLUMN created_at INTEGER")
    if not _col_exists(c, "users", "updated_at"):
        c.execute("ALTER TABLE users ADD COLUMN updated_at INTEGER")

    # Backfill password_algo for existing rows if null
    c.execute("UPDATE users SET password_algo='pbkdf2' WHERE password_algo IS NULL")

    # --- logs table (keep your original JSON-per-user design for compatibility) ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            username TEXT PRIMARY KEY,
            logs TEXT
        )
    """)

    conn.commit()
    conn.close()

# Run migrations on import
init_db()


# =========================
# SECURITY CONSTANTS
# =========================
# PBKDF2 params (used for fallback & legacy verification + Fernet derivation)
PBKDF2_ITER = 390_000

# Lockout policy
MAX_FAILS_BEFORE_LOCK = 5
BASE_LOCK_SECONDS = 60           # first lock: 60s
MAX_LOCK_SECONDS = 60 * 30       # cap at 30 minutes


# =========================
# PASSWORD HASHING
# =========================
def _hash_password_pbkdf2(password: str, salt: bytes = None):
    """
    PBKDF2 hashing (legacy). Returns (hash_b64, salt_b64).
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    pwd_hash = pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITER)
    return base64.b64encode(pwd_hash).decode(), base64.b64encode(salt).decode()

def _verify_pbkdf2(password: str, stored_hash_b64: str, salt_b64: str) -> bool:
    salt = base64.b64decode(salt_b64)
    trial_hash_b64, _ = _hash_password_pbkdf2(password, salt)
    return secrets.compare_digest(trial_hash_b64, stored_hash_b64)

def _hash_password_argon2(password: str) -> str:
    """
    Argon2id hashing (modern). Returns the full encoded hash string ($argon2id$...).
    """
    if not HAS_ARGON2:
        raise RuntimeError("Argon2 is not available")
    return PH.hash(password)

def _verify_argon2(password: str, encoded_hash: str) -> bool:
    try:
        PH.verify(encoded_hash, password)
        # If Argon2 recommends rehash (params changed), you could rehash here.
        return True
    except Exception:
        return False


# =========================
# USER CRUD & AUTH
# =========================
def user_exists(username: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username=?", (username,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def create_user(username: str, display_name: str, password: str):
    """
    Create a new user.
    - Stores password as Argon2id (if available) otherwise PBKDF2.
    - Always stores a per-user 'salt' (as base64) for *encryption key derivation*,
      keeping compatibility with your Streamlit code that reads salt to derive Fernet keys.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False, "Username already exists."

    now = int(time.time())

    # This 'enc_salt' is not used for Argon2 (which stores its own salt internally).
    # We keep it so your front-end can continue deriving Fernet keys the same way.
    enc_salt_b64 = base64.b64encode(secrets.token_bytes(16)).decode()

    if HAS_ARGON2:
        pwd_hash = _hash_password_argon2(password)
        password_algo = "argon2"
        # For Argon2, the 'salt' column is purely for your Fernet key derivation.
        c.execute(
            "INSERT INTO users (username, display_name, password, salt, password_algo, failed_attempts, lock_until, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)",
            (username, display_name, pwd_hash, enc_salt_b64, password_algo, now, now),
        )
    else:
        # Fallback to PBKDF2 (still secure, but please install argon2-cffi!)
        pwd_hash_b64, pbk_salt_b64 = _hash_password_pbkdf2(password)
        password_algo = "pbkdf2"
        # Use the PBKDF2 salt for both password hashing and Fernet derivation (compat).
        c.execute(
            "INSERT INTO users (username, display_name, password, salt, password_algo, failed_attempts, lock_until, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)",
            (username, display_name, pwd_hash_b64, pbk_salt_b64, password_algo, now, now),
        )

    conn.commit()
    conn.close()
    return True, "User created."

def _apply_lockout_policy(c, username: str, failed_attempts: int):
    """
    Exponential backoff lockout:
      attempts >= MAX_FAILS_BEFORE_LOCK -> lock for BASE * 2^(attempts - MAX_FAILS)
      capped at MAX_LOCK_SECONDS
    """
    lock_seconds = BASE_LOCK_SECONDS * (2 ** max(0, failed_attempts - MAX_FAILS_BEFORE_LOCK))
    lock_seconds = min(lock_seconds, MAX_LOCK_SECONDS)
    lock_until = int(time.time()) + lock_seconds
    c.execute("UPDATE users SET lock_until=?, updated_at=? WHERE username=?", (lock_until, int(time.time()), username))
    return lock_until

def get_lock_status(username: str):
    """
    Helper for the UI: returns {'locked': bool, 'lock_until': int, 'seconds_left': int}
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT lock_until FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {"locked": False, "lock_until": 0, "seconds_left": 0}
    lock_until = row[0] or 0
    now = int(time.time())
    return {
        "locked": now < lock_until,
        "lock_until": lock_until,
        "seconds_left": max(0, lock_until - now),
    }

def verify_user(username: str, password: str) -> bool:
    """
    Backend-ENFORCED verification with lockout.
    Signature kept as bool for compatibility with your Streamlit code.
    - Returns False if user is locked or credentials invalid.
    - Resets failed_attempts & lock_until on success.
    - Seamlessly migrates PBKDF2 users to Argon2 after a successful login.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password, salt, password_algo, failed_attempts, lock_until FROM users WHERE username=?", (username,))
    row = c.fetchone()

    if not row:
        conn.close()
        return False

    stored_password, salt_b64, algo, fails, lock_until = row
    now = int(time.time())

    # Enforce lockout
    if lock_until and now < lock_until:
        conn.close()
        return False

    ok = False
    if algo == "argon2" or (HAS_ARGON2 and isinstance(stored_password, str) and stored_password.startswith("$argon2")):
        # Argon2 verify
        ok = _verify_argon2(password, stored_password)
    else:
        # PBKDF2 verify (legacy)
        ok = _verify_pbkdf2(password, stored_password, salt_b64)

    if ok:
        # Reset counters
        c.execute("UPDATE users SET failed_attempts=0, lock_until=0, updated_at=? WHERE username=?", (now, username))
        # If this was a PBKDF2 user and Argon2 is available, migrate now (transparent to the user)
        if HAS_ARGON2 and algo != "argon2":
            try:
                new_hash = _hash_password_argon2(password)
                # Keep the existing salt_b64 for Fernet derivation compatibility
                c.execute("UPDATE users SET password=?, password_algo='argon2', updated_at=? WHERE username=?", (new_hash, now, username))
            except Exception:
                # If rehash fails for any reason, user remains on PBKDF2 (still fine)
                pass

        conn.commit()
        conn.close()
        return True
    else:
        # Increment failed attempts and maybe lock
        fails = (fails or 0) + 1
        c.execute("UPDATE users SET failed_attempts=?, updated_at=? WHERE username=?", (fails, now, username))
        if fails >= MAX_FAILS_BEFORE_LOCK:
            _apply_lockout_policy(c, username, fails)
        conn.commit()
        conn.close()
        return False


# =========================
# FERNET KEY (COMPATIBLE)
# =========================
def derive_fernet_key(password: str, salt_b64: str) -> str:
    """
    Derive a Fernet key for encrypting user data from password + the 'salt' column.
    Kept compatible with your existing Streamlit code.
    """
    salt = base64.b64decode(salt_b64)
    k = pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITER, dklen=32)
    return base64.urlsafe_b64encode(k).decode()


# =========================
# LOGS (COMPATIBLE)
# =========================
def save_logs(username, logs_dict):
    """
    Save a user's activity logs as JSON (one row per user).
    """
    conn = get_connection()
    c = conn.cursor()
    logs_json = json.dumps(logs_dict)
    c.execute("INSERT OR REPLACE INTO logs (username, logs) VALUES (?, ?)", (username, logs_json))
    conn.commit()
    conn.close()

def load_logs(username):
    """
    Load a user's activity logs (returns dict). Defaults to {'uploads': {}} if empty.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT logs FROM logs WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except Exception:
            return {"uploads": {}}
    return {"uploads": {}}


# =========================
# OPTIONAL: ADMIN / UTIL
# =========================
def reset_password(username: str, new_password: str) -> bool:
    """
    Force-reset a user's password (e.g., from an admin or a verified reset flow).
    Preserves the 'salt' column for Fernet derivation (generates one if missing).
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT salt FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False

    now = int(time.time())
    salt_b64 = row[0]
    if not salt_b64:
        salt_b64 = base64.b64encode(secrets.token_bytes(16)).decode()

    if HAS_ARGON2:
        new_hash = _hash_password_argon2(new_password)
        c.execute(
            "UPDATE users SET password=?, password_algo='argon2', salt=?, failed_attempts=0, lock_until=0, updated_at=? WHERE username=?",
            (new_hash, salt_b64, now, username),
        )
    else:
        # fallback: PBKDF2
        pwd_hash_b64, pbk_salt_b64 = _hash_password_pbkdf2(new_password)
        # Use pbkdf2 salt in both places for compatibility
        c.execute(
            "UPDATE users SET password=?, password_algo='pbkdf2', salt=?, failed_attempts=0, lock_until=0, updated_at=? WHERE username=?",
            (pwd_hash_b64, pbk_salt_b64, now, username),
        )

    conn.commit()
    conn.close()
    return True
