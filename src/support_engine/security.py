"""The webhook signature binds the timestamp to the exact request bytes."""

import hashlib
import hmac
import time


def signature(secret: str, timestamp: str, body: bytes) -> str:
    signed = timestamp.encode() + b"." + body
    return "sha256=" + hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def verify_signature(secret: str, timestamp: str, supplied: str, body: bytes) -> bool:
    try:
        age = abs(time.time() - int(timestamp))
    except ValueError:
        return False
    if age > 300:
        return False
    expected = signature(secret, timestamp, body)
    # Bytes also let a malformed non-ASCII header fail without raising an exception.
    return hmac.compare_digest(expected.encode(), supplied.encode())
