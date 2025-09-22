from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class TenantInfo:
    id: str
    name: str
    api_key: str
    status: str


_current_tenant: ContextVar[TenantInfo | None] = ContextVar("current_tenant", default=None)


def set_current_tenant(t: TenantInfo | None) -> None:
    _current_tenant.set(t)


def get_current_tenant() -> TenantInfo | None:
    return _current_tenant.get()
