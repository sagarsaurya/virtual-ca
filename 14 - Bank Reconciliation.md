# 🏦 Bank Reconciliation Module

**← [[00 - Home]]**

---

## Overview

Upload your bank statement + Tally bank ledger → VirtualCA auto-matches every transaction and shows what's unmatched, missing, or duplicated.

---

## Upload Flow

1. Upload **Bank Statement** (CSV/Excel from net banking)
2. Upload **Tally Bank Ledger** (Excel export from Tally)
3. Click "Start Reconciliation"
4. Results appear in 4 tabs

---

## Supported Banks

- HDFC Bank
- ICICI Bank
- State Bank of India (SBI)
- Axis Bank
- Kotak Mahindra Bank
- Yes Bank, PNB, Bank of Baroda, and more

---

## Reconciliation Summary Cards (UI)

| Card | Demo Value | Meaning |
|---|---|---|
| Matched | 131 (91.6%) | Found in both bank + Tally |
| Unmatched | 7 | In bank, not in Tally |
| Tally Only | 3 | In Tally, not in bank |
| Duplicates | 2 | Same amount+date twice in Tally |

---

## 4 Tabs in Detail

### Tab 1 — Unmatched (in bank, not in Tally)
For each entry:
- Date, Narration, Bank Ref, Amount
- Why missing (possible reason)
- **Suggested journal entry to pass in Tally**

### Tab 2 — Tally Only (in Tally, not in bank)
- Possible outstanding cheque not yet cleared
- Possible wrong entry in Tally
- Action: verify if cheque cleared, or delete wrong entry

### Tab 3 — Duplicates
- Same amount + same date appears twice in Tally
- Action: delete the duplicate voucher

### Tab 4 — Matched
- Full table of all clean matches
- Date | Bank narration | Tally narration | Amount | Status ✅

---

## Matching Algorithm (to build)

```python
def reconcile(bank_entries, tally_entries):
    matched = []
    unmatched = []
    tally_only = []
    duplicates = []

    for bank_entry in bank_entries:
        # 1. Exact match: same date + same amount
        match = find_exact(bank_entry, tally_entries)
        if match:
            matched.append((bank_entry, match))
            continue

        # 2. Fuzzy match: same amount, date ± 3 days
        near_match = find_near(bank_entry, tally_entries)
        if near_match:
            matched.append((bank_entry, near_match))  # flag as probable
            continue

        # 3. No match found
        unmatched.append(bank_entry)

    # Find Tally Only
    matched_tally = [m[1] for m in matched]
    tally_only = [t for t in tally_entries if t not in matched_tally]

    # Find duplicates in Tally
    duplicates = find_duplicates(tally_entries)

    return matched, unmatched, tally_only, duplicates

# Normalize narrations before matching:
# - Lowercase
# - Strip bank reference codes (e.g. "NEFT/12345/VENDOR" → "vendor")
# - Strip extra spaces
```

---

## To Build (Backend)

```
POST /api/bankrec
  → Accept 2 files (bank statement + tally ledger)
  → Parse both into list of {date, amount, narration, ref}
  → Run matching algorithm
  → Store result in bank_recon_sessions + bank_recon_entries
  → Return session_id

GET /api/bankrec/:session_id
  → Return full reconciliation results with 4 categories
```

---

## Related Notes
- [[05 - All Pages & Screens]]
- [[09 - Database Schema]]
- [[10 - API Endpoints]]
