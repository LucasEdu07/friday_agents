# services/shared/auth.py
from __future__ import annotations

import base64
import hashlib
from typing import Final

# Algoritmo suportado (mapeado ao campo `algo` da tabela)
ALGO_PBKDF2_SHA256: Final[str] = "pbkdf2_sha256"


def _pbkdf2_sha256(token: str, salt_b64: str, iterations: int) -> str:
    """
    Deriva o hash PBKDF2-HMAC-SHA256 do `token` usando `iterations` e `salt_b64`.
    Retorna o hash em Base64 (compatível com o campo `hash_b64`).
    """
    salt = base64.b64decode(salt_b64)
    dk = hashlib.pbkdf2_hmac("sha256", token.encode("utf-8"), salt, iterations)
    return base64.b64encode(dk).decode("ascii")


def verify_token(
    token: str,
    *,
    algo: str,
    iterations: int,
    salt_b64: str,
    hash_b64: str,
) -> bool:
    """
    Verifica se `token` corresponde ao par (algo, iterations, salt_b64, hash_b64).

    Hoje suportamos explicitamente `pbkdf2_sha256`, alinhado ao seu schema.
    Caso no futuro haja novos algoritmos (ex.: argon2), adicione aqui.
    """
    if algo != ALGO_PBKDF2_SHA256:
        # Algoritmo desconhecido: considere não-autorizado
        return False

    derived_b64 = _pbkdf2_sha256(token, salt_b64=salt_b64, iterations=iterations)
    # Comparação constante não é crítica aqui (já há PBKDF2), mas pode-se usar
    # secrets.compare_digest se preferir.
    return derived_b64 == hash_b64
