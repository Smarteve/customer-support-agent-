import hashlib
import hmac
import time


def signature(secret: str, timestamp: str, body: bytes) -> str:
    signed = timestamp.encode() + b"." + body
    return "sha256=" + hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def verify_signature(
    secret: str, timestamp: str, supplied: str, body: bytes, window_seconds: int = 300
) -> bool:
    try:
        age = abs(time.time() - int(timestamp))
    except (TypeError, ValueError):
        return False
    return age <= window_seconds and hmac.compare_digest(
        signature(secret, timestamp, body).encode(), supplied.encode()
    )
