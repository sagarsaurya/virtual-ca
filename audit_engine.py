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
    {"pattern": ["income tax","income-tax","i.tax","advance tax"],
     "correct_group": "Duties & Taxes", "wrong_groups": ["Bank Accounts","Current Assets","Indirect Expenses"], "severity": "Critical",
     "rule": "Income Tax / TDS ledger must be under Duties & Taxes, not Bank Accounts"},
    {"pattern": ["investment redemption","mutual fund redemption","redemption"],
     "correct_group": "Investments", "wrong_groups": ["Bank Accounts","Current Assets"], "severity": "Critical",
     "rule": "Investment Redemption is under Investments group, not Bank Accounts"},
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
        'Cash-in-Hand','Bank Accounts','Bank OD A/c','Direct Incomes','Direct Expenses',
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
    """
    Parses Tally daybook export. Handles two formats:
    - Standard (single row per voucher): only party name visible
    - Detailed / Alt+F5 (multiple rows per voucher): bank/cash account also visible

    Adds '_vid' (voucher id) to every row so continuation rows can be grouped.
    """
    df = pd.read_excel(filepath, header=None)
    df = df[5:].reset_index(drop=True)
    df.columns = ['Date','Particulars','VchType','VchNo','Debit','Credit']
    df['Debit']       = pd.to_numeric(df['Debit'],  errors='coerce').fillna(0)
    df['Credit']      = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    df['Date']        = pd.to_datetime(df['Date'],  errors='coerce')
    df['Particulars'] = df['Particulars'].astype(str).str.strip()
    df['VchType']     = df['VchType'].astype(str).str.strip()

    # Assign voucher_id to all rows (continuation rows inherit from header row)
    VOUCHER_TYPES = {'Payment','Receipt','Journal','Contra','Sales','Purchase',
                     'Credit Note','Debit Note','Memo'}
    vid = 0
    vids = []
    for _, row in df.iterrows():
        vt = row['VchType']
        if vt in VOUCHER_TYPES:
            vid += 1
        vids.append(vid)
    df['_vid'] = vids

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
    """
    Correctly identifies CASH payments/receipts by checking the actual
    account used in each voucher — not just the party name.

    Logic:
    1. Assign a voucher_id to every row (continuation rows inherit from header row)
    2. For each Payment/Receipt voucher, collect ALL account names across its rows
    3. If ANY account is a bank/digital account → it's a bank transaction → SKIP
    4. Only flag vouchers where all accounts are cash/unknown → true cash transaction
    """
    if daybook.empty:
        return []

    BANK_ACCOUNT_KEYWORDS = [
        'hdfc', 'icici', 'sbi', 'axis', 'kotak', 'yes bank', 'rbl', 'indusind',
        'federal bank', 'bank of baroda', 'bank of india', 'union bank', 'canara',
        'pnb', 'punjab national', 'current a/c', 'savings a/c', 'bank account',
        'zerodha', 'anand rathi', 'tapinvest', 'icici prudential', 'mutual fund',
        'nps', 'ppf', 'epf', 'neft', 'rtgs', 'upi', 'imps', 'online transfer',
    ]

    # ── Step 1: assign voucher_id to every row (continuation rows get same id) ──
    db = daybook.copy().reset_index(drop=True)
    db['_vid']   = None   # voucher id (running counter)
    db['_vtype'] = None   # voucher type for this group

    vid = 0
    current_type = None
    for idx, row in db.iterrows():
        vtype = str(row['VchType']).strip() if pd.notna(row['VchType']) else ''
        vno   = str(row['VchNo']).strip()   if pd.notna(row['VchNo'])   else ''

        is_header = vtype in ['Payment', 'Receipt', 'Journal', 'Contra', 'Sales', 'Purchase']
        if is_header:
            vid += 1
            current_type = vtype

        db.at[idx, '_vid']   = vid
        db.at[idx, '_vtype'] = current_type

    # ── Step 2: for each Payment/Receipt voucher, collect all account names ──
    pay_rcpt = db[db['_vtype'].isin(['Payment', 'Receipt'])]

    # Map vid → set of lowercase account names in that voucher
    vch_accounts = {}
    for _, row in db[db['_vid'].isin(pay_rcpt['_vid'].unique())].iterrows():
        v = row['_vid']
        name = str(row['Particulars']).strip().lower()
        if v not in vch_accounts:
            vch_accounts[v] = {'type': row['_vtype'], 'accounts': set()}
        if name and name != 'nan':
            vch_accounts[v]['accounts'].add(name)

    # ── Step 3: identify vouchers that use a bank account ──
    bank_vids = set()
    for v, info in vch_accounts.items():
        for acc in info['accounts']:
            if any(kw in acc for kw in BANK_ACCOUNT_KEYWORDS):
                bank_vids.add(v)
                break

    # ── Step 4: flag only true cash vouchers ──
    findings = []
    seen = set()  # avoid duplicate flags for same voucher

    for _, row in pay_rcpt.iterrows():
        v = row['_vid']
        if v in bank_vids:
            continue          # bank payment — not a cash violation
        if v in seen:
            continue          # already flagged this voucher
        seen.add(v)

        party  = str(row['Particulars']).strip()
        date   = str(row['Date'].date()) if pd.notna(row['Date']) else ''

        # Sec 40A(3) — payment > ₹10,000 (verify if cash or bank)
        if row['Debit'] > CASH_EXPENSE_LIMIT:
            findings.append({
                'severity': 'Critical',
                'date': date,
                'party': party,
                'amount': row['Debit'],
                'type': 'cash_expense',
                'section': '40A(3)',
                'issue': f"Payment of Rs.{row['Debit']:,.0f} to {party} — verify payment mode (cash or bank)",
                'impact': f"If paid in CASH: Rs.{row['Debit']:,.0f} will be disallowed. If paid via Bank/IMPS/NEFT: no violation — reply to dismiss."
            })

        # Sec 269ST — receipt > ₹2,00,000 (verify if cash)
        if row['Credit'] > CASH_RECEIPT_LIMIT:
            findings.append({
                'severity': 'Critical',
                'date': date,
                'party': party,
                'amount': row['Credit'],
                'type': 'cash_receipt',
                'section': '269ST',
                'issue': f"Receipt of Rs.{row['Credit']:,.0f} from {party} — verify if received in cash",
                'impact': f"If received in CASH: penalty = 100% of amount = Rs.{row['Credit']:,.0f}. If via bank: no violation — reply to dismiss."
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
    # Disallowed cash payments — reuse cash_violations to get accurate list
    cash_violations = audit_cash_violations(daybook)
    cash_disallowed = sum(v['amount'] for v in cash_violations if v['type'] == 'cash_expense')
    if cash_disallowed > 0:
        findings.append({
            'ledger': 'Cash Payments (Sec 40A(3))',
            'amount': cash_disallowed,
            'issue': f"Total cash payments above Rs.10,000 = Rs.{cash_disallowed:,.0f} — will be disallowed under Section 40A(3)",
            'action': f"Estimated additional tax (30% bracket) = Rs.{cash_disallowed*0.30:,.0f}"
        })
    return findings

# ── MODULE 7: BANK ACCOUNT DETECTION ─────────────────────────────────────────
BANK_GROUPS = ('Bank Accounts', 'Bank OD A/c')

# Words that disqualify a ledger from being a bank account
NOT_A_BANK = [
    'loan', 'advance', 'tax', 'tds', 'gst', 'income tax', 'investment',
    'redemption', 'deposit', 'fd', 'fixed deposit', 'mutual fund', 'shares',
    'capital', 'salary', 'payable', 'receivable', 'creditor', 'debtor',
    'expense', 'income', 'profit', 'loss', 'reserve', 'drawings',
    'insurance', 'rent', 'interest payable',
    # Bank-related expenses — NOT actual bank accounts
    'bank interest', 'bank charges', 'bank od interest', 'bank commission',
    'bank fee', 'bank penalty', 'bank processing', 'interest received',
    'interest paid', 'charges', 'processing fee',
    # Credit/debit cards and investment/insurance products — NOT bank accounts
    'credit card', 'debit card',
    'fund', 'prudential', 'bluechip', 'flexi', 'liquid', 'growth', 'dividend',
    'insurance', 'policy', 'lic',
]

BANK_NAME_PATTERNS = [
    'hdfc', 'icici', 'sbi', 'axis bank', 'kotak', 'pnb', 'canara', 'bob',
    'union bank', 'idbi', 'yes bank', 'indusind', 'rbl', 'federal bank',
    'current a/c', 'savings a/c', 'current account', 'savings account',
    'cash credit', 'cc a/c', 'od account', 'overdraft a/c',
]

def _is_real_bank(name_lower):
    """Returns True if name looks like an actual bank account."""
    if any(bad in name_lower for bad in NOT_A_BANK):
        return False
    # Must contain 'bank' OR a known bank name pattern
    return 'bank' in name_lower or any(p in name_lower for p in BANK_NAME_PATTERNS)

def audit_bank_accounts(ledgers, transactions=None):
    """
    Detects bank accounts from THREE sources:
    1. TB ledgers in 'Bank Accounts' or 'Bank OD A/c' group
    2. TB ledgers in any group whose name matches bank patterns
    3. Daybook transactions — unique party/ledger names that look like bank accounts
       (Payment/Receipt vouchers credit/debit the bank account)
    """
    seen     = set()
    findings = []

    # Build a case-insensitive balance lookup from TB for daybook-discovered banks
    tb_balance = {l['name']: l for l in ledgers}
    tb_balance_ci = {l['name'].lower(): l for l in ledgers}  # case-insensitive fallback

    def _add(name, balance=0, dr_cr='Dr', group='', note=''):
        if name in seen:
            return
        seen.add(name)
        bal_abs = abs(balance)
        findings.append({
            'ledger':   name,
            'balance':  bal_abs,
            'dr_cr':    dr_cr,
            'debit':    0,
            'credit':   0,
            'group':    group,
            'question': (
                f"Bank account '{name}'{note} — balance ₹{bal_abs:,.0f} ({dr_cr}). "
                f"Please reconcile with the bank statement."
            ),
        })

    # Pass 1 — TB group-based
    for ledger in ledgers:
        n   = ledger['name'].lower()
        grp = ledger['group']
        if grp in BANK_GROUPS:
            if not any(bad in n for bad in NOT_A_BANK):
                od = ' (OD Account)' if grp == 'Bank OD A/c' else ''
                bal = ledger['balance']
                _add(ledger['name'], bal, 'Dr' if bal >= 0 else 'Cr', grp, od)

    # Pass 2 — TB name-based (any group)
    for ledger in ledgers:
        n = ledger['name'].lower()
        if ledger['group'] not in BANK_GROUPS and _is_real_bank(n):
            bal = ledger['balance']
            _add(ledger['name'], bal, 'Dr' if bal >= 0 else 'Cr',
                 ledger['group'], f' [under: {ledger["group"]}]')

    # Pass 3 — Daybook scan: collect unique ledger names from Payment/Receipt/Contra vouchers
    if transactions:
        for txn in transactions:
            vtype = str(txn.get('VchType', '')).strip().lower()
            if vtype not in ('payment', 'receipt', 'contra'):
                continue
            party = str(txn.get('Particulars', '') or '').strip()
            if not party or party in seen or party.lower() in ('nan', ''):
                continue
            n = party.lower()
            if _is_real_bank(n):
                # Try to get balance from TB — exact match first, then case-insensitive
                tb = tb_balance.get(party) or tb_balance_ci.get(party.lower())
                if tb:
                    bal = tb['balance']
                    _add(tb['name'], bal, 'Dr' if bal >= 0 else 'Cr',
                         tb.get('group', ''), '')
                else:
                    _add(party, 0, 'Dr', '', ' (found in daybook — verify balance)')

    return findings


# ── MODULE 8: TDS COMPLIANCE CHECK ───────────────────────────────────────────
TDS_RULES_CONFIG = [
    {
        'section': '194C',
        'description': 'Contractor / Manpower / Freight',
        'keywords': [
            'contractor', 'construction', 'repair', 'maintenance', 'labour',
            'labor', 'manpower', 'transport', 'freight', 'cargo', 'logistics',
            'fabricat', 'housekeeping', 'security guard', 'catering', 'printing',
            'packing', 'loading', 'unloading', 'courier',
        ],
        'rate': 1.0,          # 1% for individual/HUF, 2% for company
        'single_limit': 30000,
        'annual_limit': 75000,
    },
    {
        'section': '194J',
        'description': 'Professional / Technical Fees',
        'keywords': [
            'professional fee', 'consultant', 'consulting', 'legal', 'advocate',
            'lawyer', 'doctor fee', 'technical fee', 'technical service',
            'architect', 'engineer fee', 'ca fee', 'cs fee', 'audit fee',
            'accountant fee', 'royalty', 'software service', 'it service',
            'design fee', 'professional charges', 'technical charges',
        ],
        'rate': 10.0,
        'single_limit': 50000,
        'annual_limit': 50000,
    },
    {
        'section': '194I',
        'description': 'Rent',
        'keywords': [
            'rent', 'office rent', 'shop rent', 'warehouse rent', 'godown rent',
            'factory rent', 'lease rent', 'hire charge', 'vehicle hire',
            'machinery hire', 'equipment hire',
        ],
        'rate': 10.0,
        'single_limit': 20000,   # per month trigger; annual = 240,000
        'annual_limit': 240000,
    },
    {
        'section': '194H',
        'description': 'Commission / Brokerage',
        'keywords': [
            'commission', 'brokerage', 'agency fee', 'referral fee',
            'marketing commission', 'dealer commission', 'distributor commission',
        ],
        'rate': 5.0,
        'single_limit': 15000,
        'annual_limit': 15000,
    },
]

def audit_tds_compliance(ledgers, daybook):
    """
    Checks TDS compliance for payments made during the year.

    Two checks:
    A. Payment-based check: aggregate daybook payments by party name;
       if party name keywords suggest TDS section AND total > annual limit → flag.
    B. TDS ledger check: look for TDS Payable ledgers in trial balance;
       if payable balance = 0 but large professional/contractor payments exist → flag.
    """
    findings = []

    # ── A. Aggregate payments by party ──────────────────────────────────────
    if not daybook.empty:
        payments = daybook[
            (daybook['VchType'].isin(['Payment','Journal'])) &
            (daybook['Debit'] > 0)
        ].copy()

        party_totals = (
            payments.groupby('Particulars')['Debit']
            .sum()
            .reset_index()
        )

        for _, pr in party_totals.iterrows():
            party = str(pr['Particulars']).strip()
            total = float(pr['Debit'])
            party_lower = party.lower()

            for rule in TDS_RULES_CONFIG:
                if any(kw in party_lower for kw in rule['keywords']):
                    if total > rule['annual_limit']:
                        tds_expected = round(total * rule['rate'] / 100, 0)
                        interest     = round(tds_expected * 0.015 * 12, 0)  # 1.5%/month × 12
                        findings.append({
                            'party':        party,
                            'section':      rule['section'],
                            'description':  rule['description'],
                            'total_paid':   total,
                            'rate':         rule['rate'],
                            'tds_expected': tds_expected,
                            'interest_est': interest,
                            'type':         'payment_check',
                            'severity':     'Critical',
                            'issue': (
                                f"Total payments to '{party}' = Rs.{total:,.0f}. "
                                f"TDS under Sec {rule['section']} ({rule['description']}) @ "
                                f"{rule['rate']}% applies — TDS should have been Rs.{tds_expected:,.0f}."
                            ),
                            'impact': (
                                f"If TDS not deducted: interest @ 1%/month until deduction "
                                f"+ 1.5%/month until deposit. Estimated exposure = Rs.{interest:,.0f}. "
                                f"File 26Q/27Q return and pay TDS now to stop further interest."
                            ),
                        })
                    break   # matched one rule — don't double-flag

    # ── A2. Trial Balance expense ledger scan ────────────────────────────────
    # Party-name scan above only catches if party name contains keywords.
    # This scan catches expense ledger names (e.g., "Office Rent Paid", "Professional Charges")
    already_flagged = set(f['party'] for f in findings)
    for ledger in ledgers:
        n    = ledger['name'].lower()
        bal  = abs(ledger.get('debit', 0) or ledger.get('balance', 0))
        name = ledger['name']
        if name in already_flagged:
            continue
        for rule in TDS_RULES_CONFIG:
            if any(kw in n for kw in rule['keywords']):
                if bal > rule['annual_limit']:
                    tds_expected = round(bal * rule['rate'] / 100, 0)
                    interest     = round(tds_expected * 0.015 * 12, 0)
                    findings.append({
                        'party':        name,
                        'section':      rule['section'],
                        'description':  rule['description'],
                        'total_paid':   bal,
                        'rate':         rule['rate'],
                        'tds_expected': tds_expected,
                        'interest_est': interest,
                        'type':         'payment_check',
                        'severity':     'Critical',
                        'issue': (
                            f"Expense ledger '{name}' = Rs.{bal:,.0f}. "
                            f"TDS under Sec {rule['section']} ({rule['description']}) @ "
                            f"{rule['rate']}% — TDS should be Rs.{tds_expected:,.0f}."
                        ),
                        'impact': (
                            f"Verify TDS was deducted at source. If not: interest @ 1.5%/month. "
                            f"Estimated exposure = Rs.{interest:,.0f}."
                        ),
                    })
                    break

    # ── B. TDS ledger balance check ──────────────────────────────────────────
    # Find total professional + contractor payments
    tds_bal = 0
    for ledger in ledgers:
        n = ledger['name'].lower()
        if ('tds payable' in n or 'tds on' in n) and ledger['group'] == 'Duties & Taxes':
            tds_bal += abs(ledger['balance'])

    # Heuristic: if tds_bal = 0 but there are findings above → add a general deposit warning
    if tds_bal == 0 and findings:
        findings.append({
            'party':        'TDS Payable Ledger',
            'section':      'General',
            'description':  'TDS deposit check',
            'total_paid':   0,
            'rate':         0,
            'tds_expected': 0,
            'interest_est': 0,
            'type':         'deposit_check',
            'severity':     'Critical',
            'issue': (
                "No 'TDS Payable' ledger found in Duties & Taxes. "
                "Either TDS was not deducted, or it is recorded in wrong ledger."
            ),
            'impact': (
                "TDS must be deposited by 7th of the following month (March: by 30 April). "
                "Late deposit attracts interest @ 1.5%/month. "
                "Also verify: is there a TDS Payable ledger under Current Liabilities instead of Duties & Taxes?"
            ),
        })

    return findings


# ── MODULE 9: SALARY / PF / PT COMPLIANCE ────────────────────────────────────
def audit_salary_compliance(ledgers):
    """
    Checks salary payments, PF deduction, and Professional Tax from the trial balance.
    Works entirely from ledger balances — no daybook needed.
    """
    findings = []

    salary_ledgers = [l for l in ledgers
                      if any(k in l['name'].lower()
                             for k in ['salary','wages','remuneration','staff cost'])]
    pf_ledgers     = [l for l in ledgers
                      if any(k in l['name'].lower()
                             for k in ['provident fund','pf payable','epf','pf contribution'])]
    esi_ledgers    = [l for l in ledgers
                      if any(k in l['name'].lower()
                             for k in ['esi','esic','employee state insurance'])]
    pt_ledgers     = [l for l in ledgers
                      if any(k in l['name'].lower()
                             for k in ['professional tax','pt payable','p.tax'])]

    total_salary = sum(l['debit'] for l in salary_ledgers if l['debit'] > 0)

    if total_salary == 0:
        return []  # No salary entries — skip

    findings.append({
        'type':    'salary_summary',
        'ledgers': [l['name'] for l in salary_ledgers],
        'total':   total_salary,
        'issue':   f"Total salary/wages in books = Rs.{total_salary:,.0f}",
        'question': (
            f"Total salary expense = Rs.{total_salary:,.0f}. "
            f"Please confirm: How many employees? Monthly salary per employee? "
            f"Monthly salary register maintained? Form 16 issued to employees?"
        ),
        'severity': 'Info',
    })

    # PF check
    if not pf_ledgers:
        expected_pf = round(total_salary * 0.12, 0)
        findings.append({
            'type':         'pf_missing',
            'total_salary': total_salary,
            'expected_pf':  expected_pf,
            'issue': (
                f"Salary in books = Rs.{total_salary:,.0f} but NO PF/EPF ledger found. "
                f"If any employee earns ≤ Rs.15,000/month, PF @ 12% of basic is mandatory."
            ),
            'impact': (
                f"Estimated employer PF contribution (12%) = Rs.{expected_pf:,.0f}. "
                f"Non-deduction of PF attracts penalty u/s 14B of EPF Act: up to 25% of dues."
            ),
            'severity': 'Important',
        })
    else:
        total_pf = sum(abs(l['balance']) for l in pf_ledgers)
        findings.append({
            'type':      'pf_found',
            'total_pf':  total_pf,
            'pf_ledgers': [l['name'] for l in pf_ledgers],
            'issue':     f"PF ledger found. Total PF amount = Rs.{total_pf:,.0f}.",
            'question':  (
                f"PF ledger shows Rs.{total_pf:,.0f}. "
                f"Please confirm: Is PF being deposited by 15th of every month? "
                f"ECR filed monthly on EPFO portal? Any arrears outstanding?"
            ),
            'severity': 'Info',
        })

    # ESI check
    if not esi_ledgers and total_salary > 0:
        findings.append({
            'type':    'esi_missing',
            'issue':   "No ESI ledger found. If any employee earns ≤ Rs.21,000/month, ESI registration and contribution is mandatory.",
            'impact':  "Employee contribution = 0.75% of gross salary. Employer contribution = 3.25% of gross salary. Monthly deposit by 15th.",
            'severity': 'Important',
        })

    # PT check
    if not pt_ledgers and total_salary > 0:
        findings.append({
            'type':    'pt_missing',
            'issue':   "No Professional Tax (PT) ledger found. PT is mandatory for all employees in West Bengal (and most states).",
            'impact':  "WB PT slabs: ₹0 (≤10K), ₹110 (≤15K), ₹130 (≤25K), ₹150 (≤40K), ₹200 (>40K). Annual employer PT registration also required.",
            'severity': 'Important',
        })
    elif pt_ledgers:
        total_pt = sum(abs(l['balance']) for l in pt_ledgers)
        if total_pt == 0:
            findings.append({
                'type':    'pt_zero_balance',
                'issue':   f"PT ledger found ({pt_ledgers[0]['name']}) but balance is ₹0. Was PT collected from employees?",
                'impact':  "PT should be deducted monthly and deposited to state govt. Nil balance may mean PT was not deducted or was already deposited (verify deposit challan).",
                'severity': 'Important',
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

    print("Module 7: Bank Account Detection...")
    # Convert daybook DataFrame to list of dicts for bank scanning
    txn_list = daybook.to_dict('records') if not daybook.empty else []
    results['bank_accounts'] = audit_bank_accounts(ledgers, txn_list)

    print("Module 8: TDS Compliance...")
    results['tds_compliance'] = audit_tds_compliance(ledgers, daybook)

    print("Module 9: Salary / PF / PT Compliance...")
    results['salary_compliance'] = audit_salary_compliance(ledgers)

    # Score
    critical = (
        sum(1 for f in results['ledger_classification'] if f['severity']=='Critical') +
        sum(1 for f in results['outstanding'] if f['severity']=='Critical')
    )
    # Cash violations are UNVERIFIED — count as warnings, not critical
    cash_violations_count = len(results['cash_violations'])
    warnings = (
        sum(1 for f in results['ledger_classification'] if f['severity']=='Review') +
        sum(1 for f in results['outstanding'] if f['severity']=='Review') +
        cash_violations_count
    )
    tds_critical  = sum(1 for t in results['tds_compliance'] if t.get('severity') == 'Critical')
    salary_issues = sum(1 for s in results['salary_compliance'] if s.get('severity') in ('Critical','Important'))
    questions = len(results['loans']) + len(results['large_expenses']) + len(results['bank_accounts'])
    # Cash violations: cap penalty at 20 pts (unverified — could be bank payments)
    cash_penalty = min(20, cash_violations_count)
    score = max(0, 100 - (critical * 8) - (warnings * 1) - (questions * 2)
                      - (tds_critical * 6) - (salary_issues * 3) - cash_penalty)

    results['summary'] = {
        'company': 'AJAY KUMAR LADDHA',
        'period': '1-Apr-25 to 31-Mar-26',
        'total_ledgers': len(ledgers),
        'total_vouchers': len(daybook),
        'critical': critical,
        'warnings': warnings,
        'questions': questions,
        'cash_violations_count': cash_violations_count,
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
