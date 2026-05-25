"""
tests/test_llm_crypto.py — Tests for engine/llm/crypto.py
"""
from __future__ import annotations

import pytest
from engine.llm.crypto import decrypt_api_key, encrypt_api_key


def test_round_trip():
    plaintext = "sk-ant-api03-test-key-abc123"
    token = encrypt_api_key(plaintext)
    assert decrypt_api_key(token) == plaintext


def test_empty_string_round_trip():
    token = encrypt_api_key("")
    assert decrypt_api_key(token) == ""


def test_encrypted_is_not_plaintext():
    token = encrypt_api_key("my-secret")
    assert "my-secret" not in token


def test_bad_ciphertext_raises():
    with pytest.raises(ValueError):
        decrypt_api_key("this-is-not-a-valid-fernet-token")


def test_different_values_produce_different_tokens():
    t1 = encrypt_api_key("key-a")
    t2 = encrypt_api_key("key-b")
    assert t1 != t2
