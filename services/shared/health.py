from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Literal, cast

from pydantic import BaseModel

Status = Literal["ok", "fail"]


class ProbeStatus(BaseModel):
    status: Status = "ok"
    service: str
    checks: dict[str, bool] | None = None


CheckFn = Callable[[], bool] | Callable[[], Awaitable[bool]]


class HealthChecker:
    """
    Helper simples para padronizar /health e /readiness nos serviços.
    - /health: sempre 200 OK (processo vivo).
    - /readiness: 200 OK se todos os checks passarem; 503 se algum falhar, com detalhes.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._checks: dict[str, CheckFn] = {}

    def register(self, name: str, fn: CheckFn) -> None:
        self._checks[name] = fn

    async def _run_check(self, fn: CheckFn) -> bool:
        res = fn()
        if inspect.isawaitable(res):
            return bool(await cast(Awaitable[bool], res))
        return bool(res)

    async def health(self) -> ProbeStatus:
        return ProbeStatus(status="ok", service=self.service_name)

    async def readiness(self) -> tuple[bool, ProbeStatus]:
        results: dict[str, bool] = {}
        all_ok = True
        for name, fn in self._checks.items():
            ok = False
            try:
                ok = await self._run_check(fn)
            except Exception:
                ok = False
            results[name] = bool(ok)
            all_ok = all_ok and ok
        status: Status = "ok" if all_ok else "fail"
        return all_ok, ProbeStatus(status=status, service=self.service_name, checks=results)
