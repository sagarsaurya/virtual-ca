# VirtualCA — Full Product Log & Build Documentation

**Started:** 14 March 2026
**Owner:** Sagar Pathak
**Status:** Live on Render — Active Development

---

## June 2026 — Session 2 Changelog

### Quick Audit UI Redesign
- Score banner: replaced flat orange gradient with dark card + animated circular SVG gauge (r=44, circumference=276.5)
  - Gauge animates score from 0 on load. Colors: green ≥70, orange ≥40, red <40
  - Stat cards (Critical/Warnings/Questions) are now color-coded boxes (red/yellow/blue)
  - Change Files + Download Report stacked buttons on right
- Cash Violations section: law refs shown as red pill badges (Sec 40A(3) >₹10k · Sec 269ST >₹2L)

### Knowledge Base
- Created `knowledge/` folder with feature-mapped .md files
- `knowledge_loader.py` — loads and caches .md files by feature category
- `ca_agent.py` — injects full knowledge base into Groq system prompt for Ask Your CA
- Feature map: ask_ca=all 5 folders, quick_audit=audit+accounting+tally, bank_recon=tally+accounting

### Audit Engine
- `audit_engine.py`: TDS findings now include `law` field (exact section + interest rate u/s 201(1A))
- `bankrec_engine.py`: `_suggest_journal()` added — keyword-based Tally Dr/Cr suggestion for bank-only entries

### Ask CA / AI Explain
- `dashAskAI()` — quick question buttons on dashboard feed into Ask CA
- `askAIExplain()` + `/api/ai-explain` endpoint — explains any audit finding using knowledge base + Groq

### Coming Soon System (Session 1 — documented here for completeness)
- `comingSoon(featureName)` JS function — gold toast, auto-dismiss 2.5s
- All unbuilt features: opacity 0.75 + "Soon" badge + inner buttons pointer-events:none
- Blocked: AI Audit Manager, AI Auditor Assistant, GST Readiness, ITR Readiness, GST Analysis, Generate Reports

---

## June 2026 — Session 3 Changelog

### VPS Setup (Hostinger KVM2 — Mumbai)
- Provisioned Hostinger KVM2 VPS (IP: 72.61.241.198, Ubuntu 24.04)
- Installed Node.js 20.x
- Installed and configured **Hermes Agent** (nousresearch) via `curl install.sh | bash`
  - Gateway: Local (VPS), runs as systemd service (auto-start on reboot)
  - Channel: Telegram bot (@NousHostedHermesBot) connected to Sagar's Telegram
  - Model: claude-haiku-4-5 via Anthropic API key (stored in /root/.hermes/.env)
  - Status: ✅ Working — responds on Telegram
- Installed and configured **OpenClaw** (openclaw.ai) via `curl install.sh | bash`
  - Gateway: Local (VPS), runs as systemd service
  - Channel: Telegram bot (@openclaw_sagar_bot) — separate bot from Hermes
  - Model: anthropic/claude-haiku-4-5 (Anthropic API direct)
  - Anthropic API key set via `openclaw onboard --manual`
  - Status: ✅ Working — responds on Telegram
  - Note: OpenClaw loads heavy system prompt (~19k tokens per message) — Haiku used to reduce cost

### VirtualCA Site Fix (Render)
- Site was blank since June 14 — root cause: React build files missing on Render
- Fix: Added `pip install -r requirements.txt && cd frontend && CI=false npm run build` as Render build command
- Flask static handler conflict fixed — `Flask(__name__, static_folder=frontend/build/static)`
- Removed duplicate "Bank Reconciliation" from sidebar Workspace section
- Added **Delete Company** button in company dropdown — red trash icon on hover, confirmation dialog before delete
- Fixed **company_id not updating** on new company switch in QuickAudit — `getHeaders()` now reads localStorage fresh on every request instead of capturing at mount time

## Pending / Next Build
- `knowledge/accounting/` and `knowledge/tally/` — write Accounting Standards + Tally XML samples
- TDS Analysis page — full UI
- PT Analysis page — full UI
- Full Audit mode (deeper than Quick Audit)
- Connect OpenClaw to VirtualCA backend (teach it CA rules via knowledge/ folder)

