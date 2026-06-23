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
    # Read raw (no header) — preserve original cell text including leading spaces
    df = pd.read_excel(filepath, header=None)
    ledgers = []
    current_group  = None
    current_level1 = None
    company_name = ''
    period_str   = ''

    SKIP_NAMES = {'nan','particulars','grand total','debit','credit',
                  'closing balance','trial balance','opening balance',''}

    # ── FIND DATA START ROW ───────────────────────────────────────────────────
    # Tally TB Excel has several header rows: company name, address, period, column headers.
    # Data starts AFTER the row containing "Debit" / "Credit" column labels.
    # We scan up to row 20 to find this boundary.
    data_start = 0
    for i, row in df.head(20).iterrows():
        vals = [str(v).strip().lower() for v in row if pd.notna(v) and str(v).strip()]
        # Row that says "Debit" or "Credit" = column header row → data starts next row
        if 'debit' in vals or 'credit' in vals:
            data_start = i + 1

    # Scan header rows for company name and period (before data starts)
    for i, row in df.iloc[:data_start].iterrows():
        raw = str(row[0]) if pd.notna(row[0]) else ''
        val = raw.strip()
        if not val or val.lower() in SKIP_NAMES:
            continue
        if ' to ' in val and any(c.isdigit() for c in val):
            period_str = val
        elif not company_name and len(val) > 3 and val.lower() not in SKIP_NAMES:
            # First meaningful non-skip row = company name
            # Skip address-like rows (numbers, floor, unit, road, pincode)
            looks_like_address = any(word in val.lower() for word in
                ['road', 'floor', 'unit', 'street', 'nagar', 'colony', 'tower',
                 'building', 'plot', 'sector', 'phase', 'near', 'opp'])
            looks_like_pincode = val.replace(' ','').isdigit() or (
                len(val.split()) <= 2 and any(p.isdigit() for p in val.split()))
            if not looks_like_address and not looks_like_pincode:
                company_name = val

    # Parse only data rows (skip all header rows)
    for _, row in df.iloc[data_start:].iterrows():
        raw  = str(row[0]) if pd.notna(row[0]) else ''
        name = raw.strip()
        try:
            debit  = float(row[1]) if pd.notna(row[1]) else 0.0
        except: debit = 0.0
        try:
            credit = float(row[2]) if pd.notna(row[2]) else 0.0
        except: credit = 0.0

        if not name or name.lower() in SKIP_NAMES:
            continue
        if name == period_str or name == company_name:
            continue
        # Skip header rows (col1 is non-numeric text like "Debit")
        try:
            if pd.notna(row[1]) and not str(row[1]).replace('.','').replace('-','').isnumeric():
                continue
        except: pass

        is_indented = raw != name  # leading whitespace = indented

        # Tally group hierarchy — two levels
        # Level 1: top-level Balance Sheet / P&L groups
        # Level 2: sub-groups (sit under a Level 1 group)
        # Anything else = ledger (individual account)
        LEVEL1 = {
            'capital account','loans (liability)','fixed assets','investments',
            'current assets','current liabilities',
            'direct incomes','indirect incomes','sales accounts',
            'direct expenses','indirect expenses','purchase accounts',
            'stock-in-hand','branch / divisions','reserves & surplus',
            'profit & loss a/c','misc. expenses (asset)',
        }
        LEVEL2 = {
            'duties & taxes','sundry creditors','sundry debtors',
            'cash-in-hand','bank accounts','bank od a/c',
            'loans & advances (asset)','deposits (asset)',
            'suspense a/c','suspense',
        }

        nl = name.lower()

        if nl in LEVEL1:
            # Top-level group — reset both levels, never add as ledger
            current_group  = name
            current_level1 = name

        elif nl in LEVEL2:
            # Sub-group — add as ledger under Level 1 (if it has a balance = condensed export)
            # Then reset current_group back to Level 1 so subsequent items don't fall under
            # this sub-group incorrectly (e.g. Advance to Staff after Bank Accounts)
            if (debit != 0 or credit != 0) and current_level1:
                ledgers.append({
                    'name': name, 'group': current_level1,
                    'debit': debit, 'credit': credit, 'balance': debit - credit
                })
            # Keep current_group as this sub-group name so Pass 1 bank detection still works
            # (items appearing INSIDE this group in a detailed TB will get sub-group name)
            # But for condensed TBs with no sub-items, this is overridden by Level 1 fallback
            current_group = current_level1  # reset → subsequent items go under Level 1

        else:
            # Ledger — add under current_group (or current_level1 as fallback)
            grp = current_group or current_level1
            if grp:
                ledgers.append({
                    'name': name, 'group': grp,
                    'debit': debit, 'credit': credit, 'balance': debit - credit
                })

    return ledgers, company_name, period_str

