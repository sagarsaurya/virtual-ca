import pandas as pd
import json
from datetime import datetime

# ── THRESHOLDS (Indian Tax Law) ──────────────────────────────────────────────
CASH_EXPENSE_LIMIT   = 10000    # Sec 40A(3) — disallowed above this
CASH_RECEIPT_LIMIT   = 200000   # Sec 269ST — prohibited above this
LOAN_CASH_LIMIT      = 20000    # Sec 269SS/269T
TDS_194J_THRESHOLD   = 50000    # professional fees
TDS_194C_THRESHOLD   = 30000    # single contractor payment
TDS_194I_THRESHOLD   = 240000   # rent per year

# ── LEDGER RULES (name pattern → correct group) ──────────────────────────────
LEDGER_RULES = [
    {"pattern": ["tds receivable","tds rec","t.d.s receivable","income tax receivable","tds refund"],
     "correct_group": "Current Assets", "wrong_groups": ["Duties & Taxes","Current Liabilities"], "severity": "Critical",
     "rule": "TDS receivable is a current asset — money owed to you by Income Tax dept"},
    {"pattern": ["tds payable","tds on","tax deducted"],
     "correct_group": "Duties & Taxes", "wrong_groups": ["Current Assets","Current Liabilities"], "severity": "Critical",
     "rule": "TDS payable is a statutory liability — must be under Duties & Taxes"},
    {"pattern": ["gst input","igst input","cgst input","sgst input","gst itc","input tax credit"],
     "correct_group": "Current Assets", "wrong_groups": ["Duties & Taxes"], "severity": "Critical",
     "rule": "GST Input Credit is a current asset — it is recoverable from govt"},
    {"pattern": ["gst output","igst output","cgst output","sgst output","gst payable"],
     "correct_group": "Duties & Taxes", "wrong_groups": ["Current Assets"], "severity": "Critical",
     "rule": "GST Output is a statutory liability"},
    {"pattern": ["bank interest received","interest received","interest income"],
     "correct_group": "Indirect Incomes", "wrong_groups": ["Indirect Expenses","Direct Expenses"], "severity": "Critical",
     "rule": "Bank interest is income — books it as expense reduces profit wrongly"},
    {"pattern": ["credit card","hdfc card","icici card","sbi card","axis card","amex"],
     "correct_group": "Sundry Creditors", "wrong_groups": ["Indirect Expenses","Direct Expenses"], "severity": "Critical",
     "rule": "Credit card outstanding is a liability (money owed), not an expense"},
    {"pattern": ["drawings","drawing"],
     "correct_group": "Capital Account", "wrong_groups": ["Indirect Expenses","Direct Expenses"], "severity": "Critical",
     "rule": "Drawings is a reduction of capital — not a business expense"},
    {"pattern": ["prepaid","prepaid expense","advance rent paid"],
     "correct_group": "Current Assets", "wrong_groups": ["Indirect Expenses","Direct Expenses"], "severity": "Critical",
     "rule": "Prepaid expenses are assets — expense not yet incurred"},
    {"pattern": ["security deposit","refundable deposit"],
     "correct_group": "Loans & Advances (Asset)", "wrong_groups": ["Fixed Assets","Indirect Expenses"], "severity": "Review",
     "rule": "Security deposits are refundable advances, not fixed assets"},
    {"pattern": ["advance from customer","customer advance","advance receipt"],
     "correct_group": "Current Liabilities", "wrong_groups": ["Sundry Creditors"], "severity": "Review",
     "rule": "Customer advances are current liabilities — goods/service not yet delivered"},
    {"pattern": ["pt payable","professional tax payable","p.tax"],
     "correct_group": "Duties & Taxes", "wrong_groups": ["Current Liabilities"], "severity": "Review",
     "rule": "PT Payable is a statutory duty — must be under Duties & Taxes"},
    {"pattern": ["salary payable","salary outstanding"],
     "correct_group": "Current Liabilities", "wrong_groups": ["Indirect Expenses"], "severity": "Review",
     "rule": "Salary payable is a current liability — salary incurred but not yet paid"},
]

