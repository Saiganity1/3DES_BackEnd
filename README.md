# CIT Inventory API (Django)

Backend API for the CIT Laboratory Equipment Inventory.

## Local run (Windows)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py generate_3des_key
# paste into .env as INVENTORY_3DES_KEY_B64=...
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

API base:
- `http://127.0.0.1:8000/api/`

## Deploy to Render

This repo includes `render.yaml` for a Render Blueprint.

On Render, set environment variables:
- `SECRET_KEY`
- `INVENTORY_3DES_KEY_B64`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- CORS: either allow-all (dev) or set `CORS_ALLOWED_ORIGINS`.

### Using Supabase Postgres (instead of Render Postgres)

1. Create a Supabase project and get the Postgres connection string.
2. In your Render backend service, set `DATABASE_URL` to the Supabase URL.

Notes:
- Supabase requires SSL. Include `?sslmode=require` in the URL, or set `DB_SSLMODE=require`.
- If you use the Supabase *pooler* host/port (often `pooler.supabase.com` or port `6543`), set `CONN_MAX_AGE=0` (or omit it; the backend defaults to `0` for Supabase poolers).

Example (format only — do not commit secrets):
`postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require`
