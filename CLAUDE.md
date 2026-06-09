# CLAUDE.md — VirtualCA Project Briefing
> Read this FIRST every session. This is the single source of truth.
> Last updated: June 2026 | Owner: Sagar Pathak, Kolkata

---

## What Is VirtualCA?
AI-powered Tally accounting audit SaaS for Indian SMBs and CA firms.
Upload your Tally Trial Balance + Daybook → get full audit, compliance alerts, TDS analysis, bank reconciliation in 30 seconds.

**One-line pitch:** *"Upload your Tally file. Get a full audit in 30 seconds."*

---

## Current Status: LIVE on Render ✅
- **Live URL:** https://virtual-ca.onrender.com
- **GitHub:** https://github.com/sagarsaurya/virtual-ca
- **Deploy:** Push to `main` → Render auto-deploys in ~2 minutes
- **Stack:** Flask (Python) backend + single-file HTML/CSS/JS frontend
- **AI:** Groq API (Llama 3.3 70B) via `ca_agent.py`

---

## Project Folder
```
C:\Users\sagar\Downloads\virtualca\
```

### Key Files
```
index.html          → Complete UI — ALL pages (single file, ~4500 lines)
app.py              → Flask backend — all API endpoints
audit_engine.py     → Core audit logic — ALL 9 modules
ca_agent.py         → AI CA chat — Groq API, build_context()
bank_recon.py       → Bank reconciliation engine
compliance.py       → Compliance calendar logic
LOG.md              → Build history (older)
CLAUDE.md           → THIS FILE
```

---

