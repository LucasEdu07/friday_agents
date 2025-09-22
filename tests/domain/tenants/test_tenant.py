import uuid
from datetime import datetime

from domain.tenants import Tenant, TenantStatus


def test_tenant_model_instantiation():
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Clinica Camila",
        api_key="camila123",
        status=TenantStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert tenant.name == "Clinica Camila"
    assert tenant.is_active() is True
