# 📏 Ledger Analysis Rules

**← [[00 - Home]]**

---

## Core Rule Table

| Ledger Pattern | Correct Group | Common Wrong Group | Severity |
|---|---|---|---|
| TDS Receivable | Current Assets | Duties & Taxes | 🔴 Critical |
| TDS Payable | Duties & Taxes | Current Assets | 🔴 Critical |
| GST Input Credit (ITC) | Current Assets | Duties & Taxes | 🔴 Critical |
| GST Output Payable | Duties & Taxes | Current Assets | 🔴 Critical |
| Bank Interest Received | Indirect Incomes | Indirect Expenses | 🔴 Critical |
| Capital / Partner's Capital | Capital Account | Loans (Liability) | 🔴 Critical |
| Drawings | Capital Account | Indirect Expenses | 🔴 Critical |
| Prepaid Expenses | Current Assets | Indirect Expenses | 🔴 Critical |
| Loan from Director | Loans (Liability) | Capital Account | 🔴 Critical |
| Interest Payable | Current Liabilities | Indirect Expenses | 🔴 Critical |
| Difference in Opening Bal | Flag (Dr ≠ 0) | — | 🔴 Critical |
| Salary | Indirect Expenses | Direct Expenses | 🟡 Review |
| Depreciation | Indirect Expenses | Direct Expenses | 🟡 Review |
| Accrued Income | Current Assets | Indirect Incomes | 🟡 Review |
| Security Deposit (paid) | Loans & Advances (Asset) | Fixed Assets | 🟡 Review |
| Security Deposit (received) | Current Liabilities | Loans (Liability) | 🟡 Review |
| Advance from Customer | Current Liabilities | Sundry Creditors | 🟡 Review |
| Debtor with Credit balance | Flag for review | — | 🟡 Review |
| Creditor with Debit balance | Flag for review | — | 🟡 Review |
| PT Payable | Duties & Taxes | Current Liabilities | 🟡 Review |

---

## Additional Checks

| Check | Condition | Severity |
|---|---|---|
| Opening Balance mismatch | Dr total ≠ Cr total | 🔴 Critical |
| Suspense Account balance | Non-zero balance | 🔴 Critical |
| Sales Returns > Sales | Returns exceed sales | 🔴 Critical |
| Dormant ledger | Zero balance + no transactions in FY | 🟡 Review |
| Round number transaction | Exactly ₹5,00,000 / ₹10,00,000 etc. | 🟡 Review |

---

## Accounting Rules Referenced

| Rule | What It Means |
|---|---|
| **Matching Principle** | Income and expenses must be recorded in the same period |
| **Double Entry** | Every debit must have an equal credit |
| **AS-2** | Valuation of Inventories |
| **AS-9** | Revenue Recognition |
| **AS-10** | Property, Plant and Equipment |
| **Going Concern** | Assets and liabilities must be properly classified |

---

## How the Engine Works (to build)

```python
def analyze_ledger(ledger_name, ledger_group, closing_balance, dr_cr):
    # 1. Fuzzy match ledger name against rule table
    # 2. Check if current group matches expected group
    # 3. If mismatch → flag with severity + correct group + rule violated
    # 4. Check balance anomalies (credit balance on debtor, etc.)
    # 5. Return: severity, correct_group, rule_violated, tally_fix_path

# Fuzzy matching examples:
# "TDS Rec.", "T.D.S. Receivable", "TDS A/c" → all match "TDS Receivable"
# Use: rapidfuzz library for fuzzy string matching
```

---

## Tally Fix Paths (examples)

| Error | Tally Navigation |
|---|---|
| Wrong ledger group | Gateway → Accounts Info → Ledgers → Alter → [Ledger name] → Change Group |
| Wrong voucher entry | Gateway → Day Book → Find voucher → Alter |
| Opening balance issue | Gateway → Accounts Info → Ledgers → Alter → Opening Balance |

---

## Related Notes
- [[03 - Features Overview]]
- [[05 - All Pages & Screens]]
- [[07 - Export to Tally]]