# ── WB PT SLABS ──────────────────────────────────────────────────────────────
def calc_pt(salary):
    if salary <= 10000:   return 0
    elif salary <= 15000: return 110
    elif salary <= 25000: return 130
    elif salary <= 40000: return 150
    else:                 return 200

# ── PARSE TRIAL BALANCE ──────────────────────────────────────────────────────
def parse_trial_balance(filepath):
    df = pd.read_excel(filepath, header=None)
    ledgers = []
    current_group = None
    GROUP_NAMES = [
        'Capital Account','Loans (Liability)','Current Liabilities','Duties & Taxes',
        'Sundry Creditors','Fixed Assets','Investments','Current Assets',
        'Deposits (Asset)','Loans & Advances (Asset)','Sundry Debtors',
        'Cash-in-Hand','Bank Accounts','Direct Incomes','Direct Expenses',
        'Indirect Incomes','Indirect Expenses','Suspense A/c','Suspense'
    ]
    for _, row in df.iterrows():
        name = str(row[0]).strip() if pd.notna(row[0]) else ''
        try:
            debit  = float(row[1]) if pd.notna(row[1]) else 0.0
        except: debit = 0.0
        try:
            credit = float(row[2]) if pd.notna(row[2]) else 0.0
        except: credit = 0.0
        if not name or name in ['nan','Particulars','Grand Total','Debit','Credit',
                                 'Closing Balance','1-Apr-25 to 31-Mar-26',
                                 'AJAY KUMAR LADDHA','Trial Balance']:
            continue
        # skip rows where col1 is text (header rows)
        try:
            if pd.notna(row[1]) and not str(row[1]).replace('.','').replace('-','').isnumeric():
                continue
        except: pass
        if name in GROUP_NAMES:
            current_group = name
            continue
        if current_group:
            ledgers.append({
                'name': name,
                'group': current_group,
                'debit': debit,
                'credit': credit,
                'balance': debit - credit
            })
    return ledgers

# ── PARSE DAYBOOK ─────────────────────────────────────────────────────────────
def parse_daybook(filepath):
    df = pd.read_excel(filepath, header=None)
    df = df[5:].reset_index(drop=True)
    df.columns = ['Date','Particulars','VchType','VchNo','Debit','Credit']
    df['Debit']  = pd.to_numeric(df['Debit'],  errors='coerce').fillna(0)
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    df['Date']   = pd.to_datetime(df['Date'],  errors='coerce')
    df['Particulars'] = df['Particulars'].astype(str).str.strip()
    df['VchType']     = df['VchType'].astype(str).str.strip()
    return df

# ── MODULE 1: LEDGER CLASSIFICATION ──────────────────────────────────────────
def audit_ledger_classification(ledgers):
    findings = []
    for ledger in ledgers:
        name_lower = ledger['name'].lower()
        for rule in LEDGER_RULES:
            if any(p in name_lower for p in rule['pattern']):
                if ledger['group'] in rule['wrong_groups']:
                    findings.append({
                        'severity': rule['severity'],
                        'ledger': ledger['name'],
                        'current_group': ledger['group'],
                        'correct_group': rule['correct_group'],
                        'balance': abs(ledger['balance']),
                        'rule': rule['rule'],
                        'fix': f"Gateway → Accounts Info → Ledgers → Alter → {ledger['name']} → Change Group to {rule['correct_group']}"
                    })
                break
    return findings

