import hashlib
import json
import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
HISTORY_DIR = BASE_DIR / "histories"
HISTORY_DIR.mkdir(exist_ok=True)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def safe_filename(email: str) -> str:
    email = normalize_email(email)
    return re.sub(r"[^a-z0-9_.-]", "_", email)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_users(users: dict) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def user_exists(email: str) -> bool:
    return normalize_email(email) in load_users()


def register_user(email: str, password: str) -> None:
    users = load_users()
    users[normalize_email(email)] = {
        "password_hash": hash_password(password)
    }
    save_users(users)


def authenticate_user(email: str, password: str) -> bool:
    users = load_users()
    email = normalize_email(email)
    return email in users and users[email].get("password_hash") == hash_password(password)


def get_history_path(email: str) -> Path:
    if email == "guest":
        return HISTORY_DIR / "guest_history.csv"
    return HISTORY_DIR / f"{safe_filename(email)}_history.csv"


def load_history(email: str) -> pd.DataFrame:
    path = get_history_path(email)
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=["date"])
    except Exception:
        return pd.DataFrame()


def save_history(email: str, history_df: pd.DataFrame) -> None:
    if email == "guest":
        return
    path = get_history_path(email)
    history_df.to_csv(path, index=False)
