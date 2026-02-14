import os
import base64

from cryptography.fernet import Fernet


def get_fernet():
    key = os.environ.get("DERIV_ENCRYPTION_KEY", "")
    if not key:
        raise ValueError("DERIV_ENCRYPTION_KEY not set")
    # Convert hex key to Fernet-compatible base64
    key_bytes = bytes.fromhex(key)
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_token(token: str) -> str:
    f = get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    f = get_fernet()
    return f.decrypt(encrypted.encode()).decode()