# ── MODULE 2: OUTSTANDING AMOUNTS ────────────────────────────────────────────
def audit_outstanding(ledgers):
    findings = []
    for ledger in ledgers:
        name  = ledger['name']
        group = ledger['group']
        bal   = ledger['balance']
        # Suspense non-zero
        if 'suspense' in name.lower() and (ledger['debit'] > 0 or ledger['credit'] > 0):
            findings.append({
                'type': 'suspense', 'ledger': name,
                'amount': abs(ledger['credit'] or ledger['debit']),
                'question': f'Suspense account has Rs.{abs(ledger["credit"] or ledger["debit"]):,.0f} balance. What is this for? Identify and move to correct ledger before finalising books.',
                'severity': 'Critical'
            })
        # Debtor with credit balance (unusual)
        if group == 'Sundry Debtors' and ledger['credit'] > ledger['debit'] and ledger['credit'] > 0:
            findings.append({
                'type': 'debtor_credit_balance', 'ledger': name,
                'amount': ledger['credit'] - ledger['debit'],
                'question': f'{name} is a debtor but has a credit balance of Rs.{(ledger["credit"]-ledger["debit"]):,.0f}. Is this an advance received? If yes, move to Current Liabilities.',
                'severity': 'Review'
            })
        # Large outstanding debtor
        if group == 'Sundry Debtors' and ledger['debit'] > 50000:
            findings.append({
                'type': 'outstanding_debtor', 'ledger': name,
                'amount': ledger['debit'],
                'question': f'Rs.{ledger["debit"]:,.0f} is outstanding from {name}. Has this been received? If yes, add receipt entry. If no — is recovery being pursued? Should this be written off as bad debt?',
                'severity': 'Review'
            })
        # Creditor with debit balance
        if group == 'Sundry Creditors' and ledger['debit'] > ledger['credit'] and ledger['debit'] > 0:
            findings.append({
                'type': 'creditor_debit_balance', 'ledger': name,
                'amount': ledger['debit'] - ledger['credit'],
                'question': f'{name} is a creditor but shows a debit balance of Rs.{(ledger["debit"]-ledger["credit"]):,.0f}. Is this an advance paid? If yes, move to Loans & Advances (Asset).',
                'severity': 'Review'
            })
        # Opening balance difference
        if 'difference in opening' in name.lower() and (ledger['debit'] > 0 or ledger['credit'] > 0):
            amt = ledger['debit'] or ledger['credit']
            findings.append({
                'type': 'opening_balance_diff', 'ledger': name,
                'amount': abs(amt),
                'question': f'Difference in Opening Balances = Rs.{abs(amt):,.0f}. This means last year closing balance does not match this year opening balance. Needs investigation.',
                'severity': 'Critical'
            })
    return findings

# ── MODULE 3: CASH VIOLATIONS ────────────────────────────────────────────────
def audit_cash_violations(daybook):
    findings = []
    bank_keywords = ['hdfc','icici','sbi','axis','kotak','bank','neft','rtgs','upi','imps',
                     'zerodha','loan','emi','investment','mutual fund','ppf','nps','laddha',
                     'education','anjali','mridula','arun','manoj','milapchand','sanjay',
                     'anand rathi','tapinvest','niraj','am mobile','silver spring','anil gupta',
                     'aikigai','rishikesh','e-biz','icici prudential']
    cash_vouchers = daybook[daybook['VchType'].isin(['Payment','Receipt'])].copy()
    cash_vouchers = cash_vouchers[~cash_vouchers['Particulars'].str.lower().str.contains(
        '|'.join(bank_keywords), na=False
    )]
    for _, row in cash_vouchers.iterrows():
        # Large cash expense (Sec 40A(3))
        if row['Debit'] > CASH_EXPENSE_LIMIT:
            findings.append({
                'severity': 'Critical',
                'date': str(row['Date'].date()) if pd.notna(row['Date']) else '',
                'party': row['Particulars'],
                'amount': row['Debit'],
                'type': 'cash_expense',
                'section': '40A(3)',
                'issue': f"Cash payment of Rs.{row['Debit']:,.0f} to {row['Particulars']} exceeds Rs.10,000 limit",
                'impact': f"Rs.{row['Debit']:,.0f} will be disallowed in ITR computation"
            })
        # Large cash receipt (Sec 269ST)
        if row['Credit'] > CASH_RECEIPT_LIMIT:
            findings.append({
                'severity': 'Critical',
                'date': str(row['Date'].date()) if pd.notna(row['Date']) else '',
                'party': row['Particulars'],
                'amount': row['Credit'],
                'type': 'cash_receipt',
                'section': '269ST',
                'issue': f"Cash receipt of Rs.{row['Credit']:,.0f} from {row['Particulars']} exceeds Rs.2,00,000 limit",
                'impact': f"Penalty risk = 100% of amount = Rs.{row['Credit']:,.0f}"
            })
    return findings

