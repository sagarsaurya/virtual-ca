# Tally Voucher Samples — All Common Business Scenarios

---

## GST Scenarios

### Interstate Sale (IGST)
```
Dr: Customer A/c (Delhi)              ₹1,18,000
  Cr: Sales A/c                       ₹1,00,000
  Cr: IGST Output A/c                   ₹18,000
Narration: Interstate sale to Delhi customer, Invoice INV-001
```

### Import Purchase (with customs duty)
```
Dr: Purchases A/c                     ₹1,00,000
Dr: Custom Duty A/c (Direct Expense)    ₹10,000
Dr: IGST Input A/c (if claimable)       ₹18,000
  Cr: Supplier A/c (Foreign)          ₹1,10,000
  Cr: HDFC Bank A/c                     ₹18,000
```

### RCM (Reverse Charge on GTA)
```
Dr: Freight Expense A/c                ₹10,000
Dr: CGST Input A/c (RCM)                  ₹900
Dr: SGST Input A/c (RCM)                  ₹900
  Cr: GTA Party A/c                   ₹10,000
  Cr: CGST Payable (RCM)                  ₹900
  Cr: SGST Payable (RCM)                  ₹900
Narration: GTA services — RCM applicable @ 18%
```
*(RCM paid in cash, ITC reclaimable in same period)*

---

## TDS Scenarios

### Professional Fees with TDS 194J
```
Dr: Professional Fees A/c             ₹1,00,000
  Cr: CA Firm A/c (Creditor)            ₹90,000
  Cr: TDS Payable A/c (194J)           ₹10,000
Narration: Audit fees — TDS @ 10% u/s 194J
```

### Contract Payment with TDS 194C
```
Dr: Contract Work A/c                  ₹50,000
  Cr: Contractor A/c                   ₹49,500
  Cr: TDS Payable A/c (194C)              ₹500
Narration: Maintenance contract — TDS @ 1% (individual) u/s 194C
```

### Rent Payment with TDS 194I
```
Dr: Rent A/c                           ₹25,000
  Cr: Landlord A/c                     ₹22,500
  Cr: TDS Payable A/c (194I)            ₹2,500
Narration: Office rent for April 2025 — TDS @ 10% u/s 194I
```

---

## Salary Scenarios

### Full Salary Entry with All Deductions
```
Dr: Salary A/c (Gross)                 ₹50,000
  Cr: PF Payable A/c (Employee 12%)     ₹6,000
  Cr: ESI Payable A/c (Employee 0.75%)    ₹375
  Cr: PT Payable A/c                       ₹200
  Cr: TDS Payable A/c (192)             ₹2,000
  Cr: Salary Payable A/c               ₹41,425
Narration: Salary for April 2025 — All deductions
```

### Salary Actually Paid
```
Dr: Salary Payable A/c                 ₹41,425
  Cr: HDFC Bank A/c                   ₹41,425
Narration: Salary disbursement for April 2025
```

### Employer PF Contribution
```
Dr: PF Expense A/c (Employer 12%)      ₹6,000
  Cr: PF Payable A/c                   ₹6,000
Narration: Employer PF contribution for April 2025
```

### PF Deposit (by 15th of next month)
```
Dr: PF Payable A/c (Employee + Employer)  ₹12,000
  Cr: HDFC Bank A/c                   ₹12,000
Narration: PF deposit for April 2025 — Employee ₹6,000 + Employer ₹6,000
```

### PT Deposit (West Bengal — by 21st)
```
Dr: PT Payable A/c                       ₹200
  Cr: HDFC Bank A/c                       ₹200
Narration: Professional Tax deposit for April 2025 via GRIPS portal
```

---

## Year-End Adjusting Entries

### Closing Stock
```
Dr: Stock-in-Hand A/c (Balance Sheet)  ₹5,00,000
  Cr: Closing Stock A/c (P&L)          ₹5,00,000
Narration: Closing stock as per physical count on 31 March 2026
```

### Provision for Expenses (Accrued Expenses)
```
Dr: Electricity Expense A/c            ₹15,000
  Cr: Electricity Payable A/c          ₹15,000
Narration: Electricity bill for March 2026 — not yet received
```

### Provision for Doubtful Debts
```
Dr: Bad Debt Expense A/c               ₹10,000
  Cr: Provision for Doubtful Debts A/c ₹10,000
Narration: Provision @ 10% on debts outstanding > 6 months
```

### Prepaid Expenses (for advance payments)
```
Dr: Prepaid Insurance A/c (Current Asset)  ₹6,000
  Cr: Insurance Expense A/c               ₹6,000
Narration: Insurance premium for Apr-Sep 2026 — pre-paid portion
```

### Interest Accrued (on FD)
```
Dr: Interest Receivable A/c            ₹5,000
  Cr: Interest Income A/c              ₹5,000
Narration: Interest accrued on FD for March 2026 — not yet credited
```

---

## Bank Reconciliation Entries

### Bank charges (not in books, only in bank statement)
```
Dr: Bank Charges A/c                     ₹500
  Cr: HDFC Bank A/c                       ₹500
Narration: Bank charges for April 2025 — per bank statement
```

### Interest credited in bank not in books
```
Dr: HDFC Bank A/c                       ₹2,000
  Cr: Bank Interest Received A/c        ₹2,000
Narration: Bank interest for Q1 2025-26 — per bank statement
```

---

*Source: Tally Solutions | VirtualCA Standard Journal Entries | CA Practice Manual*
