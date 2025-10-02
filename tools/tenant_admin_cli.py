from __future__ import annotations

import os
import typer
from typing import Optional

from services.shared.key_service import create_key, rotate_key, revoke_key, list_keys
from services.shared import tenant_repo

app = typer.Typer(help="Admin CLI (DEV) para tenants e chaves. Usa DATABASE_URL.")


def _require_dev() -> None:
    env = os.getenv("ENV", "").strip().lower()
    flag = os.getenv("ADMIN_ROUTES_ENABLED", "").strip().lower()
    if env == "dev" or flag in {"1", "true", "yes", "on"}:
        return
    typer.secho("Admin CLI bloqueado fora de dev (use ENV=dev ou ADMIN_ROUTES_ENABLED=true)", fg=typer.colors.RED)
    raise typer.Exit(code=2)


@app.command("tenants-list")
def tenants_list() -> None:
    _require_dev()
    rows = tenant_repo.list_all_tenants()
    for r in rows:
        typer.echo(f"{r['tenant_id']}\t{r['name']}")


@app.command("keys-list")
def keys_list(tenant_id: str = typer.Argument(..., help="Tenant ID")) -> None:
    _require_dev()
    rows = list_keys(tenant_id)
    for r in rows:
        status = "revoked" if r.revoked_at else "active"
        typer.echo(f"{r.name}\t{status}")


@app.command("keys-create")
def keys_create(
    tenant_id: str = typer.Argument(..., help="Tenant ID"),
    name: Optional[str] = typer.Option(None, help="Nome amigável (opcional)"),
) -> None:
    _require_dev()
    name_out, api_key_plain = create_key(tenant_id, name=name)
    # MOSTRA apenas uma vez no terminal (não log persistente)
    typer.secho("==== API KEY GERADA ====", fg=typer.colors.GREEN)
    typer.echo(f"tenant: {tenant_id}")
    typer.echo(f"name:   {name_out}")
    typer.echo(f"key:    {api_key_plain}")


@app.command("keys-rotate")
def keys_rotate(
    tenant_id: str = typer.Argument(..., help="Tenant ID"),
    previous_name: Optional[str] = typer.Option(None, help="Nome da chave anterior (opcional)"),
    new_name: Optional[str] = typer.Option(None, help="Nome da nova chave (opcional)"),
) -> None:
    _require_dev()
    name_out, api_key_plain = rotate_key(tenant_id, previous_name=previous_name, new_name=new_name)
    typer.secho("==== API KEY ROTACIONADA ====", fg=typer.colors.GREEN)
    typer.echo(f"tenant: {tenant_id}")
    typer.echo(f"name:   {name_out}")
    typer.echo(f"key:    {api_key_plain}")


@app.command("keys-revoke")
def keys_revoke(
    tenant_id: str = typer.Argument(..., help="Tenant ID"),
    name: str = typer.Argument(..., help="Nome da chave a revogar"),
) -> None:
    _require_dev()
    n = revoke_key(tenant_id, name)
    if n == 0:
        typer.secho("Chave não encontrada ou já revogada.", fg=typer.colors.YELLOW)
    else:
        typer.secho("Chave revogada.", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
