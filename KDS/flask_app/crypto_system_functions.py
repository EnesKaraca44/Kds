"""
Java'daki SystemFunctions (kısmi) Python uyarlaması.

Özellikle:
- sha256(text)                 -> hex lowercase SHA-256
- string_to_sha256(text)       -> hex lowercase SHA-256 (Java StringToSha256 ile uyumlu)
- encrypt_string_v2(text)      -> specialCharacterEncrypt + AES/CBC/PKCS5Padding + Base64

Notlar:
- AES için proje ortamında ya `pycryptodome` (Crypto.*) ya da `cryptography` paketi yüklü olmalı.
- PKCS5Padding, AES blok boyutu 16 olduğu için PKCS7 ile aynıdır.
"""

from __future__ import annotations

import base64
import hashlib
import re
from typing import Optional


# Java'daki sabitlerle birebir aynı (16 byte zorunluluğu var)
KEY_BYTES: bytes = b"my_ideal_way_mts"
IV_BYTES: bytes = b"metasoft_yazilim"

_ALNUM_RE = re.compile(r"^[a-zA-Z0-9]$")
_ESC_SEQ_RE = re.compile(r"~S(\d+)E~")


def sha256(text: str) -> str:
    """Guava Hashing.sha256().hashString(...).toString() ile uyumlu hex çıktısı."""
    if text is None:
        raise TypeError("text must not be None")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def string_to_sha256(sifre: Optional[str]) -> Optional[str]:
    """Java StringToSha256 ile uyumlu hex çıktısı (None -> None)."""
    if sifre is None:
        return None
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


def _is_letter_or_number(ch: str) -> bool:
    return bool(_ALNUM_RE.match(ch))


def _special_character_encrypt(text: Optional[str]) -> Optional[str]:
    """
    Java specialCharacterEncrypt ile aynı mantık:
    - [a-zA-Z0-9] dışındaki her karakteri '~S<ascii>E~' formatına çevirir.
    - null/""/"0" veya length==0 için None döner.
    """
    if text is None or text == "" or text == "0" or len(text) == 0:
        return None

    out: list[str] = []
    for ch in text:
        if _is_letter_or_number(ch):
            out.append(ch)
        else:
            out.append(f"~S{ord(ch)}E~")
    return "".join(out)


def _pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len


def _pkcs7_unpad(padded: bytes, block_size: int = 16) -> bytes:
    if not padded or (len(padded) % block_size) != 0:
        raise ValueError("Invalid padded data length")
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > block_size:
        raise ValueError("Invalid padding")
    if padded[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("Invalid padding")
    return padded[:-pad_len]


def _aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """
    AES/CBC şifreleme. Çıktı: raw ciphertext bytes.
    Önce pycryptodome dener, yoksa cryptography dener.
    """
    if len(key) != 16:
        raise ValueError("KEY_BYTES must be 16 bytes for AES-128 compatibility with Java code")
    if len(iv) != 16:
        raise ValueError("IV_BYTES must be 16 bytes for AES-CBC compatibility with Java code")

    padded = _pkcs7_pad(plaintext, 16)

    # 1) pycryptodome
    try:
        from Crypto.Cipher import AES  # type: ignore

        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return cipher.encrypt(padded)
    except Exception:
        pass

    # 2) cryptography
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # type: ignore
        from cryptography.hazmat.backends import default_backend  # type: ignore

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        return encryptor.update(padded) + encryptor.finalize()
    except Exception as e:
        raise ImportError(
            "AES encryption requires either `pycryptodome` or `cryptography` to be installed. "
            "Install one of them (e.g. `pip install pycryptodome` or `pip install cryptography`)."
        ) from e


def _aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    if len(key) != 16:
        raise ValueError("KEY_BYTES must be 16 bytes for AES-128 compatibility with Java code")
    if len(iv) != 16:
        raise ValueError("IV_BYTES must be 16 bytes for AES-CBC compatibility with Java code")

    # 1) pycryptodome
    try:
        from Crypto.Cipher import AES  # type: ignore

        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        padded = cipher.decrypt(ciphertext)
        return _pkcs7_unpad(padded, 16)
    except Exception:
        pass

    # 2) cryptography
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # type: ignore
        from cryptography.hazmat.backends import default_backend  # type: ignore

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        return _pkcs7_unpad(padded, 16)
    except Exception as e:
        raise ImportError(
            "AES decryption requires either `pycryptodome` or `cryptography` to be installed. "
            "Install one of them (e.g. `pip install pycryptodome` or `pip install cryptography`)."
        ) from e


def _special_character_decrypt(text: Optional[str]) -> Optional[str]:
    if text is None or text == "" or text == "0":
        return None

    def _repl(match: re.Match[str]) -> str:
        code = int(match.group(1))
        try:
            return chr(code)
        except ValueError:
            return match.group(0)

    return _ESC_SEQ_RE.sub(_repl, text)


def encrypt_string_v2(text: Optional[str]) -> Optional[str]:
    """
    Java encryptString_V2 ile uyumlu:
    - None/""/"0" => None
    - önce specialCharacterEncrypt
    - sonra AES/CBC/PKCS5Padding
    - Base64 çıktısı döner (string)
    """
    if text is None or text == "" or text == "0":
        return None

    escaped = _special_character_encrypt(text)
    if escaped is None:
        return None

    ciphertext = _aes_cbc_encrypt(KEY_BYTES, IV_BYTES, escaped.encode("utf-8"))
    return base64.b64encode(ciphertext).decode("ascii")


def decrypt_string_v2(encrypted_b64: Optional[str]) -> Optional[str]:
    """
    encrypt_string_v2'nin tersidir:
    - Base64 decode
    - AES/CBC/PKCS5(PKCS7) unpad
    - specialCharacterDecrypt
    """
    if encrypted_b64 is None or encrypted_b64 == "" or encrypted_b64 == "0":
        return None

    ciphertext = base64.b64decode(encrypted_b64)
    escaped_bytes = _aes_cbc_decrypt(KEY_BYTES, IV_BYTES, ciphertext)
    escaped_text = escaped_bytes.decode("utf-8")
    return _special_character_decrypt(escaped_text)


if __name__ == "__main__":
    # Mini smoke test (çıktı sabit bir değer olarak yazılmıyor; sadece çalıştığını doğrular)
    sample = "Meta26.soft"
    print("sha256:", sha256(sample))
    enc = encrypt_string_v2(sample)
    print("encrypt_string_v2:", enc)
    print("decrypt_string_v2:", decrypt_string_v2(enc))
