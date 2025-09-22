-- Seed inicial de tenants
INSERT INTO tenants (id, name, api_key, status, created_at, updated_at)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'Dra. Camila', 'camila123', 'active',   CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('00000000-0000-0000-0000-000000000002', 'Oficina do Zé', 'zeoficina456', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;
