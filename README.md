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
- `DATABASE_URL` (Render Postgres recommended)
- CORS: either allow-all (dev) or set `CORS_ALLOWED_ORIGINS`.