# ── PARSE DAYBOOK ─────────────────────────────────────────────────────────────
def parse_daybook(filepath):
    """
    Parses Tally daybook export. Auto-detects header row and column layout.
    Handles both 6-column and 8-column Tally exports.

    6-col format: Date | Particulars | VchType | VchNo | Debit | Credit
    8-col format: Date | Particulars | (blank) | (blank) | VchType | VchNo | Debit | Credit

    Adds '_vid' (voucher id) to every row so continuation rows can be grouped.
    """
    df = pd.read_excel(filepath, header=None)

    # Auto-detect header row — find the row where col0='Date' or col1='Particulars'
    header_row = None
    for i, row in df.head(12).iterrows():
        vals = [str(v).strip().lower() for v in row if pd.notna(v)]
        if 'date' in vals and 'particulars' in vals:
            header_row = i
            break

    if header_row is None:
        header_row = 5  # fallback: skip first 5 rows (AJKL format)

    df = df[header_row + 1:].reset_index(drop=True)

    # Map columns by position based on total count
    ncols = len(df.columns)
    if ncols >= 8:
        # 8-col: Date(0) Particulars(1) ?(2) ?(3) VchType(4) VchNo(5) Debit(6) Credit(7)
        df = df.iloc[:, [0, 1, 4, 5, 6, 7]]
    elif ncols == 7:
        # 7-col: Date(0) Particulars(1) ?(2) VchType(3) VchNo(4) Debit(5) Credit(6)
        df = df.iloc[:, [0, 1, 3, 4, 5, 6]]
    # else 6-col: keep as is

    df.columns = ['Date','Particulars','VchType','VchNo','Debit','Credit']
    df['Debit']       = pd.to_numeric(df['Debit'],  errors='coerce').fillna(0)
    df['Credit']      = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    df['Date']        = pd.to_datetime(df['Date'],  errors='coerce')
    df['Particulars'] = df['Particulars'].astype(str).str.strip()
    df['VchType']     = df['VchType'].astype(str).str.strip()

    # Assign voucher_id AND propagate VchType to all continuation rows
    # so every row in a voucher knows what type it belongs to.
    VOUCHER_TYPES = {'Payment','Receipt','Journal','Contra','Sales','Purchase',
                     'Credit Note','Debit Note','Memo'}
    vid          = 0
    vids         = []
    vtypes_prop  = []   # propagated VchType for every row
    current_vtype = ''
    for _, row in df.iterrows():
        vt = str(row['VchType']).strip() if pd.notna(row['VchType']) else ''
        if vt in VOUCHER_TYPES:
            vid += 1
            current_vtype = vt
        vids.append(vid)
        vtypes_prop.append(current_vtype)   # continuation rows get parent's type

    df['_vid']   = vids
    df['VchType'] = vtypes_prop   # overwrite — now every row has its voucher type

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
    """
    Checks:
    - Suspense A/c non-zero (Critical)
    - Sundry Debtors: credit balance, large outstanding, >3yr bad debt (Sec 36(1)(vii))
    - Sundry Creditors: debit balance, >3yr cessation of liability (Sec 41(1) IT Act),
                        MSME 45-day rule flag (Sec 43B(h))
    - Cash-in-Hand: negative balance (impossible = books error), very high balance (>₹2L)
    - Loans & Advances: unadjusted advances
    - Opening balance difference
    """
    findings = []
    for ledger in ledgers:
        name  = ledger['name']
        group = ledger['group']
        nl    = name.lower()
        bal   = ledger['balance']   # debit - credit (positive = Dr balance)

        # ── Suspense non-zero ────────────────────────────────────────────────
        if 'suspense' in nl and (ledger['debit'] > 0 or ledger['credit'] > 0):
            amt = abs(ledger['credit'] or ledger['debit'])
            findings.append({
                'type': 'suspense', 'ledger': name, 'amount': amt,
                'question': (f'Suspense account has Rs.{amt:,.0f} balance. '
                             'Identify the nature and move to correct ledger before finalising books. '
                             'Suspense balance in final accounts is not acceptable per ICAI standards.'),
                'severity': 'Critical',
                'law': 'ICAI Guidance Note on Accounts — suspense must be nil at year-end'
            })

        # ── Sundry Debtors ───────────────────────────────────────────────────
        if group == 'Sundry Debtors':
            # Credit balance debtor = advance received? Should be Current Liability
            if ledger['credit'] > ledger['debit'] and ledger['credit'] > 0:
                findings.append({
                    'type': 'debtor_credit_balance', 'ledger': name,
                    'amount': ledger['credit'] - ledger['debit'],
                    'question': (f'{name} is under Sundry Debtors but has a CREDIT balance '
                                 f'of Rs.{(ledger["credit"]-ledger["debit"]):,.0f}. '
                                 'Is this an advance received from the customer? '
                                 'If yes, move to Current Liabilities → Advance from Customers.'),
                    'severity': 'Review',
                    'law': 'AS 9 Revenue Recognition — advance received is a liability, not a debtor'
                })
            # Large outstanding debtor
            if ledger['debit'] > 50000:
                findings.append({
                    'type': 'outstanding_debtor', 'ledger': name,
                    'amount': ledger['debit'],
                    'question': (f'Rs.{ledger["debit"]:,.0f} outstanding from {name}. '
                                 'When was this invoiced? Has any payment been received? '
                                 'If outstanding >6 months: consider provision for bad debt. '
                                 'If outstanding >3 years and irrecoverable: write off as bad debt '
                                 'and claim deduction under Sec 36(1)(vii) IT Act.'),
                    'severity': 'Review',
                    'law': 'Sec 36(1)(vii) IT Act — bad debt deduction allowed on write-off in books'
                })

        # ── Sundry Creditors ─────────────────────────────────────────────────
        if group == 'Sundry Creditors':
            # Debit balance creditor = advance paid = should be asset
            if ledger['debit'] > ledger['credit'] and ledger['debit'] > 0:
                findings.append({
                    'type': 'creditor_debit_balance', 'ledger': name,
                    'amount': ledger['debit'] - ledger['credit'],
                    'question': (f'{name} is under Sundry Creditors but has a DEBIT balance '
                                 f'of Rs.{(ledger["debit"]-ledger["credit"]):,.0f}. '
                                 'Is this an advance paid to a supplier? '
                                 'If yes, move to Loans & Advances (Asset).'),
                    'severity': 'Review',
                    'law': 'AS 2 / Balance Sheet presentation — advance paid is an asset'
                })
            # Large creditor outstanding — Sec 41(1) + MSME 43B(h) flag
            if ledger['credit'] > 50000:
                findings.append({
                    'type': 'large_creditor_outstanding', 'ledger': name,
                    'amount': ledger['credit'],
                    'question': (f'Rs.{ledger["credit"]:,.0f} payable to {name}. '
                                 '(1) Is this creditor an MSME? If yes and payment is >45 days, '
                                 'expense will be DISALLOWED under Sec 43B(h) — re-allowed only in year of payment. '
                                 '(2) If this liability is >3 years old and not likely to be paid, '
                                 'it becomes taxable income under Sec 41(1) IT Act (cessation of liability). '),
                    'severity': 'Review',
                    'law': 'Sec 43B(h) IT Act (MSME 45-day rule) | Sec 41(1) IT Act (cessation of liability >3yr)'
                })

        # ── Cash-in-Hand ─────────────────────────────────────────────────────
        if group == 'Cash-in-Hand':
            # Negative cash = impossible = books error
            if bal < 0:
                findings.append({
                    'type': 'negative_cash', 'ledger': name,
                    'amount': abs(bal),
                    'question': (f'Cash-in-Hand "{name}" shows a NEGATIVE balance of '
                                 f'Rs.{abs(bal):,.0f}. This is impossible — cash cannot be negative. '
                                 'A payment entry must be missing or wrongly entered. '
                                 'Check the cash ledger and correct the entry.'),
                    'severity': 'Critical',
                    'law': 'Basic accounting principle — cash balance cannot be negative'
                })
            # Very high cash balance
            elif bal > 200000:
                findings.append({
                    'type': 'high_cash_balance', 'ledger': name,
                    'amount': bal,
                    'question': (f'Cash-in-Hand balance is very high at Rs.{bal:,.0f}. '
                                 'Is this correct? High cash balance invites scrutiny. '
                                 'Verify with physical cash count. Any cash above ₹2L received '
                                 'in a single transaction is prohibited under Sec 269ST.'),
                    'severity': 'Review',
                    'law': 'Sec 269ST IT Act — cash receipt >₹2L prohibited; penalty = 100% of amount'
                })

        # ── Loans & Advances (Asset) — old unadjusted advances ───────────────
        if group == 'Loans & Advances (Asset)' and 'advance' in nl and bal > 50000:
            findings.append({
                'type': 'old_advance', 'ledger': name,
                'amount': bal,
                'question': (f'Advance of Rs.{bal:,.0f} in "{name}" is outstanding. '
                             'Has the advance been adjusted against bills/services received? '
                             'Old unadjusted advances should be recovered or written off.'),
                'severity': 'Review',
                'law': 'AS 4 / Prudence principle — unadjusted advances should be reviewed annually'
            })

        # ── Opening balance difference ────────────────────────────────────────
        if 'difference in opening' in nl and (ledger['debit'] > 0 or ledger['credit'] > 0):
            amt = ledger['debit'] or ledger['credit']
            findings.append({
                'type': 'opening_balance_diff', 'ledger': name,
                'amount': abs(amt),
                'question': (f'Difference in Opening Balances = Rs.{abs(amt):,.0f}. '
                             'This means last year closing balance does not match this year opening balance. '
                             'Likely cause: ledger added mid-year without opening balance entry, '
                             'or prior year balance was edited. Must be corrected before audit.'),
                'severity': 'Critical',
                'law': 'AS 1 — opening balance of current year must equal closing balance of prior year'
            })

    return findings

