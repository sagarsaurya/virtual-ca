# Tally Day Book — Export Format Guide

---

## What is the Day Book?

The Day Book in Tally shows ALL vouchers/transactions in date order — every single entry made in Tally for the selected period.

This is the most important file for audit because it shows every transaction, not just balances.

---

## How to Export Day Book from Tally

### Tally Prime:
1. Gateway of Tally → Display More Reports → Day Book
2. Set period: F2 → set from 1 April to 31 March
3. Alt+E → Export → Excel or XML
4. Include all voucher types

### Tally ERP 9:
1. Gateway of Tally → Display → Day Book
2. F2 to change period
3. Alt+E → Export

---

## Day Book Excel Format (Columns)

| Column | Content | Example |
|---|---|---|
| Date | Voucher date | 05-Apr-2025 |
| Voucher Type | Type of entry | Payment |
| Voucher No | Reference number | PV-001 |
| Narration | Description | Payment to Sharma & Co |
| Debit Account | Account debited | Sharma & Co |
| Credit Account | Account credited | HDFC Bank A/c |
| Amount | Transaction amount | 25,000.00 |
| Dr Amount | Debit side | 25,000.00 |
| Cr Amount | Credit side | — |

---

## Tally Voucher Types

| Voucher Type | Tally Code | What It Records |
|---|---|---|
| Sales | Sales | Customer invoices |
| Purchase | Purchase | Supplier bills |
| Receipt | Receipt | Money received from customers |
| Payment | Payment | Money paid to suppliers/expenses |
| Contra | Contra | Cash↔Bank transfers |
| Journal | Journal | Adjusting entries, provisions |
| Debit Note | Debit Note | Purchase returns or debit to party |
| Credit Note | Credit Note | Sales returns or credit to party |
| Memo | Memo | Non-accounting (tracking) entries |

---

## Standard Voucher Entries in Tally

### Sales Invoice
```
Dr: Customer A/c (Sundry Debtors)     ₹1,18,000
  Cr: Sales A/c                        ₹1,00,000
  Cr: CGST Output A/c                     ₹9,000
  Cr: SGST Output A/c                     ₹9,000
Narration: Invoice No. INV-001 dated 05-Apr-2025
```

### Purchase Invoice
```
Dr: Purchases A/c                     ₹1,00,000
Dr: CGST Input A/c                       ₹9,000
Dr: SGST Input A/c                       ₹9,000
  Cr: Supplier A/c (Sundry Creditors)  ₹1,18,000
Narration: Bill No. PB-001 from Supplier dated 05-Apr-2025
```

### Payment to Supplier
```
Dr: Supplier A/c (Sundry Creditors)    ₹1,18,000
  Cr: HDFC Bank A/c                    ₹1,16,820
  Cr: TDS Payable A/c (194C)              ₹1,180
Narration: Payment against Bill PB-001, TDS deducted @ 1%
```

### Receipt from Customer
```
Dr: HDFC Bank A/c                      ₹1,18,000
  Cr: Customer A/c (Sundry Debtors)    ₹1,18,000
Narration: Receipt against Invoice INV-001
```

### Salary Payment
```
Dr: Salary A/c                           ₹50,000
  Cr: PT Payable A/c                        ₹200
  Cr: PF Payable A/c (Employee share)     ₹1,800
  Cr: TDS Payable A/c (192)               ₹2,000
  Cr: HDFC Bank A/c                      ₹46,000
Narration: Salary for April 2025 — Employee Name
```

### TDS Deposit
```
Dr: TDS Payable A/c                      ₹2,000
  Cr: HDFC Bank A/c                       ₹2,000
Narration: TDS deposit for April 2025 via challan No. XXXXX
```

### GST Payment (GSTR-3B)
```
Dr: CGST Output A/c                      ₹9,000
Dr: SGST Output A/c                      ₹9,000
  Cr: CGST Input A/c                      ₹7,000
  Cr: SGST Input A/c                      ₹7,000
  Cr: HDFC Bank A/c                        ₹4,000
Narration: GST payment for April 2025 — Net liability ₹4,000
```

### Depreciation Entry (Year End)
```
Dr: Depreciation A/c                    ₹15,000
  Cr: Accumulated Depreciation A/c      ₹15,000
  (Or directly reduce asset: Cr: Computer A/c)
Narration: Depreciation for FY 2025-26 @ 40% on computers
```

### Contra — Cash Deposited in Bank
```
Dr: HDFC Bank A/c                       ₹50,000
  Cr: Cash A/c                          ₹50,000
Narration: Cash deposited in bank on 10-Apr-2025
```

---

## Common Day Book Errors to Flag in Audit

| Error | How to Detect | Severity |
|---|---|---|
| Payment in cash > ₹10,000 | Filter Payment vouchers, check Cr to Cash A/c > ₹10,000 | Critical (40A(3)) |
| Payment without TDS | Large payments to contractors/professionals, no TDS entry | Critical (40a(ia)) |
| Round number transactions | Filter amounts ending in 00,000 | Review |
| Same narration multiple times | Duplicate voucher check | Critical |
| Journal entries with no narration | Missing documentation | Review |
| Contra entries between same bank accounts | Circular transactions | Review |
| Debit to Capital A/c (Drawings not in Capital) | Drawings misclassified | Review |
| Late date entries (March entries in April) | Prior period items | Review |

---

*Source: Tally Prime Help | Tally Solutions | VirtualCA Audit Engine*
