import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TenantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class Tenant:
    id: uuid.UUID
    name: str
    api_key: str
    status: TenantStatus
    created_at: datetime
    updated_at: datetime

    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE
