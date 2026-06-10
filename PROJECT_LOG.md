# VirtualCA — Project Log

> Built by Sagar Pathak (Kolkata) with Claude. No developer — 100% AI-built.
> This file tracks every major feature, fix, and design decision.

---

## TECH STACK
- Backend: Python + Flask
- Frontend: Single-file HTML/CSS/JS (`index.html`)
- Storage: Supabase (PostgreSQL + file storage) — replaces local disk (Render has no persistent disk)
- Hosting: Render (free tier) → https://virtual-ca.onrender.com
- AI: Groq API (for CA chat)

---

## CORE FEATURES (what the app does)

### 1. Quick Audit (TB + Daybook)
- Upload Trial Balance + Daybook Excel exports from Tally
- Runs 9 audit modules: Cash Violations, Ledger Classification, TDS Compliance, Outstanding Balances, Large Expenses, Loans & Director Advances, Bank Accounts, ITR/Personal Expenses, Salary/PF/PT
- Score out of 100, Critical / Warnings / Questions breakdown
- Cash violations: grouped by party, mark "All Bank" to confirm bank payment
- Bank cross-check: auto-clears cash violations that have a matching debit in the bank statement

### 2. Bank Reconciliation
- Upload Bank Statement (PDF/Excel/CSV) + Tally Bank Ledger
- Matches entries: Matched / Wrong Date / Missing in Tally / Extra in Tally / Duplicates
- Closing balance comparison
- "Change Files" back button

### 3. Full Audit (all 6 files)
- Combines: TB + Daybook (from Quick Audit) + Bank Statement + Bank Ledger (from Bank Recon) + Balance Sheet + P&L (new upload)
- BS/P&L compliance checks: Sec 269SS, Sec 200, Sec 194I, Sec 194J, Sec 32, Sec 197, Sec 80G
- Auto-clears cash violations verified against bank statement
- "Upload New Files" / "Change Files" back button

### 4. TDS Analysis
- Section-wise: 194C, 194J, 194I, 194H — payable, deposited, pending
- Salary/PT compliance table

### 5. Compliance Calendar
- TDS due dates, GST, Advance Tax, PT

### 6. Ask Your CA
- Groq AI chat with full audit context loaded

### 7. Journal Entry Guide
- Get correct journal entries for any transaction

### 8. Admin Panel
- Audit history, stats

### 9. Paper Trade (legacy — from TradeIQ, not used in VirtualCA)

---

## SUPABASE SCHEMA

### Tables
```sql
files_meta   — id=1, meta JSONB  (tracks all uploaded file names + timestamps)
audit_result — id=1, result JSONB (latest audit result)
audit_history — id serial, filename, audited_at, company, period, score, critical, warnings, questions
personal_marks — id serial, date, party, amount, reason  (bank confirmations + personal exclusions)
```

### Storage Bucket: `virtualca-files`
```
current_tb.xlsx        — Trial Balance
current_db.xlsx        — Daybook
current_bs.xlsx        — Balance Sheet
current_pnl.xlsx       — P&L
current_bank_stmt.xlsx — Bank Statement
current_bank_tally.xlsx — Tally Bank Ledger
```

---

## FILE MAP

| File | Purpose |
|---|---|
| `app.py` | Flask backend — all API endpoints |
| `index.html` | Entire frontend (HTML + CSS + JS) |
| `audit_engine.py` | 9 audit modules + `run_full_audit()` |
| `bankrec_engine.py` | Bank reconciliation + PDF/CSV/Excel parsers |
| `bs_pnl_audit.py` | Balance Sheet + P&L compliance checks |
| `supabase_client.py` | All Supabase DB + storage operations |
| `trade_analysis.py` | Behaviour analysis (legacy) |
| `paper_trade.py` | Paper trade engine (legacy) |

---

## CHANGE HISTORY (newest first)

### 2026-06-10 — Restore all sections on page reload
- **Problem**: Bank Accounts, Ledger Classification etc. showed `——` after page refresh
- **Cause**: On load, only CA chat banner + TDS + Salary were restored from saved Supabase result. `renderAuditResults()` was not called.
- **Fix**: Call `renderAuditResults(d)` on page load if saved result has `d.summary` and `audit_type !== 'full'`

### 2026-06-10 — Fix false positive: bank interest flagged as cash violation
- **Problem**: "Bank Interest", "Bank Charges" ledgers were being flagged as Sec 40A(3) cash violations
- **Cause**: Audit engine only checked account names within voucher for bank keywords, not the party name itself
- **Fix**: Added party-name check — if party matches bank keywords (bank interest, bank charges, interest on od, processing fee etc.) → skip flagging
- **Keywords added**: `bank interest`, `interest received`, `interest on od`, `bank charges`, `bank commission`, `processing fee`, `gst on bank`, `cash deposit`, `cheque deposit`

### 2026-06-10 — Bank cross-check in Quick Audit
- **Problem**: Bank cross-check only ran in Full Audit. Quick Audit still showed all cash violations including ones confirmed in bank statement.
- **Fix**: Extracted `_cross_check_bank()` helper in `app.py`, called from both `/api/audit` and `/api/full-audit`
- Quick Audit badge shows "X auto-cleared by bank ✓" inline

