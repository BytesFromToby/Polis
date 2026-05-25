"""
engine/llm/crypto.py — API key encryption for LLM profiles.

Uses Fernet (AES-128-CBC + HMAC-SHA256) with a key derived from the
machine's MAC address. Protects against casual file inspection and
accidental log exposure on the local machine.
"""
from __future__ import annotations

import base64
import hashlib
import uuid

from cryptography.fernet import Fernet, InvalidToken


def _derive_fernet_key() -> bytes:
    seed = str(uuid.getnode()).encode()
    raw = hashlib.sha256(seed).digest()        # 32 bytes
    return base64.urlsafe_b64encode(raw)       # Fernet requires url-safe base64


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt a plaintext API key. Returns a base64 Fernet token string."""
    f = Fernet(_derive_fernet_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """
    Decrypt a Fernet token back to plaintext.
    Raises ValueError if the token is invalid or was encrypted on a different machine.
    """
    try:
        f = Fernet(_derive_fernet_key())
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt API key — token invalid or wrong machine") from exc