---

**Status:** Live on Render ✅ | VPS Running ✅ | Hermes + OpenClaw on Telegram ✅
**Last Updated:** 15 June 2026 (Session 3)

---

## What We Are Building

**VirtualCA** is an AI-powered SaaS platform for Indian SMBs and CA firms using Tally.
Upload your Tally Trial Balance (or XML, ledger dump, bank statement, GST JSON) → AI instantly
flags all accounting errors, wrong ledger groupings, compliance deadlines, TDS issues,
bank reconciliation mismatches — and gives step-by-step Tally fix instructions.

**One-line pitch:** *"Upload your Tally file. Get a full audit in 30 seconds."*

---

## Files in This Folder

| File | Description |
|---|---|
| `prototype.html` | Complete UI prototype — all pages, all flows, fully interactive (single HTML file) |
| `analyzer.py` | Python script for Tally Excel analysis logic |
| `LOG.md` | This file — full product documentation and build specs |

---

## Target Users

| User | Pain | How We Help |
|---|---|---|
| SMB Owner | Doesn't know if books are correct | Instant analysis report |
| In-house Accountant | Makes ledger grouping errors | Error list with Tally fix steps |
| CA Firm | Reviews multiple clients manually | Multi-client admin panel |
| Startup Finance Team | Misses compliance deadlines | Calendar with alerts |

---

## All Pages Built in Prototype

### 1. Login Page
- Email + password fields (pre-filled for demo)
- "Sign In" button → navigates to Dashboard
- Dark gradient background, glass card UI
- Demo credentials shown: admin@company.com / any password

---

### 2. Dashboard
**What it shows:**
- 4 stat cards: Total Analyses (24), Critical Errors (7), Needs Review (12), Compliance Health (72%)
- Recent Analyses list → each row clickable → opens Results page
- Compliance Alerts widget (TDS overdue, PT upcoming, Salary done)
- "Ask Your Virtual CA" banner → links to AI chat

**To build:**
- Pull stats from DB: count of uploads per user, count of errors per severity
- Compliance alerts: calculate from fixed due-date rules against current date
- Recent analyses: last 5 uploads for this user/company

---

### 3. Upload & Analyze
**What it shows:**
- 5 file type selector tabs:
  1. **Excel Trial Balance** — .xlsx/.xls/.csv, export via Alt+E in Tally
  2. **Tally XML** — .xml, export via Gateway → Export Data → Masters & Transactions
  3. **Ledger Dump** — .xlsx, export via Account Books → Ledger → Alt+E
  4. **Bank Statement** — .csv/.xlsx, download from net banking (HDFC/ICICI/SBI/Axis/Kotak)
  5. **GST JSON** — .json, download GSTR-2A/2B from GST portal
- Upload zone (drag & drop or click to browse)
- Upload progress bar (Uploading → Analyzing → Mapping columns)
- After upload: **Data Mapping Screen** appears

**Data Mapping Screen:**
- Table showing: Required Field → Your Column → Sample Value → Status
- Fields mapped: Ledger Name, Ledger Group, Closing Balance, Dr/Cr, Opening Balance
- User can change column mapping via dropdowns
- **Chart of Accounts Mapping**: detects custom group names, lets user map them to standard Tally groups
- "Run Analysis" button → goes to Results page

