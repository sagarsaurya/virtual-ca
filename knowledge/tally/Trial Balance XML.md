# Tally Trial Balance — Export Format Guide

---

## How to Export Trial Balance from Tally

### Steps in Tally Prime:
1. Gateway of Tally → Display More Reports → Trial Balance
2. Set period: 1 April to 31 March (full FY)
3. Press Alt+E → Export
4. Format: Excel (xlsx) or XML
5. Select all groups or specific groups

### Steps in Tally ERP 9:
1. Gateway of Tally → Display → Trial Balance
2. Set date range: F2
3. Alt+E → Export → Excel

---

## Trial Balance Excel Format (Typical Columns)

| Column | Content | Example |
|---|---|---|
| Particulars | Ledger name | HDFC Bank A/c |
| Parent Group | Tally group | Bank Accounts |
| Closing Balance Dr | Debit balance | 1,25,000.00 |
| Closing Balance Cr | Credit balance | — |
| Opening Balance Dr | Opening debit | 80,000.00 |
| Opening Balance Cr | Opening credit | — |

---

## Tally Groups — Complete Hierarchy

### Balance Sheet Groups (Liabilities side)
```
Capital Account
├── Partners' Capital A/c (for partnership)
├── Proprietor's Capital A/c (for proprietorship)
└── Share Capital (for company)

Reserves & Surplus
└── General Reserve, P&L Balance

Loans (Liability)
├── Secured Loans
│   └── Term Loan, Mortgage Loan
└── Unsecured Loans
    └── Loan from Director, Loan from Partner

Current Liabilities
├── Duties & Taxes
│   ├── TDS Payable
│   ├── CGST Payable
│   ├── SGST Payable
│   ├── IGST Payable
│   ├── PT Payable
│   ├── PF Payable
│   └── ESI Payable
├── Provisions
│   └── Provision for Expenses
└── Sundry Creditors
    └── Individual creditor ledgers
```

### Balance Sheet Groups (Assets side)
```
Fixed Assets
├── Land
├── Building
├── Plant and Machinery
├── Furniture and Fixtures
├── Vehicles
├── Computers
└── Office Equipment

Investments
└── Investment in FD, Shares, MF

Current Assets
├── Sundry Debtors
│   └── Individual debtor ledgers
├── Stock-in-Hand
│   ├── Opening Stock
│   └── Closing Stock
├── Cash-in-Hand
│   └── Cash A/c
├── Bank Accounts
│   ├── HDFC Bank A/c
│   └── SBI Current A/c
├── Loans & Advances (Asset)
│   ├── Advance to Suppliers
│   ├── Staff Advances
│   └── Security Deposit Paid
└── Other Current Assets
    ├── TDS Receivable
    ├── CGST Input (ITC)
    ├── SGST Input (ITC)
    ├── IGST Input (ITC)
    └── Prepaid Expenses
```

### P&L Groups
```
Sales Accounts
├── Sales (Local)
├── Sales (Interstate)
├── Sales (Export)
└── Service Income

Purchase Accounts
└── Purchases (Local)
    Purchases (Interstate)

Direct Income
└── Job Work Income

Indirect Income
├── Interest Received
├── Discount Received
├── Commission Received
└── Other Income

Direct Expenses
├── Freight Inward
├── Loading/Unloading
└── Direct Labour

Indirect Expenses
├── Salary
├── Rent
├── Electricity
├── Telephone
├── Professional Fees
├── Advertisement
├── Repairs and Maintenance
├── Travelling Expenses
├── Printing & Stationery
├── Insurance
├── Audit Fees
├── Bank Charges
└── Miscellaneous Expenses
```

---

## Common Tally Ledger Grouping Errors

| Ledger Name | Wrong Group (Common) | Correct Group | Impact |
|---|---|---|---|
| TDS Receivable | Duties & Taxes | Current Assets | Balance sheet wrong |
| TDS Payable | Current Assets | Duties & Taxes | Balance sheet wrong |
| CGST Input (ITC) | Duties & Taxes | Current Assets | Asset shown as liability |
| CGST Output | Current Assets | Duties & Taxes | Liability shown as asset |
| Capital A/c | Loans (Liability) | Capital Account | Equity shown as debt |
| Drawings | Indirect Expenses | Capital Account | Profit understated |
| Bank Interest Received | Indirect Expenses | Indirect Income | P&L wrong |
| Prepaid Expenses | Indirect Expenses | Current Assets | P&L wrong, asset missing |
| Advance from Customer | Sundry Creditors | Current Liabilities | Minor classification |
| Loan from Director | Capital Account | Loans (Liability) | Legal/compliance issue |
| Security Deposit Paid | Fixed Assets | Loans & Advances (Asset) | Asset misclassified |
| Interest Payable | Indirect Expenses | Current Liabilities | P&L understated |
| PT Payable | Current Liabilities | Duties & Taxes | Minor classification |

---

## Tally XML Export Format (for Integration)

```xml
<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Trial Balance</REPORTNAME>
        <STATICVARIABLES>
          <SVFROMDATE>20250401</SVFROMDATE>
          <SVTODATE>20260331</SVTODATE>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>
```

**Response structure:**
```xml
<LEDGER NAME="HDFC Bank A/c" PARENT="Bank Accounts">
  <OPENINGBALANCE>80000.00</OPENINGBALANCE>
  <CLOSINGBALANCE>125000.00</CLOSINGBALANCE>
</LEDGER>
```

---

*Source: Tally Solutions Documentation | Tally Prime Help | VirtualCA Integration Guide*