# ── MODULE 4: LOAN AUDIT ──────────────────────────────────────────────────────
def audit_loans(ledgers, daybook):
    findings = []
    loan_groups = ['Loans (Liability)', 'Loans & Advances (Asset)']
    for ledger in ledgers:
        if ledger['group'] in loan_groups and abs(ledger['balance']) > 10000:
            bal = abs(ledger['balance'])
            findings.append({
                'ledger': ledger['name'],
                'group': ledger['group'],
                'balance': bal,
                'documents_required': [
                    f"Bank statement showing loan {'receipt' if ledger['group']=='Loans (Liability)' else 'disbursement'} of Rs.{bal:,.0f}",
                    "Loan agreement with repayment terms and interest rate",
                    "If Director loan — Board resolution + compliance with Sec 269SS (must be via banking channel)"
                ],
                'question': f"Loan account '{ledger['name']}' has balance of Rs.{bal:,.0f}. Please provide bank statement and loan agreement for verification."
            })
    return findings

# ── MODULE 5: LARGE EXPENSE CHECK ────────────────────────────────────────────
def audit_large_expenses(daybook, threshold=100000):
    findings = []
    payments = daybook[(daybook['VchType'] == 'Payment') & (daybook['Debit'] >= threshold)]
    for _, row in payments.iterrows():
        findings.append({
            'date': str(row['Date'].date()) if pd.notna(row['Date']) else '',
            'party': row['Particulars'],
            'amount': row['Debit'],
            'question': f"Large payment of Rs.{row['Debit']:,.0f} to {row['Particulars']} on {str(row['Date'].date()) if pd.notna(row['Date']) else 'unknown date'}. Please provide supporting bill/invoice/agreement."
        })
    return findings

# ── MODULE 6: INCOME TAX / ITR FLAGS ─────────────────────────────────────────
def audit_itr(ledgers, daybook):
    findings = []
    # Personal expenses in business books
    personal_keywords = ['grocery','personal','family','children','school','shopping','hotel',
                         'food','club','medical','college fees','membership']
    for ledger in ledgers:
        name_lower = ledger['name'].lower()
        if any(k in name_lower for k in personal_keywords) and ledger['debit'] > 0:
            findings.append({
                'ledger': ledger['name'],
                'amount': ledger['debit'],
                'issue': f"'{ledger['name']}' (Rs.{ledger['debit']:,.0f}) may be a personal expense — not deductible as business expense",
                'action': "Verify — if personal, move to Drawings account"
            })
    # Disallowed cash payments from Module 3
    cash_disallowed = sum(
        r['Debit'] for _, r in daybook[
            (daybook['VchType']=='Payment') & (daybook['Debit'] > CASH_EXPENSE_LIMIT)
        ].iterrows()
    )
    if cash_disallowed > 0:
        findings.append({
            'ledger': 'Cash Payments (Sec 40A(3))',
            'amount': cash_disallowed,
            'issue': f"Total cash payments above Rs.10,000 = Rs.{cash_disallowed:,.0f} — will be disallowed under Section 40A(3)",
            'action': f"Estimated additional tax (30% bracket) = Rs.{cash_disallowed*0.30:,.0f}"
        })
    return findings

