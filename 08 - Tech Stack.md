# ⚙️ Tech Stack

**← [[00 - Home]]**

---

## Frontend

| Technology | Purpose |
|---|---|
| **React 18** (Vite) | Main UI framework |
| **Tailwind CSS v3** | Styling |
| **React Router v6** | Page routing |
| **Zustand** | State management |
| **Recharts** | Dashboard charts |
| **TanStack Query** | API calls + caching |
| **Font Awesome** | Icons |

---

## Backend

| Technology | Purpose |
|---|---|
| **Python FastAPI** | API server (chosen for pandas/Excel support) |
| **pandas + openpyxl** | Excel/CSV parsing |
| **xml.etree** | Tally XML parsing |
| **Anthropic Python SDK** | Claude AI for chat |
| **SQLAlchemy + Alembic** | ORM + database migrations |
| **PostgreSQL** | Main database |
| **Redis** | Session cache + job queue |
| **Celery** | Async file processing jobs |
| **AWS S3 / Cloudflare R2** | File storage |
| **JWT** | Auth tokens |

---

## Infrastructure & Services

| Service | Purpose |
|---|---|
| **Vercel** | React frontend hosting |
| **Railway or Render** | FastAPI backend hosting |
| **Supabase** | PostgreSQL + Auth (optional) |
| **Resend** | Transactional email |
| **Razorpay** | Indian payment gateway |

---

## Why FastAPI (not Node)?

- pandas is Python — best for Excel/CSV file processing
- openpyxl for writing Excel correction sheets
- xml.etree for Tally XML parsing
- Anthropic Python SDK is first-class
- FastAPI is fast, async, auto-generates API docs

---

## Development Setup (Phase 2)

```
Frontend:  npm create vite@latest → React + TypeScript
Backend:   pip install fastapi uvicorn pandas openpyxl anthropic sqlalchemy
Database:  PostgreSQL on Supabase (free tier for MVP)
Storage:   Cloudflare R2 (free 10GB, cheap after)
Deploy:    Vercel (frontend) + Railway (backend)
```

---

## Related Notes
- [[09 - Database Schema]]
- [[10 - API Endpoints]]
- [[17 - AI Integration (Claude API)]]
- [[16 - Build Phases & Roadmap]]
