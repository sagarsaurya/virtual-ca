import pandas as pd

# TDS rules — Income Tax Act 1961
TDS_RULES = [
    {'keywords': ['contractor','labour contractor','subcontractor','sub contractor','transport','freight','cargo'],
     'section': '194C', 'rate_individual': 1, 'rate_company': 2, 'threshold_single': 30000, 'threshold_annual': 100000,
     'description': 'Payment to contractor/sub-contractor'},
    {'keywords': ['professional fee','professional fees','consultancy','consultant','legal fee','legal fees',
                  'advocate','ca fee','audit fee','technical fee','management fee','retainer'],
     'section': '194J', 'rate_individual': 10, 'rate_company': 10, 'threshold_single': 50000, 'threshold_annual': 50000,
     'description': 'Professional / technical services'},
    {'keywords': ['rent','office rent','lease rent','godown rent','warehouse rent','shop rent','factory rent'],
     'section': '194I', 'rate_individual': 10, 'rate_company': 10, 'threshold_single': 1, 'threshold_annual': 240000,
     'description': 'Rent (land, building, plant, machinery)'},
    {'keywords': ['commission','brokerage','agency commission','sales commission','distribution commission'],
     'section': '194H', 'rate_individual': 5, 'rate_company': 5, 'threshold_single': 15000, 'threshold_annual': 15000,
     'description': 'Commission or brokerage'},
    {'keywords': ['interest on loan','interest paid','bank interest','loan interest','interest on od'],
     'section': '194A', 'rate_individual': 10, 'rate_company': 10, 'threshold_single': 1, 'threshold_annual': 40000,
     'description': 'Interest (other than securities)'},
    {'keywords': ['director remuneration','director sitting fee','sitting fee','director salary'],
     'section': '194J', 'rate_individual': 10, 'rate_company': 10, 'threshold_single': 50000, 'threshold_annual': 50000,
     'description': 'Director remuneration / sitting fees'},
    {'keywords': ['royalty','copyright','patent'],
     'section': '194J', 'rate_individual': 10, 'rate_company': 10, 'threshold_single': 30000, 'threshold_annual': 30000,
     'description': 'Royalty payments'},
    {'keywords': ['advertisement','media agency','ad agency','marketing agency'],
     'section': '194C', 'rate_individual': 1, 'rate_company': 2, 'threshold_single': 30000, 'threshold_annual': 100000,
     'description': 'Advertisement contracts'},
    {'keywords': ['insurance commission','lic commission'],
     'section': '194D', 'rate_individual': 5, 'rate_company': 5, 'threshold_single': 15000, 'threshold_annual': 15000,
     'description': 'Insurance commission'},
]

# Ledger names that indicate TDS was already deducted — skip these
TDS_DEDUCTED_KEYWORDS = ['tds deducted', 'tds payable', 'tax deducted', 'tds on', 'tds @ ']

def _match_rule(ledger_name):
    name_lower = ledger_name.lower()
    for rule in TDS_RULES:
        for kw in rule['keywords']:
            if kw in name_lower:
                return rule
    return None

def detect_missed_tds(tb_path, daybook_path=None):
    from audit_engine import parse_trial_balance
    ledgers = parse_trial_balance(tb_path)

    # Build set of ledgers where TDS was deducted
    tds_deducted_parties = set()
    for l in ledgers:
        name = (l.get('ledger') or '').lower()
        for kw in TDS_DEDUCTED_KEYWORDS:
            if kw in name:
                tds_deducted_parties.add(name)

    results = []
    party_totals = {}

    # Check trial balance ledgers (expense side) against TDS rules
    for l in ledgers:
        name   = l.get('ledger') or ''
        group  = (l.get('group') or '').lower()
        bal    = abs(float(l.get('closing_balance') or l.get('balance') or 0))
        dr_cr  = (l.get('dr_cr') or '').upper()

        if bal < 1000:
            continue
        # Only look at expense/payment ledgers (Dr balances in expense groups)
        if dr_cr != 'DR' and 'expense' not in group and 'indirect' not in group and 'direct' not in group:
            continue

        rule = _match_rule(name)
        if not rule:
            continue

        # Check if annual threshold crossed
        annual_threshold = rule['threshold_annual']
        if bal < annual_threshold:
            continue

        # Check if TDS already exists for this party
        name_lower = name.lower()
        tds_exists = any(name_lower in td or td in name_lower for td in tds_deducted_parties)

        rate = rule['rate_company']
        tds_due = round(bal * rate / 100, 0)
        interest_est = round(tds_due * 0.015 * 3, 0)  # 1.5%/month * 3 months avg delay

        results.append({
            'ledger': name,
            'section': rule['section'],
            'description': rule['description'],
            'total_paid': round(bal, 0),
            'rate': rate,
            'threshold': annual_threshold,
            'tds_due': tds_due,
            'interest_est': interest_est,
            'tds_already_deducted': tds_exists,
            'action': f"Deduct TDS u/s {rule['section']} @ {rate}% = ₹{int(tds_due):,}. "
                      f"Deposit via Challan 281 by 7th of next month. "
                      f"File Form 26Q (quarterly return).",
        })

    # Sort: missed TDS first, then already deducted
    results.sort(key=lambda x: (x['tds_already_deducted'], -x['tds_due']))

    total_exposure = sum(r['tds_due'] for r in results if not r['tds_already_deducted'])
    total_interest = sum(r['interest_est'] for r in results if not r['tds_already_deducted'])
    missed_count = sum(1 for r in results if not r['tds_already_deducted'])

    return {
        'items': results,
        'total_exposure': round(total_exposure, 0),
        'total_interest': round(total_interest, 0),
        'missed_count': missed_count,
        'total_checked': len(results),
    }
