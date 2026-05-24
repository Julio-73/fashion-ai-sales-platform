# AI Sales Agent SaaS

Enterprise SaaS foundation for fashion businesses.

## Local Development

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env.local`.

No Docker is required for this foundation.

## Authentication

The auth foundation includes FastAPI endpoints for:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Frontend auth lives under `frontend/src/store/auth-store.tsx`, `frontend/src/services/auth.service.ts`, and `frontend/src/app/login/page.tsx`.