# ── MAIN AUDIT RUNNER ─────────────────────────────────────────────────────────
def run_full_audit(tb_path, db_path=None):
    print("Parsing files...")
    ledgers = parse_trial_balance(tb_path)
    daybook = parse_daybook(db_path) if db_path else pd.DataFrame(
        columns=['Date','Particulars','VchType','VchNo','Debit','Credit'])
    print(f"  Ledgers: {len(ledgers)} | Daybook entries: {len(daybook)}")

    results = {}

    print("Module 1: Ledger Classification...")
    results['ledger_classification'] = audit_ledger_classification(ledgers)

    print("Module 2: Outstanding Amounts...")
    results['outstanding'] = audit_outstanding(ledgers)

    print("Module 3: Cash Violations...")
    results['cash_violations'] = audit_cash_violations(daybook)

    print("Module 4: Loan Audit...")
    results['loans'] = audit_loans(ledgers, daybook)

    print("Module 5: Large Expenses...")
    results['large_expenses'] = audit_large_expenses(daybook, threshold=100000)

    print("Module 6: ITR / Tax Audit...")
    results['itr'] = audit_itr(ledgers, daybook)

    # Score
    critical = (
        sum(1 for f in results['ledger_classification'] if f['severity']=='Critical') +
        len(results['cash_violations']) +
        sum(1 for f in results['outstanding'] if f['severity']=='Critical')
    )
    warnings = (
        sum(1 for f in results['ledger_classification'] if f['severity']=='Review') +
        sum(1 for f in results['outstanding'] if f['severity']=='Review')
    )
    questions = len(results['loans']) + len(results['large_expenses'])
    score = max(0, 100 - (critical * 8) - (warnings * 3) - (questions * 2))

    results['summary'] = {
        'company': 'AJAY KUMAR LADDHA',
        'period': '1-Apr-25 to 31-Mar-26',
        'total_ledgers': len(ledgers),
        'total_vouchers': len(daybook),
        'critical': critical,
        'warnings': warnings,
        'questions': questions,
        'score': score,
        'generated_at': datetime.now().strftime('%d-%b-%Y %H:%M')
    }

    return results

# ── RUN & PRINT RESULTS ──────────────────────────────────────────────────────
if __name__ == '__main__':
    TB = r'C:\Users\sagar\OneDrive\Desktop\AJKL trialbalance 08-06.xlsx'
    DB = r'C:\Users\sagar\OneDrive\Desktop\AJKL daybook 08-06.xlsx'

    results = run_full_audit(TB, DB)
    s = results['summary']

    print(f"\n{'='*60}")
    print(f"AUDIT COMPLETE — {s['company']}")
    print(f"Period: {s['period']}")
    print(f"Score: {s['score']}/100")
    print(f"Critical: {s['critical']} | Warnings: {s['warnings']} | Questions: {s['questions']}")
    print(f"{'='*60}")

    print(f"\n--- LEDGER CLASSIFICATION ({len(results['ledger_classification'])} issues) ---")
    for f in results['ledger_classification']:
        print(f"  [{f['severity']}] {f['ledger']} — Rs.{f['balance']:,.0f}")
        print(f"    Currently: {f['current_group']} → Should be: {f['correct_group']}")

    print(f"\n--- OUTSTANDING AMOUNTS ({len(results['outstanding'])} issues) ---")
    for f in results['outstanding']:
        print(f"  [{f['severity']}] {f['ledger']} — Rs.{f['amount']:,.0f}")
        print(f"    Q: {f['question'][:100]}...")

    print(f"\n--- CASH VIOLATIONS ({len(results['cash_violations'])} issues) ---")
    for f in results['cash_violations'][:10]:
        print(f"  [{f['section']}] {f['party']} — Rs.{f['amount']:,.0f} on {f['date']}")

    print(f"\n--- LOANS REQUIRING DOCUMENTS ({len(results['loans'])} loans) ---")
    for f in results['loans']:
        print(f"  {f['ledger']} — Rs.{f['balance']:,.0f}")

    print(f"\n--- LARGE EXPENSES > Rs.1L ({len(results['large_expenses'])} entries) ---")
    for f in results['large_expenses']:
        print(f"  {f['date']} | {f['party']} — Rs.{f['amount']:,.0f}")

    print(f"\n--- ITR FLAGS ({len(results['itr'])} issues) ---")
    for f in results['itr']:
        print(f"  {f['ledger']} — Rs.{f['amount']:,.0f}")
        print(f"    {f['issue'][:100]}")

    # Save JSON for frontend
    with open(r'C:\Users\sagar\Downloads\virtualca\data\audit_result.json', 'w') as fp:
        json.dump(results, fp, indent=2, default=str)
    print(f"\nSaved to data/audit_result.json")
