# GST Audit Guide — Step by Step

---

## What is GST Audit?

Three types:
1. **Self-Audit** — business checks its own books vs GST returns
2. **Departmental Audit (Section 65)** — GST officer audits registered person
3. **Special Audit (Section 66)** — CA/CMA appointed by GST Commissioner

This guide focuses on **Self-Audit** — what VirtualCA does.

---

## GST Audit Checklist

### Step 1 — Registration Check
- [ ] GSTIN valid and active
- [ ] All business places registered
- [ ] GSTIN mentioned on all invoices
- [ ] Profile updated (address, bank account, authorized signatory)

### Step 2 — Invoice Compliance
- [ ] All mandatory fields present on every invoice (Rule 46)
- [ ] Invoice serial numbers consecutive and unique
- [ ] Invoices issued within 30 days of supply (services)
- [ ] HSN/SAC codes correct
- [ ] Tax rates correct as per GST rate schedules

### Step 3 — GSTR-1 vs Books Reconciliation
- [ ] All B2B invoices in GSTR-1 match books exactly
- [ ] All B2C summary matches books
- [ ] Debit notes and credit notes reported
- [ ] Nil-rated and exempt supplies reported separately
- [ ] Export invoices with shipping bill numbers

### Step 4 — GSTR-3B vs GSTR-1 Reconciliation
- [ ] Output tax in 3B = Output tax in GSTR-1
- [ ] Differences explained (amendments, debit/credit notes)
- [ ] No excess ITC claimed over GSTR-2B

### Step 5 — ITC Verification
- [ ] ITC in books = ITC in GSTR-2B (no excess)
- [ ] ITC on blocked items (Section 17(5)) not claimed
- [ ] ITC on ineligible expenses (personal, CSR) not claimed
- [ ] 180-day rule checked (reversal for unpaid suppliers)
- [ ] ITC proportionate reversal done for exempt supplies

### Step 6 — RCM Verification
- [ ] All RCM transactions identified
- [ ] RCM tax paid in cash (cannot use ITC for RCM payment)
- [ ] ITC of RCM re-claimed after payment

### Step 7 — E-Way Bill Compliance
- [ ] All goods movements > ₹50,000 have e-way bills
- [ ] E-way bill numbers recorded in delivery records
- [ ] No expired e-way bills during transit

### Step 8 — Annual Reconciliation (for GSTR-9)
- [ ] Sum of all GSTR-1 = Annual GSTR-9 outward supply
- [ ] Sum of all GSTR-3B tax paid = Annual GSTR-9 tax paid
- [ ] Any missed invoices or ITC added in GSTR-9
- [ ] GSTR-9C reconciliation prepared if turnover > ₹5 crore

---

## Common GST Audit Findings

| Finding | Root Cause | Action Required |
|---|---|---|
| ITC > GSTR-2B | Supplier filed late or not filed | Reverse excess ITC, follow up supplier |
| Output tax mismatch GSTR-1 vs 3B | Invoice missed in GSTR-1 | Amend GSTR-1, pay differential |
| ITC on blocked items | Accounting error | Reverse ITC + pay interest 24% |
| RCM not paid | Unawareness | Pay RCM + interest 18% |
| E-way bill not generated | Process failure | Penalty ₹10,000 or tax amount |
| Export without LUT | Procedural error | File refund claim with IGST paid |
| HSN code wrong | Data entry error | Amend invoice, correct GSTR-1 |
| Late GSTR-1 filing | Delayed filing | Pay late fee ₹50/day |
| Late GSTR-3B filing | Cash flow issues | Pay late fee + 18% interest |

---

## Red Flags That Trigger GST Notice

1. **GSTR-1 vs GSTR-3B mismatch** — system auto-generates ASMT-10
2. **ITC claimed > 110% of GSTR-2B** — system blocks filing
3. **Turnover in GSTR-1 much lower than in IT returns** — cross-verification
4. **Sudden spike in ITC claims** — triggers scrutiny
5. **Regular nil returns but bank shows large credits** — risk-based audit selection
6. **Exports without LUT but no IGST paid** — customs mismatch

---

## GST Reconciliation Statement Format

| Item | As per Books | As per GST Returns | Difference | Reason |
|---|---|---|---|---|
| Outward supplies (taxable) | | | | |
| Outward supplies (exempt) | | | | |
| Output CGST | | | | |
| Output SGST | | | | |
| Output IGST | | | | |
| ITC claimed (CGST) | | | | |
| ITC claimed (SGST) | | | | |
| ITC claimed (IGST) | | | | |
| Net tax paid | | | | |

---

*Source: ICAI GST Audit Guide | CBIC GST Audit Manual*
