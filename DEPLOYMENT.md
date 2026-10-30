# 🚢 ECHO WorkforceOS - Deployment & Environment Guide

This guide covers deployment options for **ECHO WorkforceOS**, ranging from zero-dependency local development to cloud production containers.

---

## 1. Environment Variable Reference

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `ENVIRONMENT` | Yes | `development` | Environment mode (`development`, `staging`, `production`). |
| `PORT` | Yes | `8000` | Backend API port. |
| `DATABASE_URL` | Yes | `sqlite:///./echo.db` | Connection URI. Falls back to SQLite if Supabase credentials absent. |
| `SUPABASE_URL` | No | - | Supabase Project URL. |
| `SUPABASE_SERVICE_ROLE_KEY` | No | - | Privileged Supabase backend API key. |
| `SUPABASE_ANON_KEY` | No | - | Client-safe Supabase anon key. |
| `JWT_SECRET` | Yes | - | Secret key used to sign access tokens. |
| `GROQ_API_KEY` | No | - | Groq LLM API Key for natural language reasoning. |
| `GEMINI_API_KEY` | No | - | Google Gemini API Key. |
| `OPENAI_API_KEY` | No | - | OpenAI API Key. |
| `ENABLE_EMAIL` | No | `false` | Enable live SMTP email dispatch (otherwise recorded in `email_outbox`). |
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000/api/v1` | Public backend URL exposed to Next.js browser bundle. |

---

## 2. Docker & Container Deployment

### Dockerfile (Backend API)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend/data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    depends_on:
      - backend
```

---

## 3. Production Cloud Deployment

### Vercel (Frontend Next.js App)
1. Import `frontend/` directory to Vercel.
2. Set Environment Variables:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend-domain.com/api/v1`
   - `NEXT_PUBLIC_ENABLE_REALTIME`: `true`
3. Deploy!

### Google Cloud Run / Railway (FastAPI Backend API)
1. Deploy `backend/` container using Dockerfile above.
2. Configure Environment Variables in Cloud Console.
3. Apply initial SQL schema (`database/schema.sql`) to Supabase / Managed PostgreSQL.
