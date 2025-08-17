# user_logs.py
import json
import os
from cryptography.fernet import Fernet

LOGS_FOLDER = "user_logs"  # folder to store encrypted logs per user
os.makedirs(LOGS_FOLDER, exist_ok=True)

def _log_path(username: str) -> str:
    # safe filename (simple): username + .bin
    safe = "".join(c for c in username if c.isalnum() or c in ("-", "_")).strip()
    return os.path.join(LOGS_FOLDER, f"logs_{safe}.bin")

def save_logs(username: str, fernet_key: str, logs: dict) -> None:
    """
    Encrypts JSON logs and writes to disk.
    fernet_key: string (base64 urlsafe) as returned by derive_fernet_key
    """
    path = _log_path(username)
    f = Fernet(fernet_key.encode())
    raw = json.dumps(logs).encode("utf-8")
    token = f.encrypt(raw)
    with open(path, "wb") as fh:
        fh.write(token)

def load_logs(username: str, fernet_key: str) -> dict:
    """
    Loads and decrypts logs. Returns {} if missing or decryption fails.
    """
    path = _log_path(username)
    if not os.path.exists(path):
        return {}
    try:
        f = Fernet(fernet_key.encode())
        with open(path, "rb") as fh:
            token = fh.read()
        raw = f.decrypt(token)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        # Could be wrong key -> return empty dict (or you could raise)
        return {}