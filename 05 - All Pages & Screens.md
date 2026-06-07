# 🖥️ All Pages & Screens

**← [[00 - Home]]**

---

## Page List (11 Pages Built in Prototype)

| # | Page | Nav Item | Status |
|---|---|---|---|
| 1 | Login | — | ✅ |
| 2 | Dashboard | Dashboard | ✅ |
| 3 | Upload & Analyze | Upload & Analyze | ✅ |
| 4 | Analysis Results | (from dashboard/history) | ✅ |
| 5 | History | History | ✅ |
| 6 | Bank Reconciliation | Bank Reconciliation | ✅ |
| 7 | Ask Your CA (AI Chat) | Ask Your CA | ✅ |
| 8 | Journal Entry Guide | Journal Entry Guide | ✅ |
| 9 | Compliance Calendar | Compliance Calendar | ✅ |
| 10 | TDS Analysis | TDS Analysis | ✅ |
| 11 | Admin Panel | Admin Panel | ✅ |

---

## Page 1 — Login

- Email + password fields (pre-filled for demo)
- Sign In button → navigates to Dashboard
- Dark gradient background, glass card UI
- Demo credentials: `admin@company.com` / any password
- "Forgot password?" link
- "Remember me" checkbox

---

## Page 2 — Dashboard

**Stats row (4 cards):**
- Total Analyses: 24
- Critical Errors: 7
- Needs Review: 12
- Compliance Health: 72%

**Widgets:**
- Recent Analyses list → each row clickable → opens Results
- Compliance Alerts widget (TDS overdue, PT upcoming, Salary done)
- "Ask Your Virtual CA" banner → links to AI chat

**To build:**
- Stats from DB: count uploads, count errors by severity per user
- Compliance alerts: calculate from fixed due-date rules vs today's date
- Recent analyses: last 5 uploads for this user/company

---

## Page 3 — Upload & Analyze

**5 file type tabs:**
1. Excel Trial Balance
2. Tally XML
3. Ledger Dump
4. Bank Statement
5. GST JSON

**Upload flow:**
1. Select file type tab
2. Drag & drop or browse
3. Progress bar (Uploading → Analyzing → Mapping columns)
4. Data Mapping Screen appears

**Data Mapping Screen:**
- Table: Required Field | Your Column | Sample Value | Status
- Fields: Ledger Name, Ledger Group, Closing Balance, Dr/Cr, Opening Balance
- User changes column mapping via dropdowns
- Chart of Accounts Mapping: map custom groups to standard Tally groups
- "Run Analysis" → goes to Results

---

## Page 4 — Analysis Results

See [[03 - Features Overview]] and [[06 - Fix Workflow & Team Collaboration]]

**Header:** File name, FY, upload date, ledger count
**Summary tiles:** Total Ledgers (120), Critical (7), Review (12), OK (101)
**Toolbar:** Colour legend, FY filter, Sort by, Download Report
**Status bar:** Open: 7 | In Progress: 2 | Resolved: 3 | Ignored: 1
**Tabs:** Critical Errors | Needs Review | All OK | Full Report

---

## Page 5 — History

- Table: File Name, Uploaded By, Date, Period, Result tags, Action (View Report)
- Search input + Status filter dropdown
- Click any row → opens Results for that upload

**To build:**
- Query uploads table filtered by company_id, ORDER BY created_at DESC
- Paginate 20 per page

---

## Page 6 — Bank Reconciliation

See [[14 - Bank Reconciliation]]

---

## Page 7 — Ask Your CA

See [[17 - AI Integration (Claude API)]]

**Key UI elements:**
- Blue "Data Connected" banner: file name, ledger count, error count
- Green pulsing "Data Connected" badge
- Pre-loaded contextual Q&A
- 5 quick-ask chips
- Chat input (Enter to send, Shift+Enter for newline)
- Typing indicator (animated dots)

---

## Page 8 — Journal Entry Guide

- Search bar for entry types
- Category cards: Sales & Revenue, Purchases & Expenses, Banking, Tax & Compliance
- Pre-built entries: Sales Invoice, Purchase Invoice, Bank Receipt, Payment, TDS Deduction, Depreciation, Salary with PT
- Each entry shows: Dr side | Cr side | Tally navigation

---

## Page 9 — Compliance Calendar

See [[15 - Compliance Calendar]]

---

## Page 10 — TDS Analysis

See [[12 - TDS Analysis]]

---

## Page 11 — Admin Panel

- 3 stat cards: Total Users (4), Total Uploads (24), Errors Fixed (47)
- Users table: avatar, name, email, role badge (Admin/User), delete button
- "Add User" button
- All Uploads Overview: file name, uploaded by, date, result tag

**Roles:** Admin (full access), Accountant (own uploads + assigned errors), Viewer (read-only)
