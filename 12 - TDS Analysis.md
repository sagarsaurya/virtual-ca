# 📊 TDS Analysis

**← [[00 - Home]]**

---

## Overview

Full TDS health check — not just a reminder, but complete reconciliation and interest calculation.

---

## Summary Cards (UI)

| Card | Demo Value |
|---|---|
| TDS Deducted | ₹48,200 |
| TDS Deposited | ₹38,500 |
| Pending | ₹9,700 |
| Late Interest | ₹291 |

---

## Section-Wise TDS Table

| Section | Nature | Deducted | Deposited | Pending | Status |
|---|---|---|---|---|---|
| 194C | Contractor payments | ₹18,500 | ₹18,500 | ₹0 | ✅ Clear |
| 194J | Professional fees | ₹22,000 | ₹12,300 | ₹9,700 | ⚠️ Pending |
| 194I | Rent | ₹4,200 | ₹4,200 | ₹0 | ✅ Clear |
| 192 | Salary | ₹3,500 | ₹3,500 | ₹0 | ✅ Clear |

---

## Late Payment Interest Calculator

**Rate:** 1.5% per month on pending TDS amount
**Reference:** Section 201(1A) of Income Tax Act

Formula:
```
Interest = Pending Amount × 1.5% × Number of Months Delayed
₹291 = ₹9,700 × 1.5% × 2 months
```

Additional: 1% per month if TDS was not deducted at all (non-deduction rate)

---

## TDS Return Mismatch (Form 26AS vs Books)

| Deductor | Section | 26AS Amount | Books Amount | Difference |
|---|---|---|---|---|
| Vendor A | 194J | ₹22,000 | ₹20,500 | ₹1,500 ⚠️ |
| Vendor B | 194C | ₹18,500 | ₹18,500 | ₹0 ✅ |

User can click "Reconcile" on any mismatch row.

---

## Due Dates

| Item | Due Date | Penalty |
|---|---|---|
| Monthly TDS deposit | 7th of every month | ₹200/day under Section 234E + 1.5%/month |
| TDS quarterly return | 31 Jul / 31 Oct / 31 Jan / 31 May | ₹200/day |

---

## Sections Handled

- **192** — Salary
- **194A** — Interest other than securities
- **194C** — Contractor / sub-contractor payments
- **194D** — Insurance commission
- **194H** — Commission or brokerage
- **194I** — Rent
- **194J** — Professional / technical fees

---

## To Build (Backend)

```python
# TDS Engine
def analyze_tds(upload_id):
    # 1. Scan all vouchers for TDS deducted (look for "TDS" in ledger names)
    # 2. Match with TDS deposited (TDS payment vouchers)
    # 3. Group by section (194C, 194J, etc.)
    # 4. Calculate pending = deducted - deposited
    # 5. Calculate interest: pending × 1.5% × months_delayed
    # 6. Compare with 26AS if imported

# Section detection from ledger names:
# "TDS on Professional Fees" → 194J
# "TDS on Contractor" → 194C
# "TDS on Salary" → 192
# Use keyword matching + regex
```

---

## Related Notes
- [[13 - PT Analysis Kolkata]]
- [[15 - Compliance Calendar]]
- [[11 - Ledger Analysis Rules]]
