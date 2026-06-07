# 📤 Export Back to Tally

**← [[00 - Home]]**

---

## Overview

After reviewing all errors and corrections, export them directly back into Tally. Three formats supported.

---

## Export Formats

### 1. Tally XML (.xml)
- Full Tally-compatible import file
- Contains corrected vouchers and ledger groups
- **Import in Tally:** Gateway of Tally → Import Data → Vouchers → Select XML file
- Best for: full correction import with all details

### 2. Excel Correction Sheet (.xlsx)
- Structured spreadsheet with all corrections listed
- Columns: Ledger Name | Current Group | Correct Group | Dr/Cr Entry | Narration
- Best for: sharing with accountant who will make changes manually

### 3. Tally Import CSV (.csv)
- Simplified format for basic ledger corrections
- **Import in Tally:** Gateway of Tally → Import Data → Masters
- Best for: quick ledger group corrections only

---

## Export Modal (UI)

Shows:
- "7 corrections ready to export"
- 3 buttons: Tally XML | Excel Correction Sheet | Tally Import CSV
- XML import step-by-step instructions
- Success toast after selecting format

---

## XML Import Instructions (shown in app)

```
Step 1: Open Tally
Step 2: Gateway of Tally → Import Data
Step 3: Select "Vouchers"
Step 4: Browse and select the downloaded .xml file
Step 5: Press Enter to import
Step 6: Verify imported entries in Day Book
```

---

## To Build (Backend)

```python
# XML generation
GET /api/uploads/:id/export/xml
→ Generate Tally-format XML from ledger_results where status='resolved' or status='open'
→ Include: voucher corrections, ledger group changes

# Excel generation
GET /api/uploads/:id/export/excel
→ pandas DataFrame → openpyxl → download .xlsx

# CSV generation
GET /api/uploads/:id/export/csv
→ Simple CSV with corrections
```

---

## Related Notes
- [[06 - Fix Workflow & Team Collaboration]]
- [[11 - Ledger Analysis Rules]]
- [[09 - Database Schema]]
