import pandas as pd

# Schedule III — Companies Act 2013 grouping map
# Tally group → (side, section, subsection)
GROUP_MAP = {
    # EQUITY & LIABILITIES
    'Capital Account':            ('liabilities', 'equity', 'Share Capital / Proprietor Capital'),
    'Reserves & Surplus':         ('liabilities', 'equity', 'Reserves & Surplus'),
    'Share Capital':              ('liabilities', 'equity', 'Share Capital / Proprietor Capital'),
    'Retained Earnings':          ('liabilities', 'equity', 'Reserves & Surplus'),
    'Secured Loans':              ('liabilities', 'noncurrent', 'Long-term Borrowings'),
    'Unsecured Loans':            ('liabilities', 'noncurrent', 'Long-term Borrowings'),
    'Long-term Liabilities':      ('liabilities', 'noncurrent', 'Other Long-term Liabilities'),
    'Long-term Provisions':       ('liabilities', 'noncurrent', 'Long-term Provisions'),
    'Sundry Creditors':           ('liabilities', 'current', 'Trade Payables'),
    'Current Liabilities':        ('liabilities', 'current', 'Other Current Liabilities'),
    'Duties & Taxes':             ('liabilities', 'current', 'Other Current Liabilities'),
    'Provisions':                 ('liabilities', 'current', 'Short-term Provisions'),
    'Bank OD Account':            ('liabilities', 'current', 'Short-term Borrowings'),
    # ASSETS
    'Fixed Assets':               ('assets', 'noncurrent', 'Property, Plant & Equipment'),
    'Intangible Assets':          ('assets', 'noncurrent', 'Intangible Assets'),
    'Capital Work-in-Progress':   ('assets', 'noncurrent', 'Capital Work-in-Progress'),
    'Investments':                ('assets', 'noncurrent', 'Non-current Investments'),
    'Long-term Loans & Advances': ('assets', 'noncurrent', 'Long-term Loans & Advances'),
    'Loans & Advances (Asset)':   ('assets', 'noncurrent', 'Long-term Loans & Advances'),
    'Stock-in-Hand':              ('assets', 'current', 'Inventories'),
    'Sundry Debtors':             ('assets', 'current', 'Trade Receivables'),
    'Bank Accounts':              ('assets', 'current', 'Cash & Cash Equivalents'),
    'Cash-in-Hand':               ('assets', 'current', 'Cash & Cash Equivalents'),
    'Current Assets':             ('assets', 'current', 'Other Current Assets'),
    'Loans & Advances':           ('assets', 'current', 'Short-term Loans & Advances'),
    'Deposits (Asset)':           ('assets', 'current', 'Other Current Assets'),
    'Miscellaneous Expenses (Asset)': ('assets', 'noncurrent', 'Other Non-current Assets'),
}

# Keywords to auto-detect group if not explicitly mapped
KEYWORD_GROUPS = [
    (['fixed asset','plant','machinery','vehicle','furniture','equipment','building','land'],
     ('assets', 'noncurrent', 'Property, Plant & Equipment')),
    (['bank','hdfc','icici','sbi','axis','kotak','current account','saving account'],
     ('assets', 'current', 'Cash & Cash Equivalents')),
    (['cash','petty cash'],
     ('assets', 'current', 'Cash & Cash Equivalents')),
    (['debtor','receivable','trade receivable'],
     ('assets', 'current', 'Trade Receivables')),
    (['stock','inventory','closing stock'],
     ('assets', 'current', 'Inventories')),
    (['creditor','trade payable','supplier'],
     ('liabilities', 'current', 'Trade Payables')),
    (['loan from','unsecured loan','secured loan','term loan','od limit'],
     ('liabilities', 'noncurrent', 'Long-term Borrowings')),
    (['capital','proprietor','partner'],
     ('liabilities', 'equity', 'Share Capital / Proprietor Capital')),
    (['gst','tds payable','duties','tax payable'],
     ('liabilities', 'current', 'Other Current Liabilities')),
    (['investment','mutual fund','share','equity shares held'],
     ('assets', 'noncurrent', 'Non-current Investments')),
    (['prepaid','advance paid','deposit paid','security deposit'],
     ('assets', 'current', 'Other Current Assets')),
    (['advance from customer','customer advance'],
     ('liabilities', 'current', 'Other Current Liabilities')),
    (['salary payable','outstanding salary','audit fee payable'],
     ('liabilities', 'current', 'Other Current Liabilities')),
]

def _classify(group_name, ledger_name):
    g = (group_name or '').strip()
    if g in GROUP_MAP:
        return GROUP_MAP[g]
    # keyword match on group name first
    g_lower = g.lower()
    l_lower = (ledger_name or '').lower()
    for kws, mapping in KEYWORD_GROUPS:
        for kw in kws:
            if kw in g_lower or kw in l_lower:
                return mapping
    return None

def generate_balance_sheet(tb_path):
    from audit_engine import parse_trial_balance
    ledgers, _, _ = parse_trial_balance(tb_path)

    assets = {}
    liabilities = {}
    unclassified = []

    for l in ledgers:
        name   = l.get('name', '')
        group  = l.get('group', '')
        debit  = float(l.get('debit') or 0)
        credit = float(l.get('credit') or 0)
        bal    = abs(debit - credit)
        dr_cr  = 'DR' if debit >= credit else 'CR'
        if not name or bal == 0:
            continue

        mapping = _classify(group, name)
        if not mapping:
            unclassified.append({'ledger': name, 'group': group, 'balance': abs(bal), 'dr_cr': dr_cr})
            continue

        side, section, subsection = mapping
        bucket = assets if side == 'assets' else liabilities
        if subsection not in bucket:
            bucket[subsection] = {'section': section, 'items': [], 'total': 0}
        entry_bal = abs(bal)
        bucket[subsection]['items'].append({'ledger': name, 'balance': entry_bal, 'dr_cr': dr_cr})
        bucket[subsection]['total'] += entry_bal

    total_assets = sum(v['total'] for v in assets.values())
    total_liabilities = sum(v['total'] for v in liabilities.values())
    diff = round(total_assets - total_liabilities, 2)
    tallied = abs(diff) < 1

    return {
        'assets': assets,
        'liabilities': liabilities,
        'total_assets': round(total_assets, 2),
        'total_liabilities': round(total_liabilities, 2),
        'difference': diff,
        'tallied': tallied,
        'unclassified': unclassified,
    }
