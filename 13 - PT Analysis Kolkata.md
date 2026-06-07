# 🏙️ PT Analysis — Kolkata / West Bengal

**← [[00 - Home]]**

---

## What is Professional Tax (PT)?

Professional Tax (PT) is a **state-level tax** deducted from employee salaries every month.
In West Bengal, it is governed by the **West Bengal State Tax on Professions, Trades, Callings and Employments Act, 1979**.

> PT is **not the same as TDS** — it is a state tax, deposited to the WB government via the **Grips portal**, not the Income Tax department.

---

## West Bengal PT Slab Table

| Gross Monthly Salary | PT Deduction |
|---|---|
| Up to ₹10,000 | **Nil** |
| ₹10,001 – ₹15,000 | **₹110/month** |
| ₹15,001 – ₹25,000 | **₹130/month** |
| ₹25,001 – ₹40,000 | **₹150/month** |
| Above ₹40,000 | **₹200/month** |

**Maximum PT:** ₹200/month = ₹2,400/year per employee

---

## Summary Cards (UI)

| Card | Demo Value |
|---|---|
| PT Deducted | ₹2,640 |
| PT Deposited | ₹0 |
| Due Date | 21st of every month |
| Portal | Grips WB (wbifms.gov.in) |

---

## Employee-Wise PT Table (UI)

| Employee | Gross Salary | Slab | PT Due |
|---|---|---|---|
| Ravi Kumar | ₹45,000 | Above ₹40,000 | ₹200 |
| Priya Das | ₹28,000 | ₹25,001–₹40,000 | ₹150 |
| Amit Saha | ₹18,000 | ₹15,001–₹25,000 | ₹130 |
| Sunita Roy | ₹12,000 | ₹10,001–₹15,000 | ₹110 |
| Mohan Lal | ₹8,000 | Up to ₹10,000 | Nil |

---

## Tally Journal Entries

### Entry 1 — PT Deduction on Salary Date
```
Dr  Salary A/c                   ₹2,640
    Cr  PT Payable (Duties & Taxes)      ₹2,640
Narration: PT deducted from employee salaries for March 2026
```

### Entry 2 — PT Deposit via Grips by 21st
```
Dr  PT Payable (Duties & Taxes)  ₹2,640
    Cr  HDFC Bank                        ₹2,640
Narration: PT deposited via Grips portal for March 2026
```

---

## Grips Deposit — Step by Step

1. Go to **wbifms.gov.in**
2. Click **Grips (Government Receipt Portal System)**
3. Select **"Professional Tax"**
4. Enter: Employer Registration Number, Period, Amount
5. Pay via Net Banking / UPI / Debit Card
6. Download challan
7. Keep challan for Tally entry narration reference

---

## Important Notes

- PT must be deposited by **21st of every month**
- Penalty for late deposit: interest + penalty from WB Government
- PT Payable ledger in Tally should be under **Duties & Taxes** group
- After deposit, PT Payable balance should be ₹0
- Annual PT return filing also required

---

## To Build (Backend)

```python
def calculate_pt(employee_salary):
    if employee_salary <= 10000:
        return 0
    elif employee_salary <= 15000:
        return 110
    elif employee_salary <= 25000:
        return 130
    elif employee_salary <= 40000:
        return 150
    else:
        return 200

# PT Engine:
# 1. Pull salary ledger data from upload
# 2. Identify employee-wise salary amounts
# 3. Apply WB slab per employee
# 4. Check if PT Payable ledger balance = 0 (deposited) or > 0 (pending)
# 5. Flag if deposit date > 21st of month
```

---

## Related Notes
- [[12 - TDS Analysis]]
- [[15 - Compliance Calendar]]
- [[11 - Ledger Analysis Rules]]
