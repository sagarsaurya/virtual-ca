"""
pt_engine.py — Professional Tax analysis (West Bengal slabs)
Wraps the PT logic from audit_engine for a dedicated /api/pt-analysis endpoint.
"""
from audit_engine import parse_trial_balance, parse_daybook, audit_salary_compliance, calc_pt
import os


def run_pt_analysis(tb_path, db_path=None):
    ledgers, _, _ = parse_trial_balance(tb_path)

    daybook = None
    if db_path and os.path.exists(db_path):
        daybook = parse_daybook(db_path)

    findings = audit_salary_compliance(ledgers, daybook)

    # Summarise
    total_salary = next((f['total'] for f in findings if f['type'] == 'salary_summary'), 0)

    pt_shortfall   = 0
    pt_unpaid_govt = 0
    pt_deducted    = 0
    months_missing = []

    for f in findings:
        if f['type'] == 'pt_not_deducted':
            pt_shortfall   = f.get('total_shortfall', 0)
            months_missing = f.get('months', [])
        if f['type'] == 'pt_not_paid_govt':
            pt_unpaid_govt = f.get('amount', 0)
        if f['type'] in ('pt_deducted_ok', 'pt_paid_govt_ok'):
            pt_deducted = f.get('amount', 0)
        if f['type'] == 'pt_missing':
            pt_shortfall = f.get('est_annual_pt', 0)

    critical_count = sum(1 for f in findings if f.get('severity') == 'Critical')
    ok_count       = sum(1 for f in findings if f.get('severity') == 'Info')

    return {
        'findings':        findings,
        'total_salary':    total_salary,
        'pt_shortfall':    pt_shortfall,
        'pt_unpaid_govt':  pt_unpaid_govt,
        'pt_deducted':     pt_deducted,
        'months_missing':  months_missing,
        'critical_count':  critical_count,
        'ok_count':        ok_count,
        'wbslabs': [
            {'range': 'Up to ₹10,000/month',  'pt': '₹0'},
            {'range': '₹10,001–₹15,000/month','pt': '₹110'},
            {'range': '₹15,001–₹25,000/month','pt': '₹130'},
            {'range': '₹25,001–₹40,000/month','pt': '₹150'},
            {'range': 'Above ₹40,000/month',  'pt': '₹200'},
        ],
    }
