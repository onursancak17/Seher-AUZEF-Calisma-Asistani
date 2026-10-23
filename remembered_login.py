"""Password-bound, signed device credentials; no password is sent to the browser."""
import hashlib
import hmac
import re
import secrets
from functools import lru_cache


@lru_cache(maxsize=4)
def _signing_key(password):
    return hashlib.pbkdf2_hmac(
        'sha256', str(password).encode('utf-8'),
        b'Seher-AUZEF-Calisma-Asistani/remember-device/v1', 600_000,
    )


def password_tag(password):
    return hmac.new(_signing_key(password), b'active-session', 'sha256').hexdigest()


def issue_token(password):
    payload = 'v1.' + secrets.token_urlsafe(32)
    signature = hmac.new(_signing_key(password), payload.encode('ascii'), 'sha256').hexdigest()
    return payload + '.' + signature


def valid_token(token, password):
    if not isinstance(token, str) or not re.fullmatch(r'v1\.[A-Za-z0-9_-]{43}\.[0-9a-f]{64}', token):
        return False
    payload, signature = token.rsplit('.', 1)
    expected = hmac.new(_signing_key(password), payload.encode('ascii'), 'sha256').hexdigest()
    return hmac.compare_digest(signature, expected)
