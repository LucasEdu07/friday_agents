# services/shared/api_keys.py
from __future__ import annotations

import base64
import os
import secrets
from dataclasses import dataclass
from hashlib import pbkdf2_hmac
from typing import Final

# Parâmetros de derivação (seguros e rápidos o bastante p/ API)
ALG: Final[str] = "sha256"
ITERATIONS: Final[int] = 120_000
SALT_BYTES: Final[int] = 16
DKLEN: Final[int] = 32


@dataclass(frozen=True)
class KeyHash:
    """Representa um hash de API key armazenável no DB."""

    salt_b64: str
    hash_b64: str

    def as_db_tuple(self) -> tuple[str, str]:
        return self.salt_b64, self.hash_b64


def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def derive_key(secret: str, salt: bytes) -> bytes:
    """Deriva o hash da chave com PBKDF2-HMAC-SHA256."""
    return pbkdf2_hmac(ALG, secret.encode("utf-8"), salt, ITERATIONS, dklen=DKLEN)


def hash_key(plain_api_key: str) -> KeyHash:
    """Gera salt aleatório e retorna (salt_b64, hash_b64)."""
    salt = os.urandom(SALT_BYTES)
    dk = derive_key(plain_api_key, salt)
    return KeyHash(salt_b64=_b64e(salt), hash_b64=_b64e(dk))


def verify_key(plain_api_key: str, salt_b64: str, hash_b64: str) -> bool:
    """Verifica a API key contra (salt_b64, hash_b64) com comparação constante."""
    try:
        salt = _b64d(salt_b64)
        expected = _b64d(hash_b64)
        candidate = derive_key(plain_api_key, salt)
        return secrets.compare_digest(candidate, expected)
    except Exception:
        return False
