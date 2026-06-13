# Sandeep Bajoria — Feature Specs

**Source:** Meeting on 12-06-2026
**← [[03 - Features Overview]] | [[16 - Build Phases & Roadmap]]**

---

## What Changed

| Decision | Detail |
|---|---|
| ❌ Bank Reconciliation | DROPPED — Tally already handles it |
| ✅ Party-wise Ledger Rec | CONFIRMED good — keep and improve |
| 🆕 6 new features | All grounded in real CA daily workflows |

---

## Feature 10 — TDS Detection + AI Action (UPGRADE)

**What:** Scan every ledger entry and detect:
- Was TDS applicable on this payment?
- Was TDS actually deducted?
- If not deducted → AI tells what to do

**Build:** See [[21 - TDS Detection Rules]]

---

## Feature 14 — Balance Sheet from Trial Balance

**What:** Auto-generate a proper Balance Sheet by grouping Trial Balance ledgers

**Build:** See [[22 - Balance Sheet Generator]]

---

## Feature 15 — P&L on Shares + Mutual Funds

**What:** Read investment/trading ledgers from Tally → calculate realized gains → show STCG/LTCG breakdown

**Build:** See [[23 - Investment P&L]]

---

## Feature 16 — Tally vs Broker Statement Reconciliation

**What:** Upload broker statement (Zerodha/Groww/ICICI Direct) + Tally trading ledger → match entries both sides

**Build:** See [[24 - Broker Reconciliation]]

---

## Feature 17 — Document Availability against Entries

**What:** For each Tally entry, show what supporting document exists (bill, invoice, receipt) — and flag entries with no document

**Build:** See [[25 - Document Checker]]

---

## Feature 18 — GST Return File Generator

**What:** Take raw Tally export → parse sales/purchase ledgers → generate GSTR-1 / GSTR-3B ready JSON/Excel for CA to review and file

**Build:** See [[26 - GST Return Generator]]

---

## Feature 19 — Fund Flow + Cash Flow + Budget

**What:**
- Cash Flow Statement (from bank + cash book movements)
- Fund Flow Statement (changes in working capital)
- Budget (predict future spend from past patterns)

**Build:** See [[27 - Financial Statements]]

---

## Priority Order (suggested)

| Priority | Feature | Why |
|---|---|---|
| 1 | Balance Sheet from TB | Every CA needs this, straightforward |
| 2 | TDS Detection upgrade | High compliance value, rules are clear |
| 3 | GST Return Generator | CAs file GSTR every month — very high value |
| 4 | Cash Flow + Fund Flow | Standard financial reporting |
| 5 | P&L on Shares/MF | Growing need, niche advantage |
| 6 | Broker Reconciliation | Complex but unique feature |
| 7 | Document Checker | Needs voucher data from Tally XML |