**To build:**
- File upload endpoint (multipart/form-data)
- Parser per file type (pandas for Excel/CSV, xml.etree for XML, json.loads for GST JSON)
- Column detection: auto-detect header row, suggest mappings using fuzzy matching
- Store mapping preferences per company (so they don't re-map every time)
- Trigger analysis job after mapping confirmed

---

### 4. Analysis Results
**What it shows:**
- Header: file name, FY, upload date, ledger count
- 4 summary tiles: Total Ledgers (120), Critical (7), Review (12), OK (101)
- Buttons: Download PDF, **Export to Tally** (XML / Excel / CSV), New Upload

**Toolbar (new):**
- Color legend: Red=Critical, Yellow=Review, Green=OK, Grey=Ignored
- FY filter dropdown
- Sort by: Severity / Ledger Name / Error Type / Amount
- Download Report: PDF / Excel / CSV

**Fix Workflow Status Bar:**
- Shows: Open: 7 | In Progress: 2 | Resolved: 3 | Ignored: 1
- "Last updated by [user] at [time]"

**Tabs:** Critical Errors | Needs Review | All OK | Full Report

**Each Error Card contains:**
1. Severity badge (CRITICAL / REVIEW) + Ledger number
2. Ledger name + closing balance
3. **"Drill Down" button** → opens Ledger Drill-Down modal
4. **Error Explanation Panel:**
   - "Why This Error Occurred" — plain English explanation
   - "Rule violated" — accounting standard (AS-2, Matching Principle, Double Entry, etc.)
5. **3-column grid:** Current Group (wrong, red) | Problem | Should Be (correct, green)
6. **Auto-Correction Journal Entry (purple):**
   - Dr / Cr rows with amounts
   - Note on whether voucher is needed or just re-grouping
7. **How to Fix in Tally** (blue) — exact navigation path
8. **Fix Workflow Actions:**
   - Status dropdown: Open / In Progress / Resolved / Ignored
   - Assign to dropdown: team member names
   - Mark Resolved button
   - Comment input + Send button

**Ledger Drill-Down Modal:**
- Opening balance, Total Debits, Total Credits, Closing Balance
- Transaction History table: date, voucher no, narration, Dr/Cr amount
- Related Vouchers list: voucher number, date, type, party, amount

**Export to Tally Modal:**
- 3 export options: Tally XML / Excel correction sheet / Tally Import CSV
- Summary: "7 corrections ready to export"
- XML import instructions (step-by-step)
- Success toast after selecting format

**To build:**
- Analysis engine: rule-based ledger classifier (see Ledger Rules section below)
- Store results in DB: per upload, per ledger, with severity, correct group, etc.
- Workflow: status changes saved per error per user, with timestamp + commenter
- Assign: link error to user ID, send notification
- Export: generate XML in Tally's import format, generate Excel with correction sheet
- Drill-down: fetch voucher history from parsed data (stored in DB after upload)

---

### 5. History
**What it shows:**
- Table: File Name, Uploaded By, Date, Period, Result (tags), Action (View Report)
- Search input + Status filter dropdown
- Click any row → opens Results page for that upload

**To build:**
- Query uploads table filtered by company_id, order by created_at DESC
- Paginate (20 per page)
- Store: file_name, uploaded_by, created_at, fy_period, critical_count, review_count, ok_count

---

### 6. Ask Your CA (AI Chat)
**What it shows:**
- Blue "Data Connected" context banner: shows file name, ledger count, error count
- "Data Connected" green badge (pulses)
- AI greeting that reads actual uploaded data:
  - Lists top issues from the specific file
  - References exact amounts (e.g. "Bank Interest ₹25,000 mis-booked")
- Pre-loaded contextual Q&A example:
  - User: "Why is my profit low this month?"
  - AI: 4 specific data-driven reasons from the uploaded ledgers
- 5 quick-question chips (context-aware):
  - "Top 3 errors to fix?"
  - "TDS pending & interest?"
  - "Debtors with credit balance?"
  - "Journal entries to fix errors?"
  - "Improve compliance score?"
- Chat input (textarea, Enter to send, Shift+Enter for newline)
- Typing indicator (animated dots)
- Footer: "AI answers are based on your uploaded data"

**To build:**
- Claude API (claude-opus-4-6 or claude-sonnet-4-6)
- System prompt: inject the uploaded file's parsed data as context
  - Include: list of all ledgers, their groups, balances, error list
  - Include: compliance status, pending TDS, PT amounts
- User message → API call → stream response back
- Store chat history per session (optional: per upload)
- Quick-ask chips: pre-fill input and auto-send

**System prompt structure:**
```
You are VirtualCA, an expert Indian CA assistant. You have access to the following 
uploaded trial balance data:

Company: {company_name}
Financial Year: {fy}
Total Ledgers: {count}
Critical Errors: {critical_list}
Review Items: {review_list}
TDS Pending: {tds_pending}
PT Status: {pt_status}

Answer all questions based on this specific data. Give CA-level answers with 
journal entries, Tally navigation paths, and compliance notes. Be specific — 
mention ledger names and amounts from the data.
```

---

### 7. Journal Entry Guide
**What it shows:**
- Search input for entry types
- Category cards: Sales & Revenue, Purchases & Expenses, Banking, Tax & Compliance
- Pre-built entry templates (clickable):
  - Sales Invoice, Purchase Invoice, Bank Receipt, Payment
  - TDS Deduction, Depreciation, Salary with PT
- Each entry shows: Dr side | Cr side | Tally navigation

**To build:**
- Static content initially (no DB needed)
- Later: allow CA firms to add custom entries
- Search: client-side filter on entry names

---

### 8. Compliance Calendar
**What it shows:**
- 3 summary cards: Overdue (1), Due This Week (2), Completed Mar (3)
- Full calendar list for current month with:
  - Date badge (day + month)
  - Title + description + penalty info
  - Status badge: OVERDUE (pulsing) / X DAYS LEFT / ✓ DONE
  - "Mark Done" button

**Compliance items pre-loaded:**
| Date | Item | Notes |
|---|---|---|
| 7th every month | TDS Deposit | Section 200, penalty ₹200/day + 1.5%/month |
| 21st every month | PT Deposit (Kolkata) | Via Grips portal |
| Last day of month | Salary Payment | Deduct PT & TDS |
| 11th every month | GSTR-1 | GST outward supplies |
| 20th every month | GSTR-3B | GST summary return |
| 31st Jul | ITR Filing (non-audit) | |
| 31st Oct | ITR Filing (audit) | |
| 15 Jun/Sep/Dec/Mar | Advance Tax | |
| 31 Jul/Oct/Jan/May | TDS Quarterly Return | |

**To build:**
- Pre-seed compliance_items table with all Indian due dates + recurrence rules
- Auto-calculate next due date from recurrence
- Mark Done: update status in DB, record who marked it and when
- Overdue detection: compare due_date with today's date
- Email/WhatsApp reminder (Phase 3)

---

### 9. Bank Reconciliation Module
**What it shows:**
- Upload zone for 2 files:
  1. Bank Statement (CSV/Excel from bank)
  2. Tally Bank Ledger (Excel from Tally)
- After both uploaded: Reconciliation Summary appears:
  - 4 stat cards: Matched (131, 91.6%) | Unmatched (7) | Tally Only (3) | Duplicates (2)
- 4 tabs with detailed entries:
  - **Unmatched** (in bank, not in Tally): date, narration, bank ref, amount, why missing, suggested journal entry
  - **Tally Only** (in Tally, not in bank): possible outstanding cheque or wrong entry
  - **Duplicates**: same amount same date, two entries in Tally — delete one
  - **Matched**: table of all clean matches

**To build:**
- Parser: parse both files into list of {date, amount, narration, ref}
- Matching algorithm:
  1. Exact match: same date + same amount → Matched
  2. Amount match ± 3 days: → Probable match (flag for review)
  3. In bank only → Unmatched
  4. In Tally only → Tally Only
  5. Same date + same amount appearing twice in Tally → Duplicate
- Normalize narrations (strip bank ref codes, lowercase, strip spaces)
- Store reconciliation result in DB per session

---

### 10. TDS Analysis
**What it shows:**
- 4 summary cards: TDS Deducted (₹48,200) | TDS Deposited (₹38,500) | Pending (₹9,700) | Late Interest (₹291)
- **Section-wise TDS table:** 194C / 194J / 194I / 192 with Deducted / Deposited / Pending / Status
- **Late Payment Interest panel:**
  - Per-section interest calculation (1.5%/month on pending amount)
  - Total interest liability
  - Rate note: 1% for non-deduction, 1.5%/month for non-deposit (Section 201(1A))
- **TDS Return Mismatch (Form 26AS vs Books):** Deductor | Section | 26AS amount | Books amount | Difference | Reconcile button
- **Professional Tax (PT) — Kolkata/West Bengal section:**
  - 4 summary cards: PT Deducted (₹2,640) | PT Deposited (₹0) | Due Date (21st) | Portal (Grips WB)
  - **WB PT Slab table:**
    - Up to ₹10,000 → Nil
    - ₹10,001–₹15,000 → ₹110/month
    - ₹15,001–₹25,000 → ₹130/month
    - ₹25,001–₹40,000 → ₹150/month
    - Above ₹40,000 → ₹200/month
  - **Employee-wise PT table:** Employee | Gross Salary | Slab | PT Due
  - **2 Tally journal entries:**
    - Entry 1 (deduction on salary date): Dr Salary A/c | Cr PT Payable (Duties & Taxes)
    - Entry 2 (deposit via Grips by 21st): Dr PT Payable | Cr HDFC Bank
  - Step-by-step Grips deposit instructions (wbifms.gov.in)

**To build:**
- TDS engine: scan all vouchers for TDS deducted vs TDS deposited per section
- Sections to handle: 192, 194C, 194J, 194I, 194H, 194D, 194A
- Interest calculator: (pending amount × 1.5% × months delayed)
- 26AS reconciliation: import Form 26AS JSON/XML → compare deductor-wise
- PT engine: pull employee salaries from payroll ledgers → apply WB slab → calculate PT
- PT deposit tracking: check if PT Payable ledger has been zeroed out by 21st

---

### 11. Admin Panel
**What it shows:**
- 3 stat cards: Total Users (4) | Total Uploads (24) | Errors Fixed (47)
- Users table: avatar, name, email, role badge (Admin/User), delete button, "Add User" button
- All Uploads Overview: file name, uploaded by, date, result tag

**To build:**
- RBAC: Admin can add/remove users, see all uploads; User can only see own uploads
- Invite by email (send magic link or temp password)
- User roles: Admin, Accountant, Viewer

---

## Ledger Analysis Rules (Core Engine)

The analysis engine checks each ledger's group against these rules:

| Ledger Pattern | Correct Group | Common Wrong Group | Severity |
|---|---|---|---|
| TDS Receivable | Current Assets | Duties & Taxes | Critical |
| TDS Payable | Duties & Taxes | Current Assets | Critical |
| GST Input Credit (ITC) | Current Assets | Duties & Taxes | Critical |
| GST Output Payable | Duties & Taxes | Current Assets | Critical |
| Bank Interest Received | Indirect Incomes | Indirect Expenses | Critical |
| Salary | Indirect Expenses | Direct Expenses | Review |
| Depreciation | Indirect Expenses | Direct Expenses | Review |
| Capital / Partner's Capital | Capital Account | Loans (Liability) | Critical |
| Drawings | Capital Account | Indirect Expenses | Critical |
| Prepaid Expenses | Current Assets | Indirect Expenses | Critical |
| Accrued Income | Current Assets | Indirect Incomes | Review |
| Security Deposit (paid) | Loans & Advances (Asset) | Fixed Assets | Review |
| Security Deposit (received) | Current Liabilities | Loans (Liability) | Review |
| Loan from Director | Loans (Liability) | Capital Account | Critical |
| Advance from Customer | Current Liabilities | Sundry Creditors | Review |
| Debtor with Credit balance | Flag for review | — | Review |
| Creditor with Debit balance | Flag for review | — | Review |
| Difference in Opening Bal | Flag (Dr ≠ 0) | — | Critical |
| PT Payable | Duties & Taxes | Current Liabilities | Review |
| Interest Payable | Current Liabilities | Indirect Expenses | Critical |

**Additional checks:**
- Opening balance: Dr total must equal Cr total (else flag Difference in OB)
- Dormant ledgers: zero balance + no transactions in current FY → Review
- Large round-number transactions (e.g. ₹5,00,000 exactly) → Review (possible estimate)
- Suspense Account with non-zero balance → Critical
- Sales returns > Sales → Critical

---

## Database Schema (PostgreSQL)

```sql
-- Companies (multi-tenant)
companies (id, name, gstin, city, state, plan, created_at)

-- Users
users (id, company_id, name, email, password_hash, role, created_at)

-- Uploads
uploads (
  id, company_id, uploaded_by,
  file_name, file_type, -- excel/xml/ledger/bank/gst
  fy_period, -- '2025-26'
  status, -- processing/complete/failed
  total_ledgers, critical_count, review_count, ok_count,
  created_at
)

-- Ledger Analysis Results
ledger_results (
  id, upload_id, ledger_name, ledger_number,
  current_group, correct_group,
  closing_balance, dr_cr,
  severity, -- critical/review/ok
  error_type, -- wrong_group/credit_balance/dormant/ob_diff
  rule_violated, -- text
  tally_fix_path, -- text
  workflow_status, -- open/inprogress/resolved/ignored
  assigned_to, -- user_id
  created_at
)

-- Workflow Comments
workflow_comments (
  id, ledger_result_id, user_id, comment, created_at
)

-- Transactions (from drill-down)
transactions (
  id, upload_id, ledger_name,
  date, voucher_no, voucher_type,
  narration, debit, credit, party
)

-- Compliance Items
compliance_items (
  id, company_id, title, description,
  due_date, recurrence, -- monthly/quarterly/annual
  status, -- pending/done/overdue
  marked_done_by, marked_done_at,
  penalty_note
)

-- TDS Records
tds_records (
  id, upload_id, section,
  nature, deducted, deposited, pending,
  interest_amount, status
)

-- PT Records
pt_records (
  id, upload_id, employee_name,
  gross_salary, pt_slab, pt_amount,
  month, deposited, deposit_date
)

-- Bank Reconciliation
bank_recon_sessions (
  id, company_id, upload_id,
  bank_file_name, tally_file_name,
  matched, unmatched, tally_only, duplicates,
  created_at
)

bank_recon_entries (
  id, session_id, entry_type, -- matched/unmatched/tally_only/duplicate
  date, narration, bank_amount, tally_amount,
  bank_ref, voucher_no, party
)

-- Chat History
chat_messages (
  id, company_id, upload_id, user_id,
  role, -- user/assistant
  content, created_at
)
```

---

## API Endpoints (Backend)

```
POST   /api/auth/login
POST   /api/auth/signup
POST   /api/auth/logout

GET    /api/dashboard                    → stats, recent uploads, compliance alerts
POST   /api/uploads                      → upload file (multipart)
GET    /api/uploads/:id/results          → analysis results
GET    /api/uploads/:id/results/:ledger  → drill-down detail
PATCH  /api/uploads/:id/results/:ledger  → update workflow status/assignee
POST   /api/uploads/:id/results/:ledger/comments
GET    /api/uploads/:id/export/:format   → xml/excel/csv download
GET    /api/uploads/history              → paginated list

POST   /api/chat                         → send message, get AI response (streaming)

GET    /api/compliance                   → all items for company
PATCH  /api/compliance/:id/done         → mark done

GET    /api/tds/:upload_id              → TDS analysis
GET    /api/pt/:upload_id               → PT analysis

POST   /api/bankrec                      → start reconciliation (upload 2 files)
GET    /api/bankrec/:session_id         → results

GET    /api/admin/users                  → list users
POST   /api/admin/users                  → invite user
DELETE /api/admin/users/:id
```

---

## Tech Stack

### Frontend
- **React 18** (Vite)
- **Tailwind CSS v3**
- **React Router v6**
- **Zustand** (state management)
- **Recharts** (dashboard charts)
- **React Query / TanStack Query** (API calls + caching)
- **Font Awesome** icons

### Backend
- **Python FastAPI** (chosen for Excel/pandas support)
- **pandas + openpyxl** (Excel parsing)
- **xml.etree** (Tally XML parsing)
- **Anthropic Python SDK** (Claude API for chat)
- **SQLAlchemy + Alembic** (ORM + migrations)
- **PostgreSQL** (main database)
- **Redis** (session cache, job queue)
- **Celery** (async file processing jobs)
- **AWS S3 / Cloudflare R2** (file storage)
- **JWT** (auth tokens)

### Infrastructure
- **Vercel** (React frontend)
- **Railway or Render** (FastAPI backend)
- **Supabase** (PostgreSQL + Auth, optional)
- **Resend** (transactional email)
- **Razorpay** (Indian payments)

---

## AI Integration (Claude API)

**Model:** `claude-sonnet-4-6` for chat, `claude-haiku-4-5-20251001` for quick analysis suggestions

**Chat system prompt pattern:**
```python
system_prompt = f"""
You are VirtualCA, an expert Indian Chartered Accountant assistant.
You are analyzing the following uploaded trial balance:

Company: {company.name}
Financial Year: {upload.fy_period}
Total Ledgers: {upload.total_ledgers}

CRITICAL ERRORS FOUND:
{format_errors(critical_errors)}

REVIEW ITEMS:
{format_errors(review_items)}

TDS Status:
- Deducted: ₹{tds.deducted} | Deposited: ₹{tds.deposited} | Pending: ₹{tds.pending}
- Interest accrued: ₹{tds.interest}

PT Status (Kolkata):
- PT Deducted: ₹{pt.deducted} | Deposited: ₹{pt.deposited} | Due: 21st

Answer questions based on this specific data. Always mention ledger names,
amounts, and section numbers. Provide journal entries using Tally format.
Include Tally navigation paths in your answers.
Respond in clear English. Keep answers concise but complete.
"""
```

---

## Pricing Plan

| Plan | Price | Limits |
|---|---|---|
| Free | ₹0 | 2 uploads/month, no AI chat |
| Starter | ₹499/month | 10 uploads, AI chat (50 msgs) |
| Pro | ₹1,499/month | Unlimited uploads + chat + compliance alerts |
| CA Firm | ₹3,999/month | Multiple clients, team access, priority support |

---

## Build Phases

### Phase 1 — Prototype ✅ COMPLETE
- [x] Full UI prototype in single HTML file
- [x] All 11 pages built and interactive
- [x] Simulated upload + analysis flow
- [x] Ledger drill-down modal
- [x] Export to Tally modal (XML / Excel / CSV)
- [x] Error explanation panels with accounting rules
- [x] Auto-correction journal entry suggestions
- [x] Fix workflow (status / assign / comment / mark resolved)
- [x] Bank Reconciliation page (upload + match simulation)
- [x] TDS Analysis page (section-wise + interest + 26AS mismatch)
- [x] PT Analysis — Kolkata WB slabs + employee-wise + journal entries
- [x] Contextual AI chat (reads uploaded data)
- [x] Multi-format upload (Excel, XML, Ledger, Bank, GST JSON)
- [x] Data mapping screen + Chart of Accounts mapping
- [x] UX: color legend, FY filter, sort, download report

### Phase 2 — MVP (Build Next)
- [ ] React frontend (convert prototype)
- [ ] FastAPI backend
- [ ] File upload + Excel parser (pandas)
- [ ] Rule-based ledger analysis engine (implement rules table above)
- [ ] PostgreSQL database + all tables
- [ ] JWT auth (login/signup/logout)
- [ ] Real analysis report stored in DB
- [ ] Claude API integration for AI chat
- [ ] Deploy on Vercel + Railway

### Phase 3 — Growth
- [ ] Tally XML export (real format)
- [ ] PDF report generation (WeasyPrint or Puppeteer)
- [ ] Compliance calendar with email reminders (Resend)
- [ ] Multi-client support for CA firms
- [ ] Razorpay payment integration
- [ ] Real bank reconciliation algorithm
- [ ] Real TDS section detection from ledger names
- [ ] PT auto-calculation from payroll ledgers

### Phase 4 — Scale
- [ ] Tally direct integration (Tally XML API / TDL)
- [ ] WhatsApp bot (Twilio or WATI)
- [ ] GSTR-2A/2B vs books reconciliation
- [ ] Bank statement reconciliation (HDFC/ICICI auto-import)
- [ ] P&L + Balance Sheet validation
- [ ] Multi-branch support
- [ ] Mobile app (React Native)

---

## Change Log

### 11 June 2026
- **Dashboard redesign** — replaced old 4-card layout (Total Audits / Critical / For Review / Health Score) with new AI Audit Manager design
  - Row 1: AI Audit Manager banner + AI Auditor Status + Next Action Required
  - Row 2: 5 score cards (Health Score, Audit Status, GST Readiness, ITR Readiness, Data Completeness)
  - Row 3: Recent Analyses + Audit Journey timeline + AI Auditor Assistant
  - Row 4: Quick Actions (5 buttons)
  - Why: mockup provided by Sagar showing professional AI-first dashboard layout
- **Coming Soon system** — all unbuilt features locked with toast notification on click
  - `comingSoon(featureName)` function added — shows gold animated toast, auto-dismisses in 2.5s
  - Locked: AI Audit Manager (entire Row 1), AI Auditor Status, Next Action Required, AI Auditor Assistant panel, GST Readiness card, ITR Readiness card, GST Analysis (Quick Actions), Generate Reports (Quick Actions), How It Works button
  - Why: these features are not yet built — user was accidentally clicking into wrong pages
  - All locked cards show "Soon" badge, gray out, highlight gold on hover
- **AI Audit Manager sidebar item** added with "New" badge — clicking shows Coming Soon toast
  - Why: mockup showed it as a separate sidebar item between Dashboard and History
- **Multi-company support** — full implementation across frontend + backend
  - `X-Company-ID` header on every API call, `get_cid()` in Flask reads it
  - `company_{cid}/` prefix on all Supabase file storage paths
  - `apiFetch()` helper wraps all fetch calls with company header
  - Company switcher UI in sidebar (gold dropdown, Add Company modal)
  - `loadCompanies()` syncs active company name from server (fixes rename issue)
  - Why: Sagar has multiple client companies (AJKL, Mridula Laddha etc.) — data must be isolated
- **Bank cross-check fix** — fallback to old pre-multi-company file path for migrated files
  - Why: existing bank statements uploaded before multi-company were at root level, new code looked in company subfolder and missed them
- **Bank files Delete button** added on Bank Recon "already uploaded" banner
  - `/api/clear-bank-files` endpoint added
  - `clearBankFiles()` JS function removes banner, resets UI
  - Why: users were blocked from re-uploading bank files once saved
- **Full Audit endpoint** fully migrated to multi-company (`cpath()`, `rname()`, `cid`)
  - Why: was the last endpoint still using old global file paths

### 10 June 2026
- **BS + P&L file persistence** — remembered across sessions via Supabase, no re-upload needed
  - Why: users were frustrated uploading the same files every session
- **`loadFilesStatus()` fix** — now hides file bar AND resets audit UI when switching to a company with no files
  - Why: switching company still showed previous company's files

### 15 March 2026
- Added Fix Workflow to Results page: status (Open/In Progress/Resolved/Ignored), assign to, comments, mark resolved
- Added Fix Workflow Status Bar (Open/InProgress/Resolved/Ignored counts)
- Added UX toolbar: color legend, FY filter, sort by, download report (PDF/Excel/CSV)
- Upgraded Upload page: 5 file type tabs (Excel, Tally XML, Ledger, Bank, GST JSON)
- Added Data Mapping screen after upload (column mapping + Chart of Accounts mapping)
- Added Bank Reconciliation Module: upload 2 files, auto-match, show Unmatched/Tally Only/Duplicates/Matched tabs
- Added TDS Analysis page: section-wise table (194C/194J/194I/192), late interest calculator, 26AS mismatch table
- Added PT Analysis section (Kolkata/WB): WB slabs, employee-wise PT, journal entries, Grips steps
- Upgraded Ask Your CA: contextual AI banner, data-connected greeting, pre-loaded contextual Q&A
- Added Ledger Drill-Down modal: transaction history + voucher details
- Added Export to Tally modal: XML / Excel / CSV with import instructions
- Added Error Explanation Panel: why error occurred + accounting rule violated
- Added Auto-Correction Journal Entry on each error card

### 14 March 2026
- Created full UI prototype (`prototype.html`) with 8 pages
- Created `LOG.md` with initial product documentation

---

*Maintained by Sagar Pathak · VirtualCA Product Log*
