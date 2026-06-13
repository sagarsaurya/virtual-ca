# ⚙️ Tech Stack

**← [[00 - Home]]**

---

## Frontend (ACTUAL — as of June 2026)

| Technology | Purpose |
|---|---|
| **React 18** (Create React App) | Main UI framework |
| **Tailwind CSS** (CDN) | Styling |
| **React Router v6** | Page routing |
| **axios** | API calls to Flask backend |
| **Font Awesome** | Icons |

**Build output:** `frontend/build/` — served by Flask as static files

---

## Backend (ACTUAL)

| Technology | Purpose |
|---|---|
| **Python Flask** | API server + static file serving |
| **pandas + openpyxl** | Excel/CSV parsing |
| **xml.etree** | Tally XML parsing |
| **Groq (Llama 3.3-70B)** | AI for Ask CA chat |
| **Supabase Python client** | Database calls |
| **PostgreSQL (Supabase)** | Main database |

---

## Infrastructure & Services (ACTUAL)

| Service | Purpose |
|---|---|
| **Render** | Full-stack hosting (Flask serves both API + React build) |
| **Supabase** | PostgreSQL database |
| **Razorpay** | Indian payment gateway (planned) |
| **GitHub** | Source code — https://github.com/sagarsaurya/virtual-ca |

---

## Frontend Structure

```
frontend/
  src/
    index.css          — CSS variables + global styles (dark navy + gold theme)
    index.js           — React entry point
    App.js             — Routes + PrivateLayout (auth guard)
    api/index.js       — All Flask API calls via axios (auto X-Company-ID header)
    components/
      Sidebar.jsx      — Nav sidebar with company switcher
      Header.jsx       — Top bar with page title
    pages/
      Login.jsx        — Login page
      Dashboard.jsx    — Home with scores + quick actions
      QuickAudit.jsx   — TB + Daybook upload → audit
      FullAudit.jsx    — 6-file full audit
      BankRec.jsx      — Bank reconciliation
      TDSAnalysis.jsx  — TDS section analysis
      Compliance.jsx   — GST/ITR compliance calendar
      AskCA.jsx        — AI chat with CA
      History.jsx      — Audit history
      Admin.jsx        — Admin stats
  build/               — Compiled output (committed to git, served by Flask)
```

---

## How Flask Serves React

```python
app = Flask(__name__, static_folder='frontend/build', static_url_path='')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    # Serves static files OR falls back to index.html for React Router
    ...
```

All `/api/*` routes are Flask endpoints. Everything else is React.

---

## Development Setup

```bash
# Backend
pip install flask flask-cors pandas openpyxl anthropic supabase
python app.py

# Frontend (only needed when editing React)
cd frontend
npm install
npm start          # dev server at localhost:3000 (proxies API to Flask)
npm run build      # compile to frontend/build/ for production
```

---

## Related Notes
- [[09 - Database Schema]]
- [[10 - API Endpoints]]
- [[17 - AI Integration (Claude API)]]
- [[16 - Build Phases & Roadmap]]
