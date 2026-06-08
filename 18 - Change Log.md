# 📝 Change Log

**← [[00 - Home]]**

---

## 8 June 2026

### Bank Reconciliation — Major Upgrades

- ✅ **Closing Balance Comparison** — bank PDF closing balance vs Tally "Closing Balance" row shown as Step 1
  - Green banner when matched
  - Green banner + yellow warning when matched BUT issues exist (explains "cancelling errors" concept)
  - Red banner with diff amount when mismatch
  - Traces paise-level differences (e.g. ₹0.12) to the exact entry causing it
- ✅ **Wrong Date Detection** — entries that exist in Tally but with wrong date are separated from truly missing entries (cross-matched by amount)
- ✅ **5-tab layout** — Wrong Date (purple) | Missing in Tally | Extra in Tally | Duplicates | Matched
- ✅ **Smart Duplicate Detection** — Bank = zero duplicate detection (bank statements never have duplicates). Tally = only flags duplicate if Tally count > bank count for same date+amount (±1 day). Prevents false positives for legitimate same-party same-amount entries.
- ✅ **Amount Mismatch (paise) tracking** — shows exact matched entry where Tally entered less/more

### Ask Your CA — Complete Rebuild

- ✅ **Two-panel layout** replacing single chat panel:
  - **Left panel (55%)** — numbered queries auto-generated from audit data with severity badges, category tags, reply boxes
  - **Right panel (45%)** — live AI chat powered by Groq API
- ✅ **Query auto-generation** from audit result — ledger issues, cash violations, outstanding balances, large expenses, loans each become numbered queries
- ✅ **Query severity** — Critical (red border), Important (yellow border), Info (blue border)
- ✅ **Filter bar** — All / Critical / Pending / Done
- ✅ **Reply to query** — user types reply → AI acknowledges → query marked resolved (green)
- ✅ **Ask CA about query** — 💬 button on each query pre-fills chat with that specific issue
- ✅ **Re-analyse button** — rebuilds queries from latest audit data
- ✅ **Clear chat button** — resets chat, shows fresh greeting

### AI Integration — Switched to Groq API

- ✅ **New file: `ca_agent.py`** — Groq API integration (replaces prototype hardcoded responses)
  - Model: `llama-3.3-70b-versatile`
  - Builds rich context from last audit result (ledgers, violations, outstanding, loans, large expenses)
  - Maintains conversation history (last 10 turns per session)
  - System prompt: senior Indian CA persona, specific data-driven answers, Tally journal entry format
- ✅ **New endpoint: `POST /api/ca-chat`** — accepts message + history, returns AI reply
- ✅ **New file: `.env`** — local API key storage
- ✅ **`requirements.txt` updated** — added `groq`, `python-dotenv`
- ✅ **Dynamic greeting** — on page load, AI greeting shows real company name, period, score, issue counts from uploaded data (no more hardcoded AJKL text)
- ✅ **Context banner** replaced with header subtitle showing real audit data

---

## 15 March 2026

### Prototype Updates — Major
- ✅ Added **Fix Workflow** to Results page
  - Status: Open / In Progress / Resolved / Ignored
  - Assign to team member
  - Add comment thread
  - Mark Resolved with timestamp
- ✅ Added **Fix Workflow Status Bar** (Open / InProgress / Resolved / Ignored counts)
- ✅ Added **UX toolbar** — colour legend, FY filter, sort by, download report (PDF/Excel/CSV)

### Upload System
- ✅ **5 file type tabs**: Excel Trial Balance, Tally XML, Ledger Dump, Bank Statement, GST JSON
- ✅ **Data Mapping Screen** after upload
- ✅ **Chart of Accounts Mapping** — custom group → standard Tally group

### New Modules
- ✅ **Bank Reconciliation Module** — upload 2 files, auto-match, Unmatched/Tally Only/Duplicates/Matched tabs
- ✅ **TDS Analysis Page** — section-wise (194C/194J/194I/192), late interest calculator, 26AS mismatch table
- ✅ **PT Analysis Section (Kolkata/WB)** — WB slabs, employee-wise PT, journal entries, Grips steps

### AI Chat
- ✅ **Contextual AI banner** — "Data Connected" with file name + error count
- ✅ **Pre-loaded contextual Q&A** — Why is profit low? → data-specific answer
- ✅ **5 quick-ask chips** — context-aware, pre-filled and auto-send

### Error Cards
- ✅ **Ledger Drill-Down modal** — transaction history + voucher details
- ✅ **Export to Tally modal** — XML / Excel / CSV with import instructions
- ✅ **Error Explanation Panel** — why error occurred + accounting rule violated
- ✅ **Auto-Correction Journal Entry** on each error card

### Documentation
- ✅ Created full `LOG.md` — complete technical build log
- ✅ Created `VirtualCA_Product_Overview.docx` — client-facing Word document
- ✅ Created Obsidian vault — 18 structured notes with wikilinks

---

## 14 March 2026

### Initial Build
- ✅ Created full UI prototype (`prototype.html` → renamed `index.html`)
- ✅ 8 pages: Login, Dashboard, Upload, Results, History, Ask CA, Journal Guide, Compliance
- ✅ Created `LOG.md` with initial product documentation
- ✅ Created `analyzer.py` — Python script for Excel analysis logic

---

## Upcoming (Phase 2)

- [ ] Convert prototype to React 18 app
- [ ] FastAPI backend with all endpoints
- [ ] Real Excel parser with pandas
- [ ] PostgreSQL database setup
- [ ] JWT auth
- [ ] Claude API live integration
- [ ] Deploy to Vercel + Railway

See [[16 - Build Phases & Roadmap]]