## Tech Stack (CONFIRMED — DO NOT CHANGE)
| Layer | Technology |
|---|---|
| Backend | Python + Flask |
| Frontend | Pure HTML + Tailwind CDN + Vanilla JS (single file) |
| Styling | Dark theme — navy-900 (#070E1A) base |
| AI Chat | Groq API — `llama-3.3-70b-versatile` |
| Deploy | Render (free tier — spins down after 15 min idle) |
| Version Control | GitHub |

---

## Color Theme (LOCKED — never change)
```css
--navy-900: #070E1A   /* page background */
--navy-800: #0D1B2E   /* cards */
--navy-700: #132640   /* inner panels, table rows */
--navy-600: #1A3352   /* borders */
--navy-500: #1E3A5F   /* subtle borders */
--gold-500: #C9A84C   /* accent */
```
**Rule:** NEVER use white/cream backgrounds. All cards = navy-800. All inner panels = navy-700.

---

## All Pages (Nav Structure)
| Nav Item | Page ID | Status |
|---|---|---|
| Dashboard | `dashboard` | ✅ Working |
| History | `history` | ✅ Working |
| Bank Reconciliation | `bankrecon` | ✅ Working |
| Full Audit | `askca` | ✅ Working (renamed from Upload & Analyse) |
| TDS Analysis | `tdsanalysis` | ✅ Working |
| Compliance Calendar | `compliance` | ✅ Working |
| Ask Your CA | `chat` (right panel) | ✅ Working |
| Journal Entry Guide | `journal` | ✅ Working |
| Admin Panel | `admin` | ✅ Working |

---

## Audit Engine — 9 Modules (`audit_engine.py`)
All 9 run via `run_full_audit(tb_path, db_path)`:

| Module | Function | What it does |
|---|---|---|
| 1 | `audit_ledger_classification()` | 20+ rules — wrong group in Chart of Accounts |
| 2 | `audit_outstanding_balances()` | Abnormal balances, suspense, debtors with credit |
| 3 | `audit_cash_violations()` | Cash payments >₹10,000 — Sec 40A(3) |
| 4 | `audit_itr()` | Personal expenses in business books |
| 5 | `audit_large_expenses()` | Payments >₹1L — bill + TDS check |
| 6 | `audit_loans()` | Director loans, undocumented loans |
| 7 | `audit_bank_accounts()` | 3-pass bank detection (TB group → TB name → daybook) |
| 8 | `audit_tds_compliance()` | Section-wise TDS deduction check |
| 9 | `audit_salary_compliance()` | PF/PT/salary structure issues |

### Critical Rules for `audit_bank_accounts()` (Module 7)
- **3-pass detection:** Pass 1 = TB group "Bank Accounts"/"Bank OD A/c", Pass 2 = TB name scan, Pass 3 = Daybook scan (Payment/Receipt/Contra vouchers)
- **Daybook column is `Particulars`** — NOT `party` (fixed June 2026)
- **`txn_list`** must be passed — NOT `transactions` (was causing NameError → 0 issues bug, fixed June 2026)
- **`NOT_A_BANK` list** excludes: credit card, debit card, fund, loan, tax, tds, insurance, etc.
- **Case-insensitive TB balance lookup** — uses `tb_balance_ci` fallback (fixed June 2026)

---

## CA Queries System (Frontend — `index.html`)
- `buildCAQueries(data)` — converts audit results into numbered query cards (#1, #2...)
- `caQueries[]` global array — all query cards with status (pending/resolved)
- `renderCAQueries()` — renders filtered query cards
- Each card has: Reply input → marks done, or sends to AI chat
- `askAboutQuery(id)` — sends query context to AI chat panel

### Query categories built:
1. LEDGER — mis-classification issues
2. BALANCE — abnormal/outstanding balances
3. PERSONAL · ITR — personal expenses in books
4. TDS · BILL — large payments needing TDS check
5. LOAN — undocumented loans
6. BANK STMT — bank accounts needing reconciliation
7. TDS · SEC 194X — TDS compliance violations
8. SALARY — PF/PT compliance

---

## AI Chat (`ca_agent.py`) — IMPORTANT RULES
- Uses **Groq API** (NOT Anthropic/Claude API) — model: `llama-3.3-70b-versatile`
- `build_context(audit_data)` builds text context sent to AI
- **Large expenses are grouped by party** (fixed June 2026) — AI sees total per party, NOT raw rows
  - Before fix: AI was recalculating and getting wrong totals (e.g., ₹12L instead of ₹14.9L)
  - After fix: AI receives pre-grouped totals, told to NOT recalculate
- Context includes: company info, score, ledger issues, cash violations, outstanding, large expenses (grouped), TDS, salary, bank accounts, loans

---

## Bank Reconciliation (`bank_recon.py` + frontend)
- Upload: Bank Statement (PDF/CSV/Excel) + Tally Bank Ledger (Excel)
- Engine: matches by amount+date, finds: wrong date, missing in Tally, extra in Tally, duplicates
- Closing balance check: compares bank vs Tally closing balance
- Frontend: 5 tabs — Wrong Date | Missing in Tally | Extra in Tally | Duplicates | Matched

---

## Dark Mode (CSS) — GLOBAL OVERRIDE BLOCK
Added to `index.html` `<style>` section after tokens (June 2026):
```css
/* kills ALL Tailwind white/gray utility classes */
.bg-white { background: var(--navy-800) !important; color: #e2e8f0; }
.bg-gray-50 { background: var(--navy-700) !important; }
.bg-gray-100 { background: var(--navy-700) !important; }
.text-gray-800 { color: #e2e8f0 !important; }
/* etc. */
```
**Rule:** JS-generated HTML with hardcoded `bg-green-50`/`bg-red-50` etc. CANNOT be caught by CSS classes — must use inline `style=` with navy variables.

---

## Data Flow (Full Audit)
```
User uploads TB (.xlsx) + Daybook (.xlsx)
    ↓
POST /api/audit → app.py → run_full_audit()
    ↓
audit_engine.py runs all 9 modules
    ↓
Returns JSON: { summary, ledger_classification, cash_violations, 
                outstanding, itr, large_expenses, loans, 
                bank_accounts, tds_compliance, salary_compliance }
    ↓
Frontend: renderAuditResults(data)
    → buildCAQueries(data) → caQueries[]
    → renderTDSPage(data)
    → renderSalaryCompliance(data)
    → _renderPTSummary(data.salary_compliance)
```

---

## TDS Analysis Page (`tdsanalysis`)
- Populated by `renderTDSPage(auditData)` — called from `renderAuditResults()`
- Also re-renders when navigating via `showPage('tdsanalysis')`
- PT stat cards: `id="pt-total-deducted"` and `id="pt-emp-count"` — dynamic
- PT table: `id="pt-employee-table"` — populated by `renderSalaryCompliance()`

---

## Score System
- Audit score 0–100 based on issues found
- Score 0 + 0 issues = CORRECT behaviour on genuinely bad data days (do NOT "fix" this)
- Score calculated in `run_full_audit()` → deductions per issue severity

---

## Trial Balance Parsing (`parse_trial_balance()`)
- Reads `.xlsx` with no header
- Detects group rows vs ledger rows by indentation/structure
- `GROUP_NAMES` includes: Bank Accounts, Bank OD A/c, Sundry Debtors, Sundry Creditors, etc.
- `balance = debit - credit` for each ledger
- **NEVER use `auto_adjust=True` for yfinance** (not relevant here, carried from TradeIQ)

---

## Bugs Fixed This Session (June 2026)
1. **0 issues bug** — `run_full_audit` used undefined `transactions` variable → NameError → 0 results. Fixed: pass `txn_list = daybook.to_dict('records')`
2. **Wrong daybook column** — `audit_bank_accounts` used `txn.get('party')` but daybook has `Particulars`. Fixed.
3. **Credit cards in bank list** — added `credit card`, `debit card`, `fund`, `prudential` etc. to `NOT_A_BANK`
4. **₹0 bank balances** — case-insensitive `tb_balance_ci` lookup added for daybook-discovered banks
5. **AI wrong totals** — `build_context()` sent raw rows; AI recalculated wrong. Fixed: send grouped party totals with NOTE to not recalculate
6. **All white backgrounds** — added global CSS override block; JS-generated banners fixed with inline styles
7. **Bank Reconciliation closing balance** — hardcoded `bg-green-50`/`bg-red-50` inline → fixed to navy inline styles
8. **`_aTd()` invisible text** — `color:var(--ink)` (dark on dark) → `color:#e2e8f0`
9. **TDS page no data** — `renderTDSPage()` never called from `renderAuditResults()`. Fixed.
10. **PT hardcoded demo data** — replaced with dynamic `id="pt-employee-table"` populated from audit

---

## What's Next (Priority Order)
1. **Bank balance from TB** — verify why all detected banks show ₹0 (may be genuine year-end zero or TB name mismatch still)
2. **Compliance Calendar** — connect to real dates based on uploaded FY period
3. **History page** — save past audits to disk/DB, load previous results
4. **Export to Excel** — download audit results as formatted .xlsx report
5. **Multi-company support** — login, company switcher
6. **Supabase migration** — move from file-based to DB-backed (when scaling)
7. **PT analysis** — West Bengal slab calculator from salary data
8. **Cash flow statement** — derive from daybook
9. **Tally XML import** — accept `.xml` export in addition to `.xlsx`

---

## How To Run Locally
```bash
cd C:\Users\sagar\Downloads\virtualca
pip install flask pandas openpyxl groq nsepython
python app.py
```
Open: http://localhost:5000

## How To Deploy
```bash
cd C:\Users\sagar\Downloads\virtualca
git add .
git commit -m "your message"
git push
```
Render auto-deploys in ~2 minutes.

---

## Environment Variables (Render)
```
GROQ_API_KEY=your_groq_key_here
```

---

## Rules For Claude (Read Every Session)
1. This is Flask + single HTML file — NOT Next.js (old plan abandoned)
2. Color theme is LOCKED: navy-900/800/700 — never use white/cream backgrounds
3. JS-generated HTML strings need inline `style=` with navy vars — CSS classes won't reach them
4. `Particulars` is the daybook party column — NOT `party`
5. `txn_list` (not `transactions`) must be passed to `audit_bank_accounts()`
6. `build_context()` in `ca_agent.py` must pass grouped totals — not raw rows
7. Score 0 + 0 issues on bad data = correct, don't "fix"
8. `renderTDSPage()` must be called from both `renderAuditResults()` AND `showPage('tdsanalysis')`
9. Always check JS template literals for hardcoded light colors — they bypass CSS overrides
10. Push to GitHub after every fix — Render auto-deploys
11. **AUTONOMOUS RULE (PERMANENT):** For ANY audit logic issue — wrong rule, missing check, incorrect law reference, new compliance requirement — DO NOT ask Sagar. He is not the accounting expert. Use WebSearch to find the correct Indian law/act/section, verify it, then implement the fix directly. Sagar's job is product decisions only.
12. TB parser uses INDENTATION to detect groups vs ledgers (not a hardcoded list) — `raw != name` means indented = ledger
13. Every audit finding must include a `law` field citing the specific section/act (e.g. "Sec 43B(h) IT Act")

---
*Owner: Sagar Pathak | Built with Claude | June 2026*
