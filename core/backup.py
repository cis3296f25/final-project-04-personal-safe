import os
import json
import base64
import hashlib
from typing import Any, Dict

from .crypto import CryptoUtils

PBKDF2_ITERATIONS = 100_000
SALT_SIZE = 16  # bytes


def _derive_key_from_password(password: str, salt: bytes, dklen: int = 32) -> bytes:
    """
    Derive a symmetric key from `password` and `salt` using PBKDF2-HMAC-SHA256.
    Returns raw bytes suitable for CryptoUtils.encrypt/decrypt.
    """
    if password is None:
        raise ValueError("Password required for key derivation")
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen)


def create_encrypted_backup_bytes(obj: Any, password: str) -> bytes:
    """
    Serialize `obj` (usually a dict) to JSON, derive a key and encrypt.
    Returns bytes that are a UTF-8 JSON object:
      {"salt": "<base64>", "payload": "<base64 token>"}
    """
    salt = os.urandom(SALT_SIZE)
    key = _derive_key_from_password(password, salt, dklen=32)

    plaintext = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    token = CryptoUtils.encrypt(plaintext, key)

    out = {"salt": base64.b64encode(salt).decode("ascii"), "payload": token}
    return json.dumps(out, indent=2).encode("utf-8")


def decrypt_encrypted_backup_bytes(data: bytes, password: str) -> Any:
    """
    Read backup JSON bytes created by create_encrypted_backup_bytes,
    derive key using stored salt and password, decrypt payload and return parsed JSON object.
    Raises ValueError on bad password / malformed file.
    """
    try:
        obj = json.loads(data.decode("utf-8"))
        salt_b64 = obj.get("salt")
        payload = obj.get("payload")
        if not salt_b64 or not payload:
            raise ValueError("Invalid backup file format")
        salt = base64.b64decode(salt_b64.encode("ascii"))
    except Exception as e:
        raise ValueError(f"Failed to parse backup file: {e}")

    key = _derive_key_from_password(password, salt, dklen=32)
    try:
        plaintext = CryptoUtils.decrypt(payload, key)
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")

    try:
        return json.loads(plaintext)
    except Exception as e:
        raise ValueError(f"Failed to parse decrypted JSON: {e}")


def save_encrypted_backup_file(obj: Any, password: str, filepath: str) -> None:
    """Helper to create and write an encrypted backup file to `filepath`."""
    b = create_encrypted_backup_bytes(obj, password)
    with open(filepath, "wb") as f:
        f.write(b)


def load_encrypted_backup_file(filepath: str, password: str) -> Any:
    """Helper to load and decrypt an encrypted backup file from `filepath`."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)
    with open(filepath, "rb") as f:
        data = f.read()
    return decrypt_encrypted_backup_bytes(data, password)