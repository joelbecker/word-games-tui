"""Password-based encryption for puzzle files, using only the standard library.

This file is shared verbatim between word-game-actions (encrypts) and
word-games-tui (decrypts). Keep the two copies identical.

Format: MAGIC (4) | salt (16) | nonce (16) | ciphertext | tag (32)

* Keys: PBKDF2-HMAC-SHA256(password, salt) -> 32-byte encryption key + 32-byte MAC key
* Cipher: XOR with a keystream of HMAC-SHA256(enc_key, nonce || counter) blocks
  (HMAC used as a PRF in counter mode)
* Integrity: HMAC-SHA256(mac_key, MAGIC || salt || nonce || ciphertext), checked
  before decrypting (encrypt-then-MAC)

The goal is to keep the puzzle answers in the public data folder unreadable
without the password; it is not meant to protect anything more sensitive.
"""
import hashlib
import hmac
import os

MAGIC = b"WGC1"
ITERATIONS = 200_000
_SALT, _NONCE, _TAG = 16, 16, 32
_HEADER = len(MAGIC) + _SALT + _NONCE


def _keys(password: str, salt: bytes):
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, dklen=64)
    return key[:32], key[32:]


def _xor_keystream(key: bytes, nonce: bytes, data: bytes) -> bytes:
    blocks = (len(data) + 31) // 32
    stream = b"".join(
        hmac.new(key, nonce + i.to_bytes(8, "big"), hashlib.sha256).digest()
        for i in range(blocks)
    )[:len(data)]
    return (int.from_bytes(data, "big") ^ int.from_bytes(stream, "big")).to_bytes(len(data), "big")


def encrypt(data: bytes, password: str) -> bytes:
    salt, nonce = os.urandom(_SALT), os.urandom(_NONCE)
    enc_key, mac_key = _keys(password, salt)
    header = MAGIC + salt + nonce
    ciphertext = _xor_keystream(enc_key, nonce, data)
    tag = hmac.new(mac_key, header + ciphertext, hashlib.sha256).digest()
    return header + ciphertext + tag


def decrypt(blob: bytes, password: str) -> bytes:
    if len(blob) < _HEADER + _TAG or not blob.startswith(MAGIC):
        raise ValueError("Not an encrypted puzzle file")
    header, ciphertext, tag = blob[:_HEADER], blob[_HEADER:-_TAG], blob[-_TAG:]
    salt, nonce = header[len(MAGIC):len(MAGIC) + _SALT], header[len(MAGIC) + _SALT:]
    enc_key, mac_key = _keys(password, salt)
    expected = hmac.new(mac_key, header + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("Wrong password or corrupted file")
    return _xor_keystream(enc_key, nonce, ciphertext)
