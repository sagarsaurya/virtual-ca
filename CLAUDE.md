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
| 7 | `audit_bank_accounts()` | 2-pass bank detection (TB group → daybook behavior) |
| 8 | `audit_tds_compliance()` | Section-wise TDS deduction check |
| 9 | `audit_salary_compliance()` | PF/PT/salary structure — voucher-level analysis |

---

## TB Parser (`parse_trial_balance()`) — CRITICAL — READ CAREFULLY

### Two-Level Group Hierarchy (LOCKED — confirmed working June 2026)
Tally's Chart of Accounts has two levels. The parser now handles BOTH condensed exports
(group totals only) AND detailed exports (individual sub-ledgers).

**Level 1 — Top-level groups** (set parent context, never added as ledger):
```
Capital Account, Loans (Liability), Fixed Assets, Investments,
Current Assets, Current Liabilities,
Direct Incomes, Indirect Incomes, Sales Accounts,
Direct Expenses, Indirect Expenses, Purchase Accounts,
Stock-in-Hand, Branch / Divisions, Reserves & Surplus,
Profit & Loss A/c, Misc. Expenses (Asset)
```

**Level 2 — Sub-groups** (added as ledger under Level 1 if they have a balance,
then `current_group` RESETS back to Level 1):
```
Duties & Taxes, Sundry Creditors, Sundry Debtors,
Cash-in-Hand, Bank Accounts, Bank OD A/c,
Loans & Advances (Asset), Deposits (Asset),
Suspense A/c, Suspense
```

**Everything else** = ledger → assigned to `current_group` (Level 1 or Level 2).

### Why This Matters
- Prevents `Advance to Staff` falling under `[Bank Accounts]` ← was a bug
- Prevents `Suspense Account` falling under `[Sundry Creditors]` ← was a bug
- `current_level1` tracks the last Level 1 group seen as a fallback

### Key Variables in Parser
```python
current_group  = None   # most recent group (Level 1 or Level 2)
current_level1 = None   # most recent Level 1 group (fallback)
```

---

## Bank Detection (`audit_bank_accounts()`) — 2-Pass System

### Pass 1 — TB Group
- Look for ledgers with `group` = "Bank Accounts" or "Bank OD A/c"
- These come from the parser assigning Level 2 group "Bank Accounts" → stored under Level 1 "Current Assets"
- The ledger row named "Bank Accounts" with its Dr balance IS a bank account

### Pass 2 — Daybook Behaviour
- Count appearances in Payment / Receipt / Contra vouchers (column = `Particulars`)
- If count ≥ 3 → probable bank account
- Excludes: keywords in `DEFINITELY_NOT_BANK` list (advance, staff, tds, gst, tax, deposit, loan, etc.)
- Excludes: already found in Pass 1

**CONFIRMED WORKING on D2D data:**
- Pass 1 found: `Bank Accounts` (Dr 36,876)
- Pass 2 found: `Kotak Mahindra Bank - A/C.No.2249417755` (412 txns in daybook)
- `_misclassified_as_bank: []` — zero false positives ✓

---

## PT / Salary Compliance (`audit_salary_compliance()`) — Voucher-Level

### How it works
1. Scans every salary voucher in daybook
2. Finds salary payment amount (Debit on salary ledger)
3. Checks if PT Credit entry exists in same voucher (`_vid`)
4. Calculates expected PT using WB slabs
5. Tracks PT payment to govt (keywords: Grips, WBIFMS, Professional Tax Govt)

### Outputs
- `pt_not_deducted` — month-by-month shortfall (Critical)
- `pt_not_paid_govt` — deducted but not deposited to government (Critical)
- `pt_deducted_ok` — confirmation of correct deduction (Info)
- `pt_paid_govt_ok` — confirmation of correct govt payment (Info)

### WB PT Slabs (West Bengal — Sagar's base state)
| Monthly Salary | Monthly PT |
|---|---|
| ≤ ₹10,000 | ₹0 |
| ₹10,001–₹15,000 | ₹110 |
| ₹15,001–₹25,000 | ₹130 |
| ₹25,001–₹40,000 | ₹150 |
| > ₹40,000 | ₹200 |

---

## Daybook Parser (`parse_daybook()`) — Key Rules

### VchType Propagation (CRITICAL)
Continuation rows in a voucher have blank VchType. The parser propagates
the parent voucher's type to ALL rows in that voucher:
```python
current_vtype = ''
for _, row in df.iterrows():
    vt = str(row['VchType']).strip()
    if vt in VOUCHER_TYPES:
        vid += 1
        current_vtype = vt
    vtypes_prop.append(current_vtype)  # every row gets a type
```

### Column = `Particulars` (NOT `party`)
The daybook's ledger/party column is always named `Particulars`.

### `_vid` Column
Added during parse — groups all rows of the same voucher together.
Used for PT voucher-level analysis.

---

