from __future__ import annotations

import json
import os
from typing import Any

import typer

from services.shared.key_service import create_key, list_keys, revoke_key, rotate_key
from services.shared.tenant_repo import list_all_tenants

app = typer.Typer(help="Tenant admin CLI (dev only).")


def _ensure_dev() -> None:
    """Garante que só roda em ambiente dev, senão aborta."""
    if os.getenv("ENV") not in {"dev", "development", "local"}:
        typer.echo("This CLI is only allowed in ENV=dev.")
        raise typer.Exit(1)


@app.command("tenants-list")
def tenants_list() -> None:
    """Lista tenants que possuem pelo menos uma API key ativa."""
    _ensure_dev()
    rows = list_all_tenants()
    typer.echo(json.dumps(rows, indent=2, ensure_ascii=False))


@app.command("keys-list")
def keys_list(tenant_id: str = typer.Argument(..., help="Tenant ID")) -> None:
    """Lista chaves ativas de um tenant."""
    _ensure_dev()
    rows = list_keys(tenant_id)
    typer.echo(json.dumps(rows, indent=2, ensure_ascii=False))


@app.command("keys-create")
def keys_create(
    tenant_id: str = typer.Argument(..., help="Tenant ID"),
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="Nome da chave (opcional; será gerado se não informado).",
    ),
) -> None:
    """Cria uma nova chave para o tenant."""
    _ensure_dev()
    created_name, api_key_plain = create_key(tenant_id, name=name)
    out: dict[str, Any] = {
        "tenant_id": tenant_id,
        "name": created_name,
        "api_key_plain": api_key_plain,
    }
    typer.echo(json.dumps(out, indent=2, ensure_ascii=False))


@app.command("keys-rotate")
def keys_rotate(
    tenant_id: str = typer.Argument(..., help="Tenant ID"),
    previous_name: str | None = typer.Option(
        None, "--previous-name", help="Nome da chave anterior a ser revogada."
    ),
    new_name: str | None = typer.Option(
        None, "--new-name", help="Nome da nova chave (opcional)."
    ),
) -> None:
    """Rotaciona chave: revoga a anterior e cria uma nova."""
    _ensure_dev()
    created_name, api_key_plain = rotate_key(
        tenant_id, previous_name=previous_name, new_name=new_name
    )
    out: dict[str, Any] = {
        "tenant_id": tenant_id,
        "name": created_name,
        "api_key_plain": api_key_plain,
    }
    typer.echo(json.dumps(out, indent=2, ensure_ascii=False))


@app.command("keys-revoke")
def keys_revoke(
    tenant_id: str = typer.Argument(..., help="Tenant ID"),
    name: str = typer.Option(..., "--name", "-n", help="Nome da chave a revogar."),
) -> None:
    """Revoga uma chave ativa do tenant."""
    _ensure_dev()
    n = revoke_key(tenant_id, name)
    out = {"tenant_id": tenant_id, "revoked": int(n)}
    typer.echo(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
