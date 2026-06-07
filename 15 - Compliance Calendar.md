# 📅 Compliance Calendar

**← [[00 - Home]]**

---

## Overview

Never miss a statutory deadline. All Indian compliance due dates tracked in one place with live status, days remaining, and penalty information.

---

## Summary Cards (UI)

| Card | Demo Value |
|---|---|
| Overdue | 1 (pulsing red) |
| Due This Week | 2 |
| Completed This Month | 3 |

---

## All Compliance Items

| Due Date | Item | Description | Penalty |
|---|---|---|---|
| **7th every month** | TDS Deposit | Section 200 — deposit TDS deducted | ₹200/day + 1.5%/month interest |
| **11th every month** | GSTR-1 | Outward supplies return | ₹200/day (CGST + SGST) |
| **20th every month** | GSTR-3B | Monthly GST summary return | ₹200/day + late fee |
| **21st every month** | PT Deposit (Kolkata/WB) | Via Grips portal — wbifms.gov.in | Penalty + interest from WB Govt |
| **Last day of month** | Salary Payment | Deduct PT & TDS before payment | Labour law violation |
| **15 Jun / Sep / Dec / Mar** | Advance Tax | Quarterly advance income tax | Interest under Sec 234B & 234C |
| **31 Jul / 31 Oct / 31 Jan / 31 May** | TDS Quarterly Return | Form 24Q / 26Q | ₹200/day under Section 234E |
| **31st July** | ITR Filing (non-audit) | Income Tax Return | Penalty up to ₹5,000 |
| **31st October** | ITR Filing (audit cases) | ITR for companies/audit required | Penalty up to ₹10,000 |

---

## Status Display Logic

| Status | When | UI |
|---|---|---|
| OVERDUE | due_date < today, not done | 🔴 Pulsing red badge |
| X DAYS LEFT | due_date ≥ today, not done | 🟡 Yellow with countdown |
| DONE ✓ | marked_done = true | 🟢 Green badge |

---

## Item Actions

- **Mark Done** button on each item
- Saves: marked_done_by (user name), marked_done_at (timestamp)
- Can be un-marked if done by mistake

---

## To Build (Backend)

```python
# Pre-seed compliance_items table for each company
COMPLIANCE_RULES = [
    { "title": "TDS Deposit", "recurrence": "monthly", "day": 7,
      "penalty_note": "₹200/day + 1.5%/month interest" },
    { "title": "GSTR-1", "recurrence": "monthly", "day": 11 },
    { "title": "GSTR-3B", "recurrence": "monthly", "day": 20 },
    { "title": "PT Deposit (Kolkata)", "recurrence": "monthly", "day": 21,
      "penalty_note": "WB Govt penalty + interest" },
    { "title": "Advance Tax", "recurrence": "quarterly",
      "dates": ["Jun-15", "Sep-15", "Dec-15", "Mar-15"] },
    { "title": "TDS Quarterly Return", "recurrence": "quarterly",
      "dates": ["Jul-31", "Oct-31", "Jan-31", "May-31"] },
    { "title": "ITR Filing (non-audit)", "recurrence": "annual", "date": "Jul-31" },
    { "title": "ITR Filing (audit)", "recurrence": "annual", "date": "Oct-31" },
]

# Overdue detection:
def is_overdue(due_date, status):
    return due_date < date.today() and status != 'done'

# Days remaining:
def days_remaining(due_date):
    return (due_date - date.today()).days
```

---

## Future (Phase 3)

- Email reminders (via Resend) — 7 days before, 1 day before, on due date
- WhatsApp reminders (via Twilio/WATI)
- Google Calendar sync

---

## Related Notes
- [[12 - TDS Analysis]]
- [[13 - PT Analysis Kolkata]]
- [[16 - Build Phases & Roadmap]]
