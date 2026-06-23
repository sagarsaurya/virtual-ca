# ⚡ Features Overview

**← [[00 - Home]]**

---

## All Features at a Glance

| # | Feature | Status | Source |
|---|---|---|---|
| 1 | Smart Upload & Data Mapping | ✅ Built | — |
| 2 | Instant Analysis Results (colour-coded) | ✅ Built | — |
| 3 | Error Explanation Panel | ✅ Built | — |
| 4 | Ledger Drill-Down | ✅ Built | — |
| 5 | Auto-Correction Journal Entry | ✅ Built | — |
| 6 | Fix Workflow & Team Collaboration | ✅ Built | — |
| 7 | Export Back to Tally (XML/Excel/CSV) | ✅ Built | — |
| 8 | Bank Reconciliation Module | ❌ Dropped | Sandeep Bajoria — Tally already handles it |
| 9 | Party-wise Ledger Reconciliation | ✅ Keep & improve | Sandeep Bajoria — confirmed good |
| 10 | TDS Detection + AI Suggestions | 🔄 Upgrade needed | Sandeep Bajoria — detect missed TDS, suggest action |
| 11 | PT Analysis — Kolkata/WB slabs | ✅ Built | — |
| 12 | Ask Your CA — Contextual AI Chat | ✅ Built | — |
| 13 | Compliance Calendar | ✅ Built | — |
| 14 | Balance Sheet from Trial Balance | 🆕 New | Sandeep Bajoria |
| 15 | P&L on Shares + Mutual Funds | 🆕 New | Sandeep Bajoria |
| 16 | Tally vs Broker Statement Reconciliation | 🆕 New | Sandeep Bajoria |
| 17 | Document Availability against Entries | 🆕 New | Sandeep Bajoria |
| 18 | GST Return File Generator (GSTR format) | 🆕 New | Sandeep Bajoria |
| 19 | Fund Flow + Cash Flow + Budget | 🆕 New | Sandeep Bajoria |

---

## Sandeep Bajoria Meeting — 12 June 2026

Real feedback from CA/client meeting. Key decisions:

- **Bank Rec DROPPED** — Tally already does it. Not worth building.
- **Party-wise Ledger Rec CONFIRMED** — CAs actually use this.
- **6 new high-value features identified** — all grounded in real CA workflows.

See [[20 - Sandeep Bajoria Features]] for detailed build specs.

---

## Feature 1 — Smart Upload & Data Mapping

Accepts 5 file types:

| File | Tally Export Method |
|---|---|
| Excel Trial Balance (.xlsx/.csv) | Alt+E from Trial Balance |
| Tally XML (.xml) | Gateway → Export Data → Masters |
| Ledger Dump (.xlsx) | Account Books → Ledger → Alt+E |
| Bank Statement (.csv/.xlsx) | Net banking download |
| GST JSON (.json) | GSTR-2A/2B from GST portal |

After upload → **Data Mapping Screen** shows column mapping + Chart of Accounts mapping.
System remembers preferences for next upload.

---

## Feature 2 — Analysis Results

Colour legend:
- 🔴 **Critical** — Wrong group, balance error, compliance violation — fix immediately
- 🟡 **Review** — Possible misclassification or anomaly
- 🟢 **OK** — Correct group and balance
- ⚫ **Ignored** — User acknowledged, chose to skip

Toolbar includes: FY filter, sort by severity/ledger/error type/amount, download report (PDF/Excel/CSV)

---

## Feature 3 — Error Explanation Panel

Each error card shows:
- Why this error occurred (plain English)
- Which accounting rule was violated (AS-2, Matching Principle, Double Entry, etc.)
- Current group (red) vs Correct group (green)
- Auto-correction journal entry (Dr/Cr)
- Exact Tally navigation path

---

## Feature 4 — Ledger Drill-Down

Click any ledger → modal opens with:
- Opening balance, Total Debits, Total Credits, Closing Balance
- Full transaction history (date, voucher no, narration, Dr/Cr amount)
- Related vouchers list

---

## Feature 5 — Auto-Correction Journal Entry

Every error card shows a ready-made journal entry:
```
Dr  Office Expense A/c        ₹15,000
    Cr  Suspense Account           ₹15,000
(Narration: Correction of wrong booking — FY 2025-26)
```

---

## Feature 6 — Fix Workflow

See [[06 - Fix Workflow & Team Collaboration]]

---

## Feature 7 — Export to Tally

See [[07 - Export to Tally]]

---

## Feature 8 — Bank Reconciliation

See [[14 - Bank Reconciliation]]

---

## Feature 9 — TDS Analysis

See [[12 - TDS Analysis]]

---

## Feature 10 — PT Analysis

See [[13 - PT Analysis Kolkata]]

---

## Feature 11 — AI Chat

- Reads your actual uploaded data
- Answers questions with specific ledger names and amounts
- Pre-loaded contextual chips: Top errors, TDS pending, Journal entries, etc.
- Powered by Claude API (claude-sonnet)

See [[17 - AI Integration (Claude API)]]

---

## Feature 12 — Compliance Calendar

See [[15 - Compliance Calendar]]
