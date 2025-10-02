from __future__ import annotations

import os

from fastapi import HTTPException, status


def ensure_admin_enabled() -> None:
    """
    Bloqueia o uso de rotas /admin/* fora de ambiente de dev.

    Habilita se QUALQUER uma das condições for verdadeira:
      - ENV=dev
      - ADMIN_ROUTES_ENABLED=true (case-insensitive)
    """
    env = os.getenv("ENV", "").strip().lower()
    flag = os.getenv("ADMIN_ROUTES_ENABLED", "").strip().lower()
    if env == "dev" or flag in {"1", "true", "yes", "on"}:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin routes disabled in this environment",
    )