# ── MODULE 3: CASH VIOLATIONS ────────────────────────────────────────────────
def audit_cash_violations(daybook):
    """
    Flags ONLY transactions where the actual payment/receipt account is the
    Cash ledger in Tally (ledger named 'cash' or 'petty cash').

    Law:
    - Sec 40A(3): cash PAYMENT > ₹10,000 → expense disallowed
    - Sec 269ST:  cash RECEIPT  > ₹2,00,000 → penalty = 100% of amount

    Key rule: if payment is via Bank/NEFT/UPI/Cheque → NOT a violation at all.
    Only flag if the voucher explicitly uses a Cash ledger as the payment account.
    """
    if daybook.empty:
        return []

    # Ledger names that mean actual physical cash in Tally
    CASH_LEDGER_NAMES = ['cash', 'petty cash', 'hand cash', 'cash in hand']

    # ── Step 1: assign voucher_id to every row ────────────────────────────────
    db = daybook.copy().reset_index(drop=True)
    db['_vid']   = None
    db['_vtype'] = None

    vid = 0
    current_type = None
    for idx, row in db.iterrows():
        vtype = str(row['VchType']).strip() if pd.notna(row['VchType']) else ''
        is_header = vtype in ['Payment', 'Receipt', 'Journal', 'Contra', 'Sales', 'Purchase']
        if is_header:
            vid += 1
            current_type = vtype
        db.at[idx, '_vid']   = vid
        db.at[idx, '_vtype'] = current_type

    # ── Step 2: find vouchers that explicitly use a Cash ledger ───────────────
    pay_rcpt = db[db['_vtype'].isin(['Payment', 'Receipt'])]

    cash_vids = set()
    for _, row in db[db['_vid'].isin(pay_rcpt['_vid'].unique())].iterrows():
        name = str(row['Particulars']).strip().lower()
        if any(name == c or name.startswith(c) for c in CASH_LEDGER_NAMES):
            cash_vids.add(row['_vid'])

    # ── Step 3: flag only vouchers that used Cash ledger ─────────────────────
    findings = []
    seen = set()

    for _, row in pay_rcpt.iterrows():
        v = row['_vid']
        if v not in cash_vids:
            continue   # not a cash transaction — bank/cheque/UPI → skip
        if v in seen:
            continue
        seen.add(v)

        party = str(row['Particulars']).strip()
        date  = str(row['Date'].date()) if pd.notna(row['Date']) else ''

        # Skip the Cash ledger row itself — we want the party row
        party_lower = party.lower()
        if any(party_lower == c or party_lower.startswith(c) for c in CASH_LEDGER_NAMES):
            continue

        # Sec 40A(3) — cash payment > ₹10,000
        if row['Debit'] > CASH_EXPENSE_LIMIT:
            findings.append({
                'severity':    'Critical',
                'date':        date,
                'party':       party,
                'amount':      row['Debit'],
                'type':        'cash_expense',
                'section':     '40A(3)',
                'voucher_type': str(row['VchType']).strip(),
                'issue':       f"Cash payment of ₹{row['Debit']:,.0f} to {party} exceeds ₹10,000 limit",
                'impact':      f"₹{row['Debit']:,.0f} will be disallowed as business expense u/s 40A(3). Pay via bank to avoid disallowance.",
                'law':         'Section 40A(3) Income Tax Act 1961 — cash payments above ₹10,000 to a single person in a day are disallowed',
            })

        # Sec 269ST — cash receipt > ₹2,00,000
        if row['Credit'] > CASH_RECEIPT_LIMIT:
            findings.append({
                'severity':    'Critical',
                'date':        date,
                'party':       party,
                'amount':      row['Credit'],
                'type':        'cash_receipt',
                'section':     '269ST',
                'voucher_type': str(row['VchType']).strip(),
                'issue':       f"Cash receipt of ₹{row['Credit']:,.0f} from {party} exceeds ₹2,00,000 limit",
                'impact':      f"Penalty = 100% of amount = ₹{row['Credit']:,.0f} u/s 271DA. Receive via account payee cheque or bank transfer only.",
                'law':         'Section 269ST Income Tax Act 1961 — receiving ₹2L or more in cash from one person in a day is prohibited',
            })

    return findings