### 2026-06-10 — Cross-check cash violations against bank statement (Full Audit)
- **Problem**: Daybook flags "Cash payment to Anil Gupta" but bank statement has a matching debit — it was a bank payment, not cash
- **Logic**: For each cash violation, find a bank debit within ±1% amount and ±3 days date → auto-clear
- **New section in Full Audit**: "Auto-Cleared — Bank Statement Match" (green) shows cleared items
- **New function**: `parse_bank_statement()` in `bankrec_engine.py`

### 2026-06-10 — Save bank confirmations to server
- **Problem**: "All Bank" / "✓ All Bank" buttons in Quick Audit only did visual strikethrough — never saved to server. Full Audit had no idea what was confirmed.
- **Fix**: `confirmPartyBank()` and `confirmAllBank()` now save each transaction to `/api/audit/mark-personal` with reason "Bank payment — confirmed"
- `window._cashGroups` stores group data so individual transaction (date, party, amount) can be saved

### 2026-06-10 — Change Files / back button on all 3 audit pages
- **Problem**: No way to go back to upload page from results; Full Audit "Upload New Files" was broken
- **Fix**: 
  - Quick Audit: "← Change Files" button added to score banner (calls `resetAudit()`)
  - Bank Recon: "← Change Files" at top of results (calls `brResetToUpload()`)
  - Full Audit: Fixed `faResetToUpload()` — was using fragile `nextElementSibling`, now uses `getElementById('faUploadBox')`
  - `startCompleteAudit()` was hiding elements via `:nth-child` selector — fixed to use IDs

### 2026-06-10 — Bank Recon remembers uploaded files
- **Problem**: Bank Reconciliation page always showed empty upload zones even if files already uploaded
- **Fix**: `loadBankRecStatus()` called on page open — checks `/api/files/status`, shows "already uploaded ✓" banner + "Run Reconciliation with Existing Files" button
- New endpoint: `POST /api/bankrec-existing` — runs recon using saved Supabase files, no re-upload

### 2026-06-09 — Nav highlight + Upload New Files button
- **Problem**: Active nav item not highlighted; no way back to upload page in Full Audit
- **Fix**: `showPage()` now matches nav items by `onclick` attribute string; added "Upload New Files" button on Full Audit results

### 2026-06-09 — Full Audit result screen rebuilt
- **Problem**: Full Audit showed only 3 stat cards — "rubbish" per user
- **Fix**: `renderFullAuditResults()` completely rebuilt with 7 sections: Score Banner, Critical Issues, Warnings, Loans & Large Payments, Personal Expenses, Salary/PF/PT, Bank Recon, Action List

### 2026-06-09 — Supabase integration
- **Problem**: Render free tier has no persistent disk — files and data lost on every restart
- **Solution**: Supabase PostgreSQL for metadata/results, Supabase Storage for Excel/PDF files
- New file: `supabase_client.py` with all DB + storage operations
- All endpoints updated: upload → save to Supabase; audit → download from Supabase if local missing (`_ensure_local()`)

### 2026-06-09 — Full Audit feature (all 6 files)
- **Design**: One feature that combines TB+Daybook (from Quick Audit session) + Bank Statement+Ledger (from Bank Recon session) + Balance Sheet+P&L (new upload)
- New file: `bs_pnl_audit.py` — BS/P&L compliance checks
- New endpoint: `POST /api/full-audit`
- Old "Full Audit" renamed to "Quick Audit"; new "Full Audit" = all 6 files

### 2026-06-09 — BS/P&L compliance checks (`bs_pnl_audit.py`)
- Sec 269SS: unsecured loans >₹20K received in cash
- Sec 200: TDS payable outstanding >30 days
- Sundry debtors >₹5L (review)
- Advance tax ₹0 (review)
- Sec 194I: rent paid >₹2.4L without TDS
- Sec 194J: professional fees >₹50K without TDS
- Sec 32: no depreciation entry found
- Sec 197: director remuneration >₹84L
- Sec 80G: donations present (review)

---

## AUDIT ENGINE — KEY RULES

### Cash Violations (Sec 40A(3) + Sec 269ST)
- Payment >₹10K flagged if voucher has NO bank account in any row
- Bank keywords: hdfc, icici, sbi, axis, kotak, neft, rtgs, upi, imps + bank interest/charges
- Party name also checked — bank-type ledger names never flagged
- Cross-checked against bank statement if available

### Ledger Classification
- Every ledger checked against ICAI Chart of Accounts
- Wrong group = flagged (e.g. TDS Payable in Direct Expenses)

### TDS Compliance
- 194C: contractor >₹30K single / >₹1L aggregate
- 194J: professional fees >₹50K
- 194I: rent >₹2.4L/year
- 194H: commission >₹15K

### Score Formula
```
score = 100 - (critical × 5) - (warnings × 2) - (questions × 1)
```

---

## KNOWN ISSUES / FUTURE IDEAS
- [ ] Export Full Audit as PDF/Excel
- [ ] Multi-company support
- [ ] GST reconciliation module
- [ ] Stricter party-name matching in bank cross-check (currently amount+date only, no name match)
- [ ] Bank statement: amount tolerance currently ±1% — might miss exact matches due to rounding
