import pandas as pd
import json
from datetime import datetime

# GST rate slabs
GST_RATES = [0, 5, 12, 18, 28]

# Keywords to identify sales ledgers
SALES_KEYWORDS = ['sales', 'revenue', 'turnover', 'service income', 'income from services',
                  'export sales', 'domestic sales', 'gst sales']
PURCHASE_KEYWORDS = ['purchase', 'purchases', 'cost of goods', 'raw material']

# Tax ledger keywords
CGST_KW  = ['cgst', 'central gst', 'central tax']
SGST_KW  = ['sgst', 'utgst', 'state gst', 'state tax']
IGST_KW  = ['igst', 'integrated gst', 'integrated tax']

def _detect_rate(ledger_name):
    n = ledger_name.lower()
    for r in [28, 18, 12, 5]:
        if f'{r}%' in n or f'@{r}' in n or f'@ {r}' in n or f'gst{r}' in n:
            return r
    if 'exempt' in n or 'nil' in n or '0%' in n:
        return 0
    return 18  # default

def _is_inter_state(party_name):
    # Simple heuristic — if party name contains state-suggesting keywords
    # In real implementation CA would maintain a GSTIN → state mapping
    # For now flag as intra-state (CGST+SGST) by default
    return False

def parse_gst_data(tb_path, daybook_path=None):
    from audit_engine import parse_trial_balance
    ledgers = parse_trial_balance(tb_path)

    sales_entries   = []
    purchase_entries = []
    tax_collected    = {'cgst': 0, 'sgst': 0, 'igst': 0}
    tax_paid         = {'cgst': 0, 'sgst': 0, 'igst': 0}
    missing_gstin    = []
    b2b_total = 0
    b2c_total = 0

    for l in ledgers:
        name  = l.get('ledger') or ''
        group = (l.get('group') or '').lower()
        bal   = abs(float(l.get('closing_balance') or l.get('balance') or 0))
        n     = name.lower()

        # Tax ledgers
        if any(kw in n for kw in CGST_KW):
            if 'input' in n or 'receivable' in n or 'itc' in n:
                tax_paid['cgst'] += bal
            else:
                tax_collected['cgst'] += bal
            continue
        if any(kw in n for kw in SGST_KW):
            if 'input' in n or 'receivable' in n or 'itc' in n:
                tax_paid['sgst'] += bal
            else:
                tax_collected['sgst'] += bal
            continue
        if any(kw in n for kw in IGST_KW):
            if 'input' in n or 'receivable' in n or 'itc' in n:
                tax_paid['igst'] += bal
            else:
                tax_collected['igst'] += bal
            continue

        # Sales ledgers
        if any(kw in n for kw in SALES_KEYWORDS) or 'income' in group:
            if bal < 100:
                continue
            rate = _detect_rate(name)
            taxable = round(bal / (1 + rate/100), 2) if rate > 0 else bal
            tax_amt = round(taxable * rate / 100, 2)
            inter = _is_inter_state(name)
            entry = {
                'ledger': name,
                'taxable_value': round(taxable, 0),
                'rate': rate,
                'igst': tax_amt if inter else 0,
                'cgst': round(tax_amt/2, 0) if not inter else 0,
                'sgst': round(tax_amt/2, 0) if not inter else 0,
                'type': 'b2b',
                'gstin': '',
                'has_gstin': False,
            }
            sales_entries.append(entry)
            if entry['has_gstin']:
                b2b_total += taxable
            else:
                b2c_total += taxable
                missing_gstin.append(name)

        # Purchase ledgers
        elif any(kw in n for kw in PURCHASE_KEYWORDS) or 'purchase' in group:
            if bal < 100:
                continue
            rate = _detect_rate(name)
            taxable = round(bal / (1 + rate/100), 2) if rate > 0 else bal
            purchase_entries.append({
                'ledger': name,
                'taxable_value': round(taxable, 0),
                'rate': rate,
                'itc_eligible': True,
            })

    total_tax_collected = tax_collected['cgst'] + tax_collected['sgst'] + tax_collected['igst']
    total_itc           = tax_paid['cgst'] + tax_paid['sgst'] + tax_paid['igst']
    net_gst_payable     = round(total_tax_collected - total_itc, 0)

    # GSTR-1 structure
    gstr1 = {
        'b2b': [e for e in sales_entries if e['has_gstin']],
        'b2c': [e for e in sales_entries if not e['has_gstin']],
        'total_taxable': round(sum(e['taxable_value'] for e in sales_entries), 0),
        'total_igst': round(sum(e['igst'] for e in sales_entries), 0),
        'total_cgst': round(sum(e['cgst'] for e in sales_entries), 0),
        'total_sgst': round(sum(e['sgst'] for e in sales_entries), 0),
    }

    # GSTR-3B structure
    gstr3b = {
        'outward_taxable': round(sum(e['taxable_value'] for e in sales_entries), 0),
        'outward_tax': round(total_tax_collected, 0),
        'itc_available': round(total_itc, 0),
        'net_payable': max(0, net_gst_payable),
        'cgst_payable': max(0, round(tax_collected['cgst'] - tax_paid['cgst'], 0)),
        'sgst_payable': max(0, round(tax_collected['sgst'] - tax_paid['sgst'], 0)),
        'igst_payable': max(0, round(tax_collected['igst'] - tax_paid['igst'], 0)),
    }

    return {
        'sales_entries': sales_entries,
        'purchase_entries': purchase_entries,
        'tax_collected': {k: round(v, 0) for k, v in tax_collected.items()},
        'tax_paid': {k: round(v, 0) for k, v in tax_paid.items()},
        'net_gst_payable': max(0, net_gst_payable),
        'missing_gstin': missing_gstin,
        'b2b_count': len([e for e in sales_entries if e['has_gstin']]),
        'b2c_count': len([e for e in sales_entries if not e['has_gstin']]),
        'gstr1': gstr1,
        'gstr3b': gstr3b,
        'total_sales_entries': len(sales_entries),
        'total_purchase_entries': len(purchase_entries),
    }