# ── MODULE 4: LOAN AUDIT ──────────────────────────────────────────────────────
def audit_loans(ledgers, daybook):
    """
    Checks:
    - Any loan/advance account > ₹10,000 → ask for documentation
    - Sec 269SS: loan ACCEPTED in cash > ₹20,000 → penalty = 100% of loan amount (Sec 271D)
    - Sec 269T: loan REPAID in cash > ₹20,000 → penalty = 100% of amount (Sec 271E)
    - Director loans → Companies Act Sec 185 restriction + Sec 269SS compliance
    - Form 3CD Clause 13 reporting requirement for 269SS/269T transactions
    """
    findings = []
    loan_groups = ['Loans (Liability)', 'Loans & Advances (Asset)']

    for ledger in ledgers:
        if ledger['group'] not in loan_groups:
            continue
        bal  = abs(ledger['balance'])
        name = ledger['name']
        nl   = name.lower()
        if bal < 10000:
            continue

        is_director = any(k in nl for k in ['director', 'partner', 'proprietor', 'shareholder', 'promoter'])
        is_liability = ledger['group'] == 'Loans (Liability)'

        docs = [
            f"Bank statement showing loan {'receipt' if is_liability else 'disbursement'} of Rs.{bal:,.0f}",
            "Loan agreement with repayment schedule and interest rate",
        ]
        law_notes = []

        if is_director:
            law_notes.append(
                "Director/Partner loan: must comply with Sec 269SS (acceptance via banking channel only). "
                "For companies: Sec 185 Companies Act restricts loans to directors — requires Board resolution."
            )
            docs.append("Board resolution authorising the loan (mandatory for companies)")
            docs.append("Form DPT-3 filed with ROC (annual return of deposits/loans)")

        law_notes.append(
            f"Sec 269SS: If any amount of Rs.20,000+ was ACCEPTED as loan in cash → "
            f"penalty = 100% of loan amount under Sec 271D. "
            f"Sec 269T: If any repayment of Rs.20,000+ was made in cash → "
            f"penalty = 100% under Sec 271E. Both must be reported in Form 3CD Clause 13."
        )

        findings.append({
            'ledger':   name,
            'group':    ledger['group'],
            'balance':  bal,
            'is_director': is_director,
            'documents_required': docs,
            'law': ' | '.join(law_notes),
            'question': (
                f"{'Director/Partner' if is_director else 'Loan'} account '{name}' has "
                f"balance of Rs.{bal:,.0f}. "
                f"(1) Was this loan received/given via banking channel? "
                f"(2) Any cash acceptance/repayment >₹20,000 = penalty under Sec 269SS/269T. "
                f"Please provide bank statement + loan agreement."
            )
        })

    # Daybook-based 269SS check: look for Journal/Receipt vouchers to loan accounts with cash
    if not daybook.empty:
        cash_loan_receipts = daybook[
            (daybook['VchType'].isin(['Receipt', 'Journal'])) &
            (daybook['Credit'] >= 20000)
        ]
        for _, row in cash_loan_receipts.iterrows():
            party = str(row['Particulars']).strip()
            if any(k in party.lower() for k in ['loan', 'advance', 'director', 'partner']):
                findings.append({
                    'ledger': party,
                    'group': 'Loan Receipt (Daybook)',
                    'balance': row['Credit'],
                    'is_director': False,
                    'documents_required': ['Bank statement confirming receipt was via banking channel'],
                    'law': 'Sec 269SS IT Act — cash loan receipt >₹20,000 attracts penalty = 100% of amount (Sec 271D)',
                    'question': (
                        f"Receipt of Rs.{row['Credit']:,.0f} from '{party}' on "
                        f"{str(row['Date'].date()) if pd.notna(row['Date']) else 'unknown'}. "
                        f"If this was a CASH loan receipt, it violates Sec 269SS — penalty = Rs.{row['Credit']:,.0f}. "
                        f"Confirm: was this received via bank transfer/cheque?"
                    )
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
    """
    Checks expenses that are NOT deductible as business expenses under IT Act:
    - Personal expenses in business books (Sec 37 — only wholly business expenditure allowed)
    - Fines & penalties (Sec 37(1) — explicitly disallowed)
    - Donations to non-80G entities (Sec 80G — only approved institutions)
    - Cash payment disallowance (Sec 40A(3))
    - Drawings booked as expense
    """
    findings = []

    # ── Personal expenses (Sec 37) ───────────────────────────────────────────
    PERSONAL_KEYWORDS = [
        'grocery', 'personal', 'family', 'children', 'school fees', 'tuition',
        'shopping', 'club membership', 'medical expense', 'college fees',
        'birthday', 'wedding', 'party expense', 'tour personal', 'holiday',
        'household', 'home expense', 'domestic', 'vehicle personal',
    ]
    for ledger in ledgers:
        nl  = ledger['name'].lower()
        amt = ledger['debit']
        if any(k in nl for k in PERSONAL_KEYWORDS) and amt > 0:
            findings.append({
                'ledger': ledger['name'], 'amount': amt,
                'type': 'personal_expense',
                'issue': f"'{ledger['name']}' (Rs.{amt:,.0f}) appears to be a personal expense — not deductible as business expense",
                'action': "Verify — if personal, pass journal entry: Dr Drawings A/c / Cr this ledger",
                'law': 'Sec 37(1) IT Act — only expenditure laid out wholly for business purposes is deductible'
            })

    # ── Fines & penalties (Sec 37(1) Explanation — disallowed) ──────────────
    PENALTY_KEYWORDS = ['fine', 'penalty', 'late fee', 'traffic challan', 'challaan', 'compounding fee']
    for ledger in ledgers:
        nl  = ledger['name'].lower()
        amt = ledger['debit']
        if any(k in nl for k in PENALTY_KEYWORDS) and amt > 0:
            findings.append({
                'ledger': ledger['name'], 'amount': amt,
                'type': 'fine_penalty',
                'issue': f"'{ledger['name']}' (Rs.{amt:,.0f}) — fines/penalties are explicitly disallowed as business expense",
                'action': "This amount will be added back in the income tax computation — not a valid deduction",
                'law': 'Sec 37(1) IT Act Explanation 1 — penalty for infraction of law is not deductible'
            })

    # ── Donations — disallowed unless to 80G approved institution ────────────
    DONATION_KEYWORDS = ['donation', 'charity', 'contribution', 'csr expense', 'csr fund']
    for ledger in ledgers:
        nl  = ledger['name'].lower()
        amt = ledger['debit']
        if any(k in nl for k in DONATION_KEYWORDS) and amt > 0:
            findings.append({
                'ledger': ledger['name'], 'amount': amt,
                'type': 'donation',
                'issue': f"'{ledger['name']}' (Rs.{amt:,.0f}) — donations are not deductible as business expense",
                'action': "Only donations to 80G-approved institutions are deductible (as deduction from taxable income, NOT as expense). Obtain 80G certificate from recipient.",
                'law': 'Sec 80G IT Act — deduction for donations; Sec 37 — donations NOT a business expense'
            })

    # ── Drawings booked as expense ────────────────────────────────────────────
    for ledger in ledgers:
        nl  = ledger['name'].lower()
        amt = ledger['debit']
        if 'drawing' in nl and ledger['group'] in ['Indirect Expenses', 'Direct Expenses'] and amt > 0:
            findings.append({
                'ledger': ledger['name'], 'amount': amt,
                'type': 'drawings_as_expense',
                'issue': f"'{ledger['name']}' (Rs.{amt:,.0f}) — Drawings is booked as an expense. Drawings is NOT a business expense; it is a reduction of capital.",
                'action': "Move to Capital Account group. Journal: Dr Capital A/c / Cr Drawings A/c",
                'law': 'Sec 37 IT Act — drawings is not a business expenditure; will be disallowed'
            })

    # ── Cash payment disallowance (Sec 40A(3)) ───────────────────────────────
    cash_violations = audit_cash_violations(daybook)
    cash_disallowed = sum(v['amount'] for v in cash_violations if v['type'] == 'cash_expense')
    if cash_disallowed > 0:
        findings.append({
            'ledger': 'Cash Payments (Sec 40A(3))',
            'amount': cash_disallowed,
            'type': 'cash_disallowance',
            'issue': f"Cash payments above Rs.10,000 total = Rs.{cash_disallowed:,.0f} — will be disallowed under Sec 40A(3)",
            'action': f"Estimated additional tax (@30% bracket) = Rs.{cash_disallowed*0.30:,.0f}. Obtain confirmation that payments were via bank — if yes, dismiss these.",
            'law': 'Sec 40A(3) IT Act — cash expense >₹10,000 per day per person disallowed (₹35,000 for transporters)'
        })

    return findings

# ── MODULE 6B: FIXED ASSETS CHECK ────────────────────────────────────────────
def audit_fixed_assets(ledgers):
    """
    Checks:
    - Fixed assets exist but no depreciation ledger (Schedule II Companies Act 2013)
    - Accumulated depreciation not maintained separately (AS 10 requirement)
    - CARO 2020 Clause 3(i): fixed asset register must be maintained
    - Assets fully depreciated still in books (residual value must be ≥5% of cost per Schedule II)
    """
    findings = []
    fixed_asset_ledgers = [l for l in ledgers if l['group'] == 'Fixed Assets']
    if not fixed_asset_ledgers:
        return findings

    total_gross = sum(l['debit'] for l in fixed_asset_ledgers if l['debit'] > 0)

    # Check for depreciation ledger
    dep_ledgers = [l for l in ledgers if any(k in l['name'].lower()
                   for k in ['depreciation', 'accum. dep', 'accumulated dep', 'dep reserve'])]

    if not dep_ledgers and total_gross > 50000:
        findings.append({
            'type': 'no_depreciation',
            'amount': total_gross,
            'issue': (f"Fixed assets of Rs.{total_gross:,.0f} found but NO depreciation ledger exists. "
                      "Depreciation is mandatory every year on all fixed assets."),
            'action': (
                "Create 'Depreciation' ledger under Indirect Expenses. "
                "Create 'Accumulated Depreciation' ledger under Fixed Assets (credit side). "
                "Calculate depreciation as per Schedule II of Companies Act 2013 (useful life method) "
                "OR Income Tax rates (WDV method) — whichever applies to this entity."
            ),
            'law': 'Schedule II Companies Act 2013 — mandatory depreciation on useful life basis | AS 10 Fixed Assets | CARO 2020 Clause 3(i)',
            'severity': 'Critical'
        })
    else:
        total_dep = sum(abs(l['balance']) for l in dep_ledgers)
        dep_pct   = (total_dep / total_gross * 100) if total_gross > 0 else 0
        findings.append({
            'type': 'depreciation_summary',
            'gross_assets': total_gross,
            'total_depreciation': total_dep,
            'dep_pct': dep_pct,
            'issue': (f"Fixed assets gross = Rs.{total_gross:,.0f}. "
                      f"Accumulated depreciation = Rs.{total_dep:,.0f} ({dep_pct:.1f}% of gross). "
                      "Verify depreciation rates are as per Schedule II Companies Act 2013."),
            'action': "Check useful life used for each asset class matches Schedule II. Residual value must be ≥5% of cost.",
            'law': 'Schedule II Companies Act 2013 | AS 10 Accounting for Fixed Assets',
            'severity': 'Review'
        })

    # CARO 2020 reminder
    findings.append({
        'type': 'caro_fixed_assets',
        'amount': total_gross,
        'issue': (f"CARO 2020 Clause 3(i): Maintain a Fixed Asset Register showing — "
                  "description, location, quantity, gross cost, accumulated depreciation, net book value for each asset."),
        'action': "If not maintained, create FAR immediately. Physical verification of assets at least once in 3 years required.",
        'law': 'CARO 2020 Clause 3(i) — mandatory for companies; best practice for all entities',
        'severity': 'Review'
    })

    return findings


# ── MODULE 7: BANK ACCOUNT DETECTION ─────────────────────────────────────────
BANK_GROUPS = ('Bank Accounts', 'Bank OD A/c')

# These keywords definitively mean NOT a bank account — regardless of which group
# the ledger sits in. Used only to catch obvious misplacements (e.g. "Advance to Staff"
# wrongly placed under "Bank Accounts" group in Tally).
DEFINITELY_NOT_BANK = [
    'advance', 'staff', 'salary', 'wages', 'receivable', 'payable',
    'tds', 'gst', 'tax', 'income tax', 'deposit refund', 'security deposit',
    'investment', 'mutual fund', 'insurance', 'loan', 'capital', 'drawings',
    'expense', 'income', 'sales', 'purchase', 'sundry', 'creditor', 'debtor',
    'provision', 'reserve', 'suspense', 'opening stock', 'closing stock',
]

GENERIC_BANK_NAMES = {'bank accounts', 'bank account', 'bank', 'banks'}

def audit_bank_accounts(ledgers, transactions=None):
    """
    TWO-PASS detection:

    Pass 1 — TB GROUP (primary, authoritative):
        Any ledger under 'Bank Accounts' or 'Bank OD A/c' group = bank account.
        Same logic as Tally, QuickBooks, Zoho Books.
        Safety filter: if name clearly indicates NOT a bank → misclassification.

    Pass 2 — DAYBOOK BEHAVIOUR (catches banks in wrong group):
        In Tally's daybook:
          - Payment voucher  → account Credited   = the bank used to pay
          - Receipt voucher  → account Debited     = the bank that received money
          - Contra voucher   → both sides are bank/cash transfers
        Accounts that consistently fund payments / receive receipts = bank accounts.
        Exclude Cash-in-Hand (physical cash) and accounts already found in Pass 1.
        Cross-reference TB for closing balance.
        Flag as "wrong group" if found here but not under Bank Accounts group in TB.
    """
    findings              = []
    misclassified_as_bank = []
    found_in_pass1        = set()   # ledger names confirmed as banks from TB group

    # ── Pass 1: TB group-based ──────────────────────────────────────────────
    tb_lookup = {l['name'].lower(): l for l in ledgers}

    for ledger in ledgers:
        grp = ledger['group']
        # Also catch ledgers literally named "Bank Accounts" placed under any group
        # (some companies use "Bank Accounts" as the ledger name itself)
        is_bank_group = grp in BANK_GROUPS
        is_named_bank_accounts = ledger['name'].lower() in GENERIC_BANK_NAMES and ledger['balance'] > 0
        if not is_bank_group and not is_named_bank_accounts:
            continue
        bal  = ledger['balance']
        name = ledger['name']
        nl   = name.lower()

        if bal < 0 and grp == 'Bank Accounts':
            misclassified_as_bank.append(ledger)
            continue
        if any(kw in nl for kw in DEFINITELY_NOT_BANK):
            misclassified_as_bank.append(ledger)
            continue

        note_parts = []
        if grp == 'Bank OD A/c':
            note_parts.append('Overdraft account')
        if nl in GENERIC_BANK_NAMES:
            note_parts.append('⚠️ Rename to actual bank name e.g. "HDFC Current A/c"')

        bal_abs = abs(bal)
        dr_cr   = 'Cr (OD)' if bal < 0 else 'Dr'
        found_in_pass1.add(nl)

        findings.append({
            'ledger':    name,
            'balance':   bal_abs,
            'dr_cr':     dr_cr,
            'group':     grp,
            'source':    'TB Group',
            'question':  (
                f"Bank account '{name}' — book balance ₹{bal_abs:,.0f} ({dr_cr}). "
                + (' | '.join(note_parts) + '. ' if note_parts else '')
                + "Reconcile with actual bank statement."
            ),
        })

    # ── Pass 2: Daybook behaviour-based ────────────────────────────────────
    if transactions:
        # Count how many times each account is used as a funding account
        # Payment → Cr side = bank;  Receipt → Dr side = bank;  Contra → both sides
        funding_counts  = {}   # account_name_lower → count of times used as bank
        funding_amounts = {}   # account_name_lower → total amount transacted

        for txn in transactions:
            vtype = str(txn.get('VchType', '')).strip()
            party = str(txn.get('Particulars', '') or '').strip()
            if not party or party.lower() in ('nan', ''):
                continue
            pl  = party.lower()
            amt = float(txn.get('Debit', 0) or 0) + float(txn.get('Credit', 0) or 0)

            if vtype == 'Payment' and float(txn.get('Credit', 0) or 0) > 0:
                # Credited account in payment = bank used to pay
                funding_counts[pl]  = funding_counts.get(pl, 0) + 1
                funding_amounts[pl] = funding_amounts.get(pl, 0) + float(txn.get('Credit', 0))
            elif vtype == 'Receipt' and float(txn.get('Debit', 0) or 0) > 0:
                # Debited account in receipt = bank that received money
                funding_counts[pl]  = funding_counts.get(pl, 0) + 1
                funding_amounts[pl] = funding_amounts.get(pl, 0) + float(txn.get('Debit', 0))
            elif vtype == 'Contra':
                funding_counts[pl]  = funding_counts.get(pl, 0) + 1
                funding_amounts[pl] = funding_amounts.get(pl, 0) + amt

        CASH_KEYWORDS = ['cash', 'petty cash', 'cash in hand', 'cash-in-hand']

        for acc_lower, count in funding_counts.items():
            if acc_lower in found_in_pass1:
                continue
            if any(kw in acc_lower for kw in DEFINITELY_NOT_BANK):
                continue
            if any(kw in acc_lower for kw in CASH_KEYWORDS):
                continue
            # Must appear as funding account at least 3 times to be confident
            if count < 3:
                continue

            total_amt = funding_amounts[acc_lower]
            # Look up TB for closing balance and actual name
            tb_entry = tb_lookup.get(acc_lower)
            bal_abs  = abs(tb_entry['balance']) if tb_entry else 0
            dr_cr    = ('Dr' if tb_entry['balance'] >= 0 else 'Cr') if tb_entry else 'Dr'
            disp_name = tb_entry['name'] if tb_entry else acc_lower.title()
            tb_group  = tb_entry['group'] if tb_entry else 'Unknown'

            note = (
                f"⚠️ Found in daybook ({count} transactions, ₹{total_amt:,.0f} total) "
                f"but placed under '{tb_group}' group in Tally — should be under 'Bank Accounts'."
                if tb_entry else
                f"Found in daybook ({count} transactions) — not in Trial Balance. Verify."
            )

            findings.append({
                'ledger':   disp_name,
                'balance':  bal_abs,
                'dr_cr':    dr_cr,
                'group':    tb_group,
                'source':   'Daybook',
                'question': (
                    f"'{disp_name}' appears to be a bank account (used in {count} payment/receipt entries). "
                    f"Book balance = ₹{bal_abs:,.0f}. {note} "
                    f"Move to 'Bank Accounts' group in Tally for correct classification."
                ),
            })

    findings.append({'_misclassified_as_bank': misclassified_as_bank})
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
    {
        'section': '194A',
        'description': 'Interest on Loans / Deposits (other than bank)',
        'keywords': [
            'interest paid', 'interest on loan', 'interest on unsecured',
            'interest on borrowing', 'interest expense', 'loan interest',
        ],
        'rate': 10.0,
        'single_limit': 5000,
        'annual_limit': 5000,
    },
    {
        'section': '194M',
        'description': 'Contract/Professional payments by Individuals/HUF (>₹50L)',
        'keywords': [
            'contractor payment', 'professional payment', 'consulting fee paid',
        ],
        'rate': 5.0,
        'single_limit': 5000000,
        'annual_limit': 5000000,
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
                            'law':          f"Sec {rule['section']} Income Tax Act — TDS @ {rule['rate']}% on {rule['description']}. Interest u/s 201(1A) @ 1.5%/month for non-deposit.",
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
def audit_salary_compliance(ledgers, daybook=None):
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

    # ── PT check — voucher-level analysis ───────────────────────────────────
    # For every salary payment voucher in the daybook:
    #   1. Find the salary amount paid (Debit on salary/staff ledger)
    #   2. Check if a PT deduction entry (Credit to PT Payable) exists in the SAME voucher
    #   3. Calculate expected PT using WB slabs
    #   4. Sum: expected PT due vs actually deducted vs paid to govt → show gap
    #
    # Journal structure for correct salary payment:
    #   Dr  Salary Expense   (gross)
    #   Cr  PT Payable       (PT deducted)
    #   Cr  PF Payable       (PF deducted)
    #   Cr  Bank / Cash      (net salary paid)

    PT_KEYWORDS    = ['professional tax', 'pt payable', 'p.tax', 'ptax', 'prof tax', 'professionaltax']
    SALARY_KEYWORDS = ['salary', 'wages', 'staff salary', 'staff wages', 'remuneration',
                       'staff incentive', 'incentive']
    PT_GOVT_KEYWORDS = ['professional tax', 'pt payable', 'p.tax', 'grips', 'wbifms', 'prof tax']

    # Voucher-level PT analysis from daybook
    salary_months_missing_pt = []   # months where salary paid but no PT entry
    total_pt_deducted_db     = 0.0  # PT credits seen in salary vouchers
    total_pt_expected_db     = 0.0  # expected PT based on salary amounts
    total_pt_paid_govt       = 0.0  # PT payments to government

    if daybook is not None and not daybook.empty:
        db = daybook.copy()

        # Group rows by voucher (_vid already assigned in parse_daybook)
        # For each voucher, collect: salary debits, PT credits, voucher date
        for vid, grp_df in db.groupby('_vid'):
            particulars = grp_df['Particulars'].str.lower().fillna('')
            vtypes      = grp_df['VchType'].str.lower().fillna('')

            # Only look at Payment and Journal vouchers
            if not vtypes.isin(['payment', 'journal']).any():
                continue

            # Find salary rows (Debit entries for salary ledgers)
            salary_rows = grp_df[
                particulars.str.contains('|'.join(SALARY_KEYWORDS), na=False) &
                (grp_df['Debit'] > 0)
            ]
            if salary_rows.empty:
                continue

            salary_amt = salary_rows['Debit'].sum()

            # Find PT deduction rows (Credit entries for PT ledger in same voucher)
            pt_rows = grp_df[
                particulars.str.contains('|'.join(PT_KEYWORDS), na=False) &
                (grp_df['Credit'] > 0)
            ]
            pt_deducted = pt_rows['Credit'].sum()

            # Expected PT: use WB slab on salary amount
            # Assume monthly salary = salary_amt (each voucher = one month)
            pt_expected = calc_pt(salary_amt)

            total_pt_expected_db += pt_expected
            total_pt_deducted_db += pt_deducted

            # Get voucher date
            date_val = grp_df['Date'].dropna().iloc[0] if not grp_df['Date'].dropna().empty else None
            month_str = date_val.strftime('%b %Y') if date_val is not None else 'Unknown month'

            if pt_expected > 0 and pt_deducted == 0:
                salary_months_missing_pt.append({
                    'month':          month_str,
                    'salary_paid':    salary_amt,
                    'pt_expected':    pt_expected,
                    'pt_deducted':    0,
                    'shortfall':      pt_expected,
                })
            elif pt_deducted < pt_expected:
                salary_months_missing_pt.append({
                    'month':          month_str,
                    'salary_paid':    salary_amt,
                    'pt_expected':    pt_expected,
                    'pt_deducted':    pt_deducted,
                    'shortfall':      pt_expected - pt_deducted,
                })

        # PT payments to government
        pt_govt_rows = db[
            (db['VchType'] == 'Payment') &
            db['Particulars'].str.lower().str.contains('|'.join(PT_GOVT_KEYWORDS), na=False)
        ]
        total_pt_paid_govt = pt_govt_rows['Debit'].sum()

    total_pt_shortfall = total_pt_expected_db - total_pt_deducted_db
    total_pt_unpaid    = max(0, total_pt_deducted_db - total_pt_paid_govt)

    if daybook is not None and not daybook.empty and total_pt_expected_db > 0:
        # Voucher-level result — detailed
        if salary_months_missing_pt:
            month_details = '; '.join(
                f"{m['month']}: salary Rs.{m['salary_paid']:,.0f}, "
                f"PT due Rs.{m['pt_expected']:,.0f}, deducted Rs.{m['pt_deducted']:,.0f}"
                for m in salary_months_missing_pt[:6]
            )
            findings.append({
                'type':           'pt_not_deducted',
                'months':         salary_months_missing_pt,
                'total_shortfall': total_pt_shortfall,
                'issue': (
                    f"PT NOT deducted in {len(salary_months_missing_pt)} salary voucher(s). "
                    f"Total PT shortfall = Rs.{total_pt_shortfall:,.0f}. "
                    f"Details: {month_details}"
                ),
                'impact': (
                    f"Employer is liable to pay the undeducted PT from own pocket. "
                    f"Interest @ 2%/month on shortfall of Rs.{total_pt_shortfall:,.0f}. "
                    "Pass missed journal entries and deposit to Grips portal immediately."
                ),
                'law': 'WB PT Act 1979 — employer must deduct PT from salary; liable even if not deducted',
                'severity': 'Critical',
            })
        else:
            findings.append({
                'type':    'pt_deducted_ok',
                'amount':  total_pt_deducted_db,
                'issue':   f"PT deducted correctly in all salary vouchers. Total PT deducted = Rs.{total_pt_deducted_db:,.0f}.",
                'impact':  '',
                'law':     'WB PT Act 1979',
                'severity': 'Info',
            })

        if total_pt_unpaid > 0:
            findings.append({
                'type':    'pt_not_paid_govt',
                'amount':  total_pt_unpaid,
                'issue': (
                    f"PT deducted from employees = Rs.{total_pt_deducted_db:,.0f} "
                    f"but PT paid to government = Rs.{total_pt_paid_govt:,.0f}. "
                    f"Outstanding PT not yet deposited = Rs.{total_pt_unpaid:,.0f}."
                ),
                'impact': (
                    "PT collected from employees MUST be deposited to state govt by 21st of following month. "
                    f"Late deposit: interest @ 2%/month on Rs.{total_pt_unpaid:,.0f}. "
                    "Pay via Grips portal: wbifms.gov.in"
                ),
                'law': 'WB PT Act 1979 Sec 7 — interest @ 2%/month on delayed deposit',
                'severity': 'Critical',
            })
        elif total_pt_deducted_db > 0:
            findings.append({
                'type':    'pt_paid_govt_ok',
                'amount':  total_pt_paid_govt,
                'issue':   f"PT deposited to government = Rs.{total_pt_paid_govt:,.0f}. All PT collected appears to be deposited.",
                'impact':  "Verify monthly challans on Grips portal match this amount.",
                'law':     'WB PT Act 1979',
                'severity': 'Info',
            })
    else:
        # No daybook or no salary vouchers found — fall back to TB-level estimate
        avg_monthly   = total_salary / 12
        est_employees = max(1, round(avg_monthly / 15000))
        est_annual_pt = calc_pt(avg_monthly / max(est_employees, 1)) * 12 * est_employees

        if not pt_ledgers:
            findings.append({
                'type':          'pt_missing',
                'total_salary':  total_salary,
                'est_annual_pt': est_annual_pt,
                'issue': (
                    f"No PT ledger found. Salary in books = Rs.{total_salary:,.0f}. "
                    f"Estimated PT liability = Rs.{est_annual_pt:,.0f}/year."
                ),
                'impact': (
                    "WB PT slabs: ₹0 (≤₹10K/month), ₹110 (≤₹15K), ₹130 (≤₹25K), "
                    "₹150 (≤₹40K), ₹200 (>₹40K). "
                    "Deposit by 21st every month via Grips portal (wbifms.gov.in)."
                ),
                'law':     'WB PT Act 1979',
                'severity': 'Important',
            })

    return findings


# ── MAIN AUDIT RUNNER ─────────────────────────────────────────────────────────
def run_full_audit(tb_path, db_path=None):
    print("Parsing files...")
    ledgers, company_name, period_str = parse_trial_balance(tb_path)
    daybook = parse_daybook(db_path) if db_path else pd.DataFrame(
        columns=['Date','Particulars','VchType','VchNo','Debit','Credit'])
    print(f"  Company: {company_name} | Period: {period_str}")
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

    print("Module 6B: Fixed Assets...")
    results['fixed_assets'] = audit_fixed_assets(ledgers)

    print("Module 7: Bank Account Detection...")
    # Convert daybook DataFrame to list of dicts for bank scanning
    txn_list = daybook.to_dict('records') if not daybook.empty else []
    bank_result = audit_bank_accounts(ledgers, txn_list)

    # Separate out misclassified-as-bank ledgers and add to ledger_classification
    misclassified = []
    real_banks = []
    for item in bank_result:
        if '_misclassified_as_bank' in item:
            for ledger in item['_misclassified_as_bank']:
                misclassified.append({
                    'severity': 'Critical',
                    'ledger': ledger['name'],
                    'current_group': ledger['group'],
                    'correct_group': 'Direct Incomes or Indirect Incomes',
                    'balance': abs(ledger['balance']),
                    'rule': f"'{ledger['name']}' has a Credit balance under Bank Accounts group — this is an income ledger placed in the wrong group",
                    'fix': f"Gateway → Accounts Info → Ledgers → Alter → {ledger['name']} → Change Group to Direct Incomes or Indirect Incomes"
                })
        else:
            real_banks.append(item)

    results['bank_accounts'] = real_banks
    results['ledger_classification'].extend(misclassified)

    print("Module 8: TDS Compliance...")
    results['tds_compliance'] = audit_tds_compliance(ledgers, daybook)

    print("Module 9: Salary / PF / PT Compliance...")
    results['salary_compliance'] = audit_salary_compliance(ledgers, daybook)

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
    fa_issues = sum(1 for f in results['fixed_assets'] if f.get('severity') == 'Critical')
    questions = len(results['loans']) + len(results['large_expenses']) + len(results['bank_accounts'])
    # Cash violations: cap penalty at 20 pts (unverified — could be bank payments)
    cash_penalty = min(20, cash_violations_count)
    score = max(0, 100 - (critical * 8) - (warnings * 1) - (questions * 2)
                      - (tds_critical * 6) - (salary_issues * 3) - (fa_issues * 5) - cash_penalty)

    # Module status — green confirmation when a module finds zero issues
    module_status = {
        'ledger_classification': {
            'count': len(results['ledger_classification']),
            'ok_msg': f'All {len(ledgers)} ledgers checked — no mis-classification found. Groups are correct as per ICAI standards.',
        },
        'cash_violations': {
            'count': cash_violations_count,
            'ok_msg': 'No cash violations found — all payments appear to be within Sec 40A(3) limits or made via bank.',
        },
        'tds_compliance': {
            'count': tds_critical,
            'ok_msg': 'No TDS compliance issues detected — payments to contractors/professionals appear within threshold limits.',
        },
        'outstanding': {
            'count': len(results['outstanding']),
            'ok_msg': 'No abnormal balances — suspense accounts are nil, debtors/creditors look normal.',
        },
        'large_expenses': {
            'count': len(results['large_expenses']),
            'ok_msg': 'No payments above ₹1L found in daybook — or all large payments already verified.',
        },
        'loans': {
            'count': len(results['loans']),
            'ok_msg': 'No loan accounts found requiring documentation.',
        },
        'itr': {
            'count': len(results['itr']),
            'ok_msg': 'No personal expenses detected in business books — books appear clean for ITR filing.',
        },
        'salary_compliance': {
            'count': salary_issues,
            'ok_msg': 'No salary/PF/PT issues found — compliance appears in order.',
        },
        'bank_accounts': {
            'count': len(results['bank_accounts']),
            'ok_msg': 'No bank accounts detected in books — upload daybook to enable bank detection.',
        },
        'fixed_assets': {
            'count': fa_issues,
            'ok_msg': 'No fixed assets found in books — or depreciation is correctly maintained.',
        },
    }

    results['module_status'] = module_status
    results['summary'] = {
        'company': company_name or 'Your Company',
        'period':  period_str  or 'FY 2025-26',
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
