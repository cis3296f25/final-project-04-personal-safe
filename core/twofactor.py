import base64
import hashlib
import hmac
import struct
import time
import os
from typing import Tuple

try:
    import pyotp

    _HAS_PYOTP = True
except Exception:
    _HAS_PYOTP = False

try:
    import qrcode
    import io

    _HAS_QRCODE = True
except Exception:
    _HAS_QRCODE = False


def generate_secret() -> str:
    if _HAS_PYOTP:
        return pyotp.random_base32()

    return base64.b32encode(os.urandom(10)).decode("utf-8")


def provisioning_uri(secret: str, account_name: str, issuer: str) -> str:
    if _HAS_PYOTP:
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=account_name, issuer_name=issuer
        )

    label = f"{issuer}:{account_name}"
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer}"


def make_qr_data_uri(otpauth_uri: str) -> str | None:
    if not _HAS_QRCODE:
        return None
    buf = io.BytesIO()
    img = qrcode.make(otpauth_uri)
    img.save(buf, format="PNG")
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{data}"


def verify_code(secret: str, code: str, window: int = 1) -> bool:
    if not code:
        return False
    code = str(code).strip()
    if _HAS_PYOTP:
        totp = pyotp.TOTP(secret)
        return bool(totp.verify(code, valid_window=window))

    try:
        return _totp_verify_fallback(secret, code, window=window)
    except Exception:
        return False


def _int_to_bytes(i: int) -> bytes:
    return struct.pack(
        ">Q",
        i,
    )


def _hotp(base32_secret: str, counter: int, digits: int = 6) -> str:
    key = base64.b32decode(base32_secret, casefold=True)
    h = hmac.new(key, _int_to_bytes(counter), hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(code).zfill(digits)


def _totp_verify_fallback(
    base32_secret: str,
    code: str,
    step: int = 30,
    window: int = 1,
    digits: int = 6,
    t0: int = 0,
) -> bool:
    t = int((time.time() - t0) // step)
    for drift in range(-window, window + 1):
        if _hotp(base32_secret, t + drift, digits) == str(code).zfill(digits):
            return True
    return False