## CA Queries System (Frontend — `index.html`)
- `buildCAQueries(data)` — converts audit results into numbered query cards (#1, #2...)
- `caQueries[]` global array — all query cards with status (pending/resolved)
- `renderCAQueries()` — renders filtered query cards
- Each card has: Reply input → marks done, or sends to AI chat
- `askAboutQuery(id)` — sends query context to AI chat panel

### Query categories:
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
- **Large expenses are grouped by party** — AI sees total per party, NOT raw rows
- Context includes: company info, score, ledger issues, cash violations, outstanding,
  large expenses (grouped), TDS, salary, bank accounts, loans

---

## Bank Reconciliation (`bank_recon.py` + frontend)
- Upload: Bank Statement (PDF/CSV/Excel) + Tally Bank Ledger (Excel)
- Engine: matches by amount+date, finds: wrong date, missing in Tally, extra in Tally, duplicates
- Closing balance check: compares bank vs Tally closing balance
- Frontend: 5 tabs — Wrong Date | Missing in Tally | Extra in Tally | Duplicates | Matched

---

## Dark Mode (CSS) — GLOBAL OVERRIDE BLOCK
Added to `index.html` `<style>` section after tokens:
```css
/* kills ALL Tailwind white/gray utility classes */
.bg-white { background: var(--navy-800) !important; color: #e2e8f0; }
.bg-gray-50 { background: var(--navy-700) !important; }
.bg-gray-100 { background: var(--navy-700) !important; }
.text-gray-800 { color: #e2e8f0 !important; }
```
**Rule:** JS-generated HTML with hardcoded `bg-green-50`/`bg-red-50` etc. — must use
inline `style=` with navy variables (CSS classes won't reach JS template literals).

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

## Score System
- Audit score 0–100 based on issues found
- Score 0 + 0 issues = CORRECT behaviour on genuinely bad data days (do NOT "fix" this)
- Score calculated in `run_full_audit()` → deductions per issue severity

---

## Bugs Fixed (All Sessions — June 2026)
1. **0 issues bug** — `run_full_audit` used undefined `transactions` variable → NameError. Fixed: pass `txn_list = daybook.to_dict('records')`
2. **Wrong daybook column** — `audit_bank_accounts` used `txn.get('party')`. Fixed to `Particulars`
3. **Credit cards in bank list** — added `credit card`, `debit card`, `fund`, `prudential` etc. to `DEFINITELY_NOT_BANK`
4. **₹0 bank balances** — case-insensitive `tb_balance_ci` lookup added for daybook-discovered banks
5. **AI wrong totals** — `build_context()` sent raw rows; AI recalculated wrong. Fixed: send grouped party totals
6. **All white backgrounds** — global CSS override block added; JS banners fixed with inline styles
7. **Bank Reconciliation closing balance** — hardcoded light-color inline styles → fixed to navy
8. **`_aTd()` invisible text** — `color:var(--ink)` (dark on dark) → `color:#e2e8f0`
9. **TDS page no data** — `renderTDSPage()` never called from `renderAuditResults()`. Fixed
10. **PT hardcoded demo data** — replaced with dynamic `id="pt-employee-table"` from audit
11. **"Kolkata 700071" treated as group header** — header rows above `data_start` line now ignored
12. **Advance to Staff / TDS Receivables under Bank Accounts** — TB parser now uses two-level hierarchy; Level 2 sub-groups reset `current_group` back to Level 1 after processing
13. **Suspense Account under Sundry Creditors** — same fix as above; now correctly under Current Liabilities

---

## What's Next (Priority Order)
1. **Compliance Calendar** — connect to real dates based on uploaded FY period
2. **History page** — save past audits to disk/DB, load previous results
3. **Export to Excel** — download audit results as formatted .xlsx report
4. **Multi-company support** — login, company switcher
5. **Supabase migration** — move from file-based to DB-backed (when scaling)
6. **Cash flow statement** — derive from daybook
7. **Tally XML import** — accept `.xml` export in addition to `.xlsx`

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
1. This is Flask + single HTML file — NOT Next.js
2. Color theme is LOCKED: navy-900/800/700 — never use white/cream backgrounds
3. JS-generated HTML strings need inline `style=` with navy vars — CSS classes won't reach them
4. `Particulars` is the daybook party column — NOT `party`
5. `txn_list` (not `transactions`) must be passed to `audit_bank_accounts()`
6. `build_context()` in `ca_agent.py` must pass grouped totals — not raw rows
7. Score 0 + 0 issues on bad data = correct, don't "fix"
8. `renderTDSPage()` must be called from both `renderAuditResults()` AND `showPage('tdsanalysis')`
9. Always check JS template literals for hardcoded light colors — they bypass CSS overrides
10. Push to GitHub after every fix — Render auto-deploys
11. **AUTONOMOUS RULE (PERMANENT):** For ANY audit logic issue — wrong rule, missing check, incorrect law reference, new compliance requirement — DO NOT ask Sagar. Use WebSearch to find the correct Indian law/act/section, verify it, then implement directly. Sagar's job is product decisions only.
12. TB parser uses TWO-LEVEL hierarchy — `LEVEL1` groups reset context; `LEVEL2` sub-groups add as ledger under Level 1 then reset `current_group` to Level 1. See "TB Parser" section above.
13. Every audit finding must include a `law` field citing the specific section/act (e.g. "Sec 43B(h) IT Act")
14. NEVER add bank detection by ledger name — use GROUP (Pass 1) + daybook behavior (Pass 2) only
15. `current_level1` must be initialized to `None` before the parse loop alongside `current_group`

---
*Owner: Sagar Pathak | Built with Claude | June 2026*
