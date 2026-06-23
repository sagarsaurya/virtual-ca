import pandas as pd
import re

# Patterns that suggest a bill/invoice reference exists
BILL_PATTERNS = [
    r'\b(bill|invoice|inv|receipt|voucher|challan|ref|po|order)\s*[#:\-]?\s*\d+',
    r'\b[A-Z]{2,5}[-/]\d{3,}',        # e.g. INV-001, PO/2024
    r'\b\d{4,}[-/]\d+',               # e.g. 2024/001
    r'gst\s*invoice',
    r'tax invoice',
]

# Narrations that are definitely undocumented
UNDOCUMENTED_KEYWORDS = [
    'cash', 'petty cash', 'miscellaneous', 'misc', 'sundry', 'expenses',
    'as per voucher', 'being amount', 'to account', 'by account',
    'payment made', 'amount paid', 'transferred', 'neft', 'rtgs', 'imps',
    'upi', 'online transfer', 'bank transfer',
]

# High-risk transactions that MUST have documentation
HIGH_RISK_KEYWORDS = [
    'purchase', 'contractor', 'professional', 'legal', 'rent', 'salary',
    'repair', 'maintenance', 'commission', 'advertisement', 'travel',
    'hotel', 'conveyance', 'fuel', 'vehicle',
]

CASH_THRESHOLD   = 10000   # Flag cash payments above this
AMOUNT_THRESHOLD = 5000    # Only flag entries above this

def _has_bill_ref(narration):
    n = (narration or '').lower()
    for pattern in BILL_PATTERNS:
        if re.search(pattern, n, re.IGNORECASE):
            return True
    return False

def _is_undocumented(narration):
    n = (narration or '').lower()
    if not n or n in ('', 'nan'):
        return True, 'No narration'
    for kw in UNDOCUMENTED_KEYWORDS:
        if n.strip() == kw or n == kw + ' payment':
            return True, f'Generic narration: "{narration}"'
    return False, ''

def _is_high_risk(narration):
    n = (narration or '').lower()
    for kw in HIGH_RISK_KEYWORDS:
        if kw in n:
            return True
    return False

def check_documents(daybook_path=None, tb_path=None):
    if not daybook_path:
        # Fall back to TB-based check
        return _check_from_tb(tb_path)

    try:
        df = pd.read_excel(daybook_path, header=None)
    except:
        return _check_from_tb(tb_path)

    flagged      = []
    documented   = []
    no_narration = []
    total_rows   = 0

    for _, row in df.iterrows():
        vals = [str(c).strip() for c in row if pd.notna(c) and str(c).strip() not in ('', 'nan')]
        if len(vals) < 3:
            continue

        # Try to extract date, narration, amount
        date_val  = None
        amount    = 0
        narration = ''
        party     = ''

        for v in vals:
            # Date — handle pandas Timestamp strings and standard formats
            if date_val is None:
                try:
                    import datetime
                    import pandas as _pd
                    parsed = _pd.to_datetime(v, errors='coerce')
                    if not _pd.isna(parsed):
                        date_val = parsed.date()
                except:
                    pass
            # Amount
            try:
                num = float(v.replace(',','').replace('₹',''))
                if num > AMOUNT_THRESHOLD:
                    amount = num
            except:
                pass
            # Narration (longest text string)
            if len(v) > len(narration) and not v.replace(',','').replace('.','').isdigit():
                if not date_val or str(date_val) not in v:
                    narration = v

        if not date_val or amount < AMOUNT_THRESHOLD:
            continue

        total_rows += 1
        has_bill = _has_bill_ref(narration)
        is_undoc, undoc_reason = _is_undocumented(narration)
        high_risk = _is_high_risk(narration)

        entry = {
            'date': str(date_val),
            'narration': narration[:80],
            'amount': round(amount, 0),
            'has_bill_ref': has_bill,
            'high_risk': high_risk,
        }

        if not narration or is_undoc:
            no_narration.append({**entry, 'issue': undoc_reason or 'No narration', 'risk': 'High' if high_risk else 'Medium'})
        elif not has_bill and high_risk:
            flagged.append({**entry, 'issue': 'No bill/invoice reference in narration', 'risk': 'High'})
        elif not has_bill:
            flagged.append({**entry, 'issue': 'No bill/invoice reference', 'risk': 'Medium'})
        else:
            documented.append(entry)

    all_flagged = no_narration + flagged
    total_amount_at_risk = sum(e['amount'] for e in all_flagged)

    return {
        'flagged': all_flagged,
        'documented': documented,
        'no_narration': no_narration,
        'missing_bill_ref': flagged,
        'total_checked': total_rows,
        'flagged_count': len(all_flagged),
        'documented_count': len(documented),
        'total_amount_at_risk': round(total_amount_at_risk, 0),
        'high_risk_count': len([e for e in all_flagged if e.get('risk') == 'High']),
    }

def _check_from_tb(tb_path):
    if not tb_path:
        return {'flagged': [], 'documented': [], 'total_checked': 0, 'flagged_count': 0,
                'documented_count': 0, 'total_amount_at_risk': 0, 'high_risk_count': 0,
                'note': 'Upload daybook for document checking'}
    from audit_engine import parse_trial_balance
    ledgers, _, _ = parse_trial_balance(tb_path)
    flagged = []
    for l in ledgers:
        name  = l.get('name') or ''
        bal   = abs(float(l.get('debit') or 0) - float(l.get('credit') or 0))
        group = (l.get('group') or '').lower()
        if bal < AMOUNT_THRESHOLD:
            continue
        if 'expense' in group or 'purchase' in group:
            if _is_high_risk(name):
                flagged.append({'date': '—', 'narration': name, 'amount': round(bal, 0),
                                'issue': 'High-risk ledger — verify bills exist', 'risk': 'High'})
    return {'flagged': flagged, 'documented': [], 'total_checked': len(ledgers),
            'flagged_count': len(flagged), 'documented_count': 0,
            'total_amount_at_risk': sum(e['amount'] for e in flagged),
            'high_risk_count': len(flagged),
            'note': 'Upload daybook for detailed entry-wise document check'}
