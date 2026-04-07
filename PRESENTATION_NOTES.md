# CIT Inventory — Backend Presentation Notes

This repo is the **Django + DRF backend** for the Laboratory Equipment Inventory.

If you’re presenting the full system (frontend + backend):
- Frontend repo: https://github.com/Saiganity1/3DES_FrontEnd

---

## What this backend does

- Provides a REST API for inventory management.
- Uses JWT authentication (SimpleJWT).
- Enforces role-based permissions (viewer vs staff vs admin).
- Encrypts sensitive item fields at rest (3DES).
- Provides a permission-gated decrypt endpoint.
- Records an activity/audit feed.

---

## Where things are

- Project settings: `inventory_backend/settings.py`
  - env vars, DB config (`DATABASE_URL`), CORS, DRF/JWT defaults
- Core models: `inventory/models.py`
  - Category, Item (encrypted fields), ActivityLog
- API behavior: `inventory/views.py`
  - ViewSets for accounts/categories/items/activity
  - Decrypt endpoint is permission-gated
- Serialization: `inventory/serializers.py`
- Permissions: `inventory/permissions.py`
- Auth helpers: `inventory/auth_views.py`, `inventory/auth_serializers.py`
- 3DES helpers: `inventory/crypto/triple_des.py`

---

## Security story (presentation)

- DB stores ciphertext in `*_encrypted` columns.
- Plaintext is produced only when:
  - staff/admin requests it, OR
  - a non-staff user is granted `inventory.can_decrypt_item_details` and uses the decrypt endpoint.

---

## Demo bootstrap helpers

- Default admin bootstrap:
  - `inventory/default_admin.py`
  - `inventory/middleware.py`
  - `inventory/management/commands/ensure_default_admin.py`
- Key generator:
  - `inventory/management/commands/generate_3des_key.py`
