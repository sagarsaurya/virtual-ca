import pandas as pd

# AS-3 Cash Flow categorization
# Keyword → (activity, direction_hint)
ACTIVITY_MAP = [
    # OPERATING
    (['customer', 'debtor', 'trade receivable', 'sales receipt', 'revenue receipt'],
     'operating', 'inflow', 'Cash received from customers'),
    (['supplier', 'creditor', 'purchase payment', 'vendor', 'trade payable'],
     'operating', 'outflow', 'Cash paid to suppliers'),
    (['salary', 'wages', 'payroll', 'staff payment', 'employee'],
     'operating', 'outflow', 'Cash paid to employees'),
    (['rent', 'office rent', 'factory rent'],
     'operating', 'outflow', 'Rent paid'),
    (['professional fee', 'consultancy', 'legal fee', 'audit fee'],
     'operating', 'outflow', 'Professional fees paid'),
    (['tds', 'tax deducted', 'income tax', 'advance tax', 'gst paid', 'gst payable'],
     'operating', 'outflow', 'Taxes paid'),
    (['interest received', 'bank interest received'],
     'operating', 'inflow', 'Interest received'),
    (['dividend received'],
     'operating', 'inflow', 'Dividends received'),
    (['electricity', 'telephone', 'internet', 'utility', 'insurance'],
     'operating', 'outflow', 'Overhead expenses'),
    (['advertisement', 'marketing', 'printing', 'stationery'],
     'operating', 'outflow', 'Selling & admin expenses'),
    # INVESTING
    (['fixed asset', 'plant', 'machinery', 'vehicle', 'furniture', 'equipment',
      'building purchase', 'land purchase', 'capital expenditure', 'capex'],
     'investing', 'outflow', 'Purchase of fixed assets'),
    (['sale of asset', 'asset sold', 'disposal of asset'],
     'investing', 'inflow', 'Proceeds from sale of assets'),
    (['investment purchase', 'mutual fund purchase', 'shares purchased', 'share bought'],
     'investing', 'outflow', 'Investment purchases'),
    (['redemption', 'investment sold', 'share sold', 'mutual fund sold'],
     'investing', 'inflow', 'Investment proceeds'),
    (['loan given', 'advance given', 'loan to'],
     'investing', 'outflow', 'Loans given'),
    (['loan recovered', 'advance recovered', 'loan repaid by'],
     'investing', 'inflow', 'Loan repayments received'),
    # FINANCING
    (['loan taken', 'borrowing', 'term loan received', 'od sanctioned', 'bank loan'],
     'financing', 'inflow', 'Proceeds from borrowings'),
    (['loan repaid', 'emi paid', 'loan repayment', 'term loan paid'],
     'financing', 'outflow', 'Repayment of borrowings'),
    (['capital introduced', 'capital contribution', 'share capital received'],
     'financing', 'inflow', 'Capital introduced'),
    (['drawings', 'dividend paid', 'profit withdrawal'],
     'financing', 'outflow', 'Drawings / Dividends paid'),
    (['interest paid', 'interest on loan'],
     'financing', 'outflow', 'Interest paid on borrowings'),
]

BANK_KEYWORDS = ['bank', 'hdfc', 'icici', 'sbi', 'axis', 'kotak', 'current account', 'saving']
CASH_KEYWORDS = ['cash', 'petty cash', 'cash in hand']

def _categorize(narration):
    n = (narration or '').lower()
    for kws, activity, direction, label in ACTIVITY_MAP:
        if any(kw in n for kw in kws):
            return activity, direction, label
    return 'operating', 'outflow', 'Other operating expenses'

def generate_cash_flow(tb_path, daybook_path=None):
    from audit_engine import parse_trial_balance
    ledgers = parse_trial_balance(tb_path)

    # Find bank and cash ledgers from TB
    bank_ledgers = []
    cash_ledgers = []
    for l in ledgers:
        name  = (l.get('ledger') or '').lower()
        group = (l.get('group') or '').lower()
        if any(kw in name for kw in BANK_KEYWORDS) or 'bank' in group:
            bank_ledgers.append(l)
        elif any(kw in name for kw in CASH_KEYWORDS) or 'cash' in group:
            cash_ledgers.append(l)

    # Build cash flow from TB balances (indirect method approximation)
    operating_inflows  = []
    operating_outflows = []
    investing_inflows  = []
    investing_outflows = []
    financing_inflows  = []
    financing_outflows = []

    def add(activity, direction, label, amount, ledger=''):
        entry = {'label': label, 'amount': round(abs(amount), 0), 'ledger': ledger}
        if activity == 'operating':
            (operating_inflows if direction == 'inflow' else operating_outflows).append(entry)
        elif activity == 'investing':
            (investing_inflows if direction == 'inflow' else investing_outflows).append(entry)
        else:
            (financing_inflows if direction == 'inflow' else financing_outflows).append(entry)

    for l in ledgers:
        name  = l.get('ledger') or ''
        group = (l.get('group') or '').lower()
        bal   = abs(float(l.get('closing_balance') or l.get('balance') or 0))
        dr_cr = (l.get('dr_cr') or '').upper()

        if bal < 500:
            continue

        activity, direction, label = _categorize(name + ' ' + group)

        # Override direction by Dr/Cr if possible
        if 'income' in group or 'sales' in group:
            activity, direction, label = 'operating', 'inflow', 'Cash received from customers'
        elif 'expense' in group or 'purchase' in group:
            activity, direction, label = 'operating', 'outflow', label

        add(activity, direction, label, bal, name)

    def total(lst): return sum(e['amount'] for e in lst)

    net_operating  = total(operating_inflows)  - total(operating_outflows)
    net_investing  = total(investing_inflows)  - total(investing_outflows)
    net_financing  = total(financing_inflows)  - total(financing_outflows)
    net_cash_flow  = net_operating + net_investing + net_financing

    open_cash  = sum(abs(float(l.get('opening_balance') or 0)) for l in bank_ledgers + cash_ledgers)
    close_cash = sum(abs(float(l.get('closing_balance') or l.get('balance') or 0)) for l in bank_ledgers + cash_ledgers)

    return {
        'operating': {'inflows': operating_inflows, 'outflows': operating_outflows, 'net': round(net_operating, 0)},
        'investing': {'inflows': investing_inflows, 'outflows': investing_outflows, 'net': round(net_investing, 0)},
        'financing': {'inflows': financing_inflows, 'outflows': financing_outflows, 'net': round(net_financing, 0)},
        'net_cash_flow': round(net_cash_flow, 0),
        'opening_cash': round(open_cash, 0),
        'closing_cash': round(close_cash, 0),
        'bank_ledgers': [l.get('ledger','') for l in bank_ledgers],
        'cash_ledgers': [l.get('ledger','') for l in cash_ledgers],
        'note': 'Direct method — based on Trial Balance ledger groupings',
    }
