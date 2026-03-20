import base64
import os
from dataclasses import dataclass
from typing import Optional

from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


@dataclass(frozen=True)
class TripleDESEncrypted:
    """Stored format: base64(iv + ciphertext).

    - IV is 8 bytes (DES block size)
    - Ciphertext is PKCS7 padded
    """

    b64: str


class TripleDESConfigError(RuntimeError):
    pass


_BLOCK_SIZE = 8


def _get_key() -> bytes:
    """Get a 24-byte 3DES key from env var INVENTORY_3DES_KEY_B64.

    Provide it as base64 of 24 random bytes.
    """

    key_b64 = os.getenv("INVENTORY_3DES_KEY_B64", "").strip()
    if not key_b64:
        raise TripleDESConfigError(
            "Missing INVENTORY_3DES_KEY_B64. Generate one with: "
            "python manage.py generate_3des_key"
        )

    try:
        raw = base64.b64decode(key_b64)
    except Exception as exc:  # noqa: BLE001
        raise TripleDESConfigError("INVENTORY_3DES_KEY_B64 is not valid base64") from exc

    if len(raw) != 24:
        raise TripleDESConfigError(
            f"INVENTORY_3DES_KEY_B64 must decode to 24 bytes, got {len(raw)}"
        )

    # DES3 keys must have correct parity; adjust_key_parity will fix if needed.
    try:
        return DES3.adjust_key_parity(raw)
    except ValueError as exc:
        raise TripleDESConfigError(
            "Invalid 3DES key (failed parity adjustment). Generate a fresh key."
        ) from exc


def encrypt_text(plaintext: Optional[str]) -> Optional[str]:
    if plaintext is None:
        return None

    text = plaintext.strip()
    if text == "":
        return ""

    key = _get_key()
    iv = get_random_bytes(_BLOCK_SIZE)
    cipher = DES3.new(key, DES3.MODE_CBC, iv=iv)
    ct = cipher.encrypt(pad(text.encode("utf-8"), _BLOCK_SIZE))
    return base64.b64encode(iv + ct).decode("ascii")


def decrypt_text(b64_ciphertext: Optional[str]) -> Optional[str]:
    if b64_ciphertext is None:
        return None

    text = b64_ciphertext.strip()
    if text == "":
        return ""

    key = _get_key()
    try:
        raw = base64.b64decode(text)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Encrypted value is not valid base64") from exc

    if len(raw) < _BLOCK_SIZE:
        raise ValueError("Encrypted value is too short")

    iv, ct = raw[:_BLOCK_SIZE], raw[_BLOCK_SIZE:]
    cipher = DES3.new(key, DES3.MODE_CBC, iv=iv)
    pt = unpad(cipher.decrypt(ct), _BLOCK_SIZE)
    return pt.decode("utf-8")
