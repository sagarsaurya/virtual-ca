import pandas as pd

def _read_ledger(path):
    try:
        df = pd.read_excel(path, header=None)
        entries = []
        for _, row in df.iterrows():
            vals = [str(c).strip() for c in row if pd.notna(c) and str(c).strip() not in ('', 'nan')]
            if len(vals) < 2:
                continue
            date_val = None
            amount   = None
            narration = ''
            dr_cr = ''
            for v in vals:
                # Try date
                for fmt in ('%d-%m-%Y','%d/%m/%Y','%Y-%m-%d','%d-%b-%Y','%d %b %Y'):
                    try:
                        import datetime
                        date_val = datetime.datetime.strptime(v, fmt).date()
                        break
                    except:
                        pass
                # Try amount
                try:
                    num = float(v.replace(',','').replace('₹',''))
                    if num > 0:
                        amount = num
                except:
                    pass
                # Dr/Cr
                if v.upper() in ('DR','CR','DEBIT','CREDIT'):
                    dr_cr = v.upper()[:2]
                # Narration (longest string)
                if len(v) > 4 and not any(c.isdigit() for c in v[:3]):
                    narration = v

            if date_val and amount:
                entries.append({
                    'date': str(date_val),
                    'narration': narration[:60],
                    'amount': round(amount, 2),
                    'dr_cr': dr_cr or 'DR',
                })
        return entries
    except Exception as e:
        return []

def reconcile_party(tally_path, party_path, party_name='Party'):
    tally_entries = _read_ledger(tally_path)
    party_entries = _read_ledger(party_path)

    # Match by date + amount (within ₹1 tolerance)
    matched       = []
    only_tally    = []
    only_party    = []
    amount_diff   = []

    party_remaining = list(party_entries)

    for te in tally_entries:
        found = False
        for i, pe in enumerate(party_remaining):
            if te['date'] == pe['date'] and abs(te['amount'] - pe['amount']) <= 1:
                matched.append({'date': te['date'], 'narration': te['narration'],
                                'tally_amount': te['amount'], 'party_amount': pe['amount'],
                                'diff': 0, 'status': 'matched'})
                party_remaining.pop(i)
                found = True
                break
            # Same date, different amount
            if te['date'] == pe['date'] and abs(te['amount'] - pe['amount']) > 1:
                amount_diff.append({'date': te['date'],
                                    'narration': te['narration'],
                                    'tally_amount': te['amount'],
                                    'party_amount': pe['amount'],
                                    'diff': round(te['amount'] - pe['amount'], 2),
                                    'status': 'amount_mismatch'})
                party_remaining.pop(i)
                found = True
                break
        if not found:
            only_tally.append({'date': te['date'], 'narration': te['narration'],
                               'tally_amount': te['amount'], 'party_amount': 0,
                               'diff': te['amount'], 'status': 'only_in_tally'})

    for pe in party_remaining:
        only_party.append({'date': pe['date'], 'narration': pe['narration'],
                           'tally_amount': 0, 'party_amount': pe['amount'],
                           'diff': -pe['amount'], 'status': 'only_in_party'})

    tally_balance = sum(e['amount'] for e in tally_entries)
    party_balance = sum(e['amount'] for e in party_entries)

    return {
        'party_name': party_name,
        'matched': matched,
        'only_tally': only_tally,
        'only_party': only_party,
        'amount_diff': amount_diff,
        'tally_balance': round(tally_balance, 2),
        'party_balance': round(party_balance, 2),
        'balance_diff': round(tally_balance - party_balance, 2),
        'total_tally': len(tally_entries),
        'total_party': len(party_entries),
        'matched_count': len(matched),
        'unmatched_count': len(only_tally) + len(only_party) + len(amount_diff),
        'is_reconciled': len(only_tally) == 0 and len(only_party) == 0 and len(amount_diff) == 0,
    }
