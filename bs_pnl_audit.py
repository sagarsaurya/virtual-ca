"""
BS + P&L Audit Module
Runs compliance checks on Balance Sheet and P&L exports from Tally.
"""
import pandas as pd

# Director remuneration limit (Sec 197 Companies Act 2013)
DIRECTOR_REMUNERATION_LIMIT = 8400000  # ₹84L per year (11% of net profit — flag for review)

DIRECTOR_KEYWORDS   = ['director', 'md remuneration', 'managing director', 'cmd']
RENT_KEYWORDS       = ['rent', 'lease rent', 'office rent', 'godown rent']
PROFESSIONAL_KEYWORDS = ['professional fee', 'consultancy', 'consultant', 'legal fee',
                         'advocate', 'ca fee', 'audit fee']
DEPRECIATION_KEYWORDS = ['depreciation', 'dep.', 'amortisation', 'amortization']
DONATION_KEYWORDS   = ['donation', 'csr', 'charitable']
UNSECURED_KEYWORDS  = ['unsecured loan', 'loan from director', 'director loan',
                       'loan from partner', 'shareholder loan']
SUNDRY_DEBTOR_KEYWORDS = ['sundry debtor', 'trade receivable', 'debtors']
ADVANCE_TAX_KEYWORDS   = ['advance tax', 'self assessment tax', 'income tax paid']
TDS_PAYABLE_KEYWORDS   = ['tds payable', 'tax deducted at source payable', 'tds on']


def _read_sheet(path):
    """Read an Excel file, return flat list of (name, amount) tuples."""
    if path is None:
        return []
    try:
        df = pd.read_excel(path, header=None)
    except Exception:
        return []

    rows = []
    for _, row in df.iterrows():
        name = str(row[0]).strip() if pd.notna(row[0]) else ''
        if not name or name.lower() in ('nan', '', 'particulars', 'ledger name'):
            continue
        amt = 0.0
        for col in row[1:]:
            try:
                v = float(col)
                if v != 0:
                    amt = abs(v)
                    break
            except Exception:
                continue
        rows.append((name, amt))
    return rows


def _match(name, keywords):
    nl = name.lower()
    return any(k in nl for k in keywords)


def audit_bs_pnl(bs_path, pnl_path, existing_audit):
    """
    Returns (bs_findings, pnl_findings) — lists of audit finding dicts.
    Each finding: {type, ledger, amount, message, severity, law}
    """
    bs_rows  = _read_sheet(bs_path)
    pnl_rows = _read_sheet(pnl_path)

    bs_findings  = []
    pnl_findings = []

    # ── BALANCE SHEET CHECKS ─────────────────────────────────────────────────

    for name, amt in bs_rows:

        # Unsecured loans — Sec 269SS
        if _match(name, UNSECURED_KEYWORDS) and amt > 20000:
            bs_findings.append({
                'type': 'LOAN',
                'ledger': name,
                'amount': amt,
                'message': f'Unsecured loan ₹{amt:,.0f} — verify Mode of Receipt (must not be cash) and documentation',
                'severity': 'Critical',
                'law': 'Sec 269SS IT Act — loan >₹20,000 must be via banking channel',
            })

        # TDS Payable sitting long
        if _match(name, TDS_PAYABLE_KEYWORDS) and amt > 0:
            bs_findings.append({
                'type': 'TDS',
                'ledger': name,
                'amount': amt,
                'message': f'TDS Payable ₹{amt:,.0f} outstanding — confirm deposited to govt',
                'severity': 'Critical',
                'law': 'Sec 200 IT Act — TDS must be deposited by 7th of following month',
            })

        # Sundry Debtors — very high balance
        if _match(name, SUNDRY_DEBTOR_KEYWORDS) and amt > 500000:
            bs_findings.append({
                'type': 'BALANCE',
                'ledger': name,
                'amount': amt,
                'message': f'Sundry Debtors ₹{amt:,.0f} — check for debtors outstanding >6 months (bad debt provision)',
                'severity': 'Review',
                'law': 'AS-9 Revenue Recognition — verify recoverability',
            })

        # Advance Tax — if profit exists but no advance tax paid
        if _match(name, ADVANCE_TAX_KEYWORDS) and amt == 0:
            bs_findings.append({
                'type': 'TAX',
                'ledger': name,
                'amount': 0,
                'message': 'Advance Tax shows ₹0 — verify if applicable (required if tax liability >₹10,000)',
                'severity': 'Review',
                'law': 'Sec 208 IT Act — advance tax mandatory if estimated tax >₹10,000',
            })

    # ── P&L CHECKS ───────────────────────────────────────────────────────────

    has_depreciation = False
    total_rent = 0
    total_professional = 0
    total_director_rem = 0
    total_donation = 0

    for name, amt in pnl_rows:

        # Director remuneration
        if _match(name, DIRECTOR_KEYWORDS) and amt > 0:
            total_director_rem += amt

        # Rent — TDS 194I check
        if _match(name, RENT_KEYWORDS) and amt > 240000:
            total_rent += amt
            pnl_findings.append({
                'type': 'TDS',
                'ledger': name,
                'amount': amt,
                'message': f'Rent paid ₹{amt:,.0f} — TDS @10% under Sec 194I must be deducted',
                'severity': 'Critical',
                'law': 'Sec 194I IT Act — TDS on rent >₹2,40,000/year',
            })

        # Professional fees — TDS 194J check
        if _match(name, PROFESSIONAL_KEYWORDS) and amt > 50000:
            total_professional += amt
            pnl_findings.append({
                'type': 'TDS',
                'ledger': name,
                'amount': amt,
                'message': f'Professional fee ₹{amt:,.0f} — TDS @10% under Sec 194J must be deducted',
                'severity': 'Critical',
                'law': 'Sec 194J IT Act — TDS on professional/technical fees >₹50,000',
            })

        # Depreciation
        if _match(name, DEPRECIATION_KEYWORDS) and amt > 0:
            has_depreciation = True

        # Donations
        if _match(name, DONATION_KEYWORDS) and amt > 0:
            total_donation += amt
            pnl_findings.append({
                'type': 'COMPLIANCE',
                'ledger': name,
                'amount': amt,
                'message': f'Donation ₹{amt:,.0f} — verify 80G eligibility and CSR obligation',
                'severity': 'Review',
                'law': 'Sec 80G IT Act / Sec 135 Companies Act (CSR)',
            })

    # Director remuneration limit check
    if total_director_rem > DIRECTOR_REMUNERATION_LIMIT:
        pnl_findings.append({
            'type': 'COMPLIANCE',
            'ledger': 'Director Remuneration',
            'amount': total_director_rem,
            'message': f'Director remuneration ₹{total_director_rem:,.0f} — verify within Sec 197 limit (11% of net profit)',
            'severity': 'Review',
            'law': 'Sec 197 Companies Act 2013 — ceiling on managerial remuneration',
        })

    # No depreciation charged
    if not has_depreciation and pnl_rows:
        pnl_findings.append({
            'type': 'COMPLIANCE',
            'ledger': 'Depreciation',
            'amount': 0,
            'message': 'No depreciation found in P&L — verify if fixed assets exist and depreciation was charged',
            'severity': 'Review',
            'law': 'Sec 32 IT Act — depreciation mandatory on eligible assets',
        })

    return bs_findings, pnl_findings
