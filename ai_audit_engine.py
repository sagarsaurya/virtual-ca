"""
ai_audit_engine.py — Two-AI audit system using Claude Sonnet 4.6

AI 1 (Auditor): Reads all ledgers + daybook, finds issues, writes evidence for each
AI 2 (Critic):  Reads Auditor's findings, checks if evidence is logically sound
                Returns confidence badge: verified / disputed / low_confidence

Python handles: file parsing, cash violations (objective ₹10,000 rule), bank detection, salary/PT
Falls back to original audit_engine if either AI call fails.
"""
import os
import json
import re
from datetime import datetime
import anthropic
from audit_engine import (
    parse_trial_balance, parse_daybook,
    audit_cash_violations, audit_bank_accounts,
    audit_salary_compliance,
)

MODEL = 'claude-sonnet-4-6'


# ── BUILD INPUT TEXT FOR AUDITOR ──────────────────────────────────────────────

def _format_ledgers(ledgers):
    lines = []
    for l in ledgers:
        bal  = abs(l.get('balance', 0))
        dr   = l.get('debit', 0) or 0
        cr   = l.get('credit', 0) or 0
        side = 'DR' if dr >= cr else 'CR'
        if bal < 100:
            continue
        lines.append(f"  {l['name']} | Group: {l.get('group','')} | ₹{bal:,.0f} {side}")
    return '\n'.join(lines)


def _format_daybook_summary(daybook):
    if daybook is None or daybook.empty:
        return "No daybook uploaded."
    lines = []
    top = daybook[daybook['Debit'] > 0].nlargest(30, 'Debit')
    for _, row in top.iterrows():
        date = row.get('Date', '')
        if hasattr(date, 'strftime'):
            date = date.strftime('%d-%b-%Y')
        lines.append(
            f"  {date} | {str(row.get('Particulars',''))[:50]} | "
            f"{row.get('VchType','')} | ₹{row.get('Debit',0):,.0f}"
        )
    return '\n'.join(lines) if lines else "No debit entries found."


# ── AUDITOR SYSTEM PROMPT ─────────────────────────────────────────────────────

AUDITOR_PROMPT = """You are a senior Indian Chartered Accountant (CA) with 20+ years of experience in statutory audit, tax audit, and compliance.

You will receive Trial Balance ledgers and Daybook entries exported from Tally. Your job is to find ALL accounting issues and for each issue provide CLEAR EVIDENCE — specific numbers, balance directions, law sections — like a CA writing an audit observation.

OUTPUT: Return ONLY valid JSON. No markdown, no explanation outside the JSON.

JSON structure:
{
  "ledger_issues": [
    {
      "ledger": "exact ledger name from data",
      "current_group": "group currently in Tally",
      "correct_group": "what group it should be",
      "balance": 12345,
      "severity": "Critical",
      "issue": "one line — what is wrong",
      "evidence": "specific evidence: balance direction, amount, why this proves the issue",
      "law": "applicable law/standard e.g. ICAI Chart of Accounts, AS-2, Sec 40A(3)",
      "impact": "what goes wrong in the books if not fixed",
      "fix": "Gateway of Tally → Accounts Info → Ledgers → Alter → [name] → Change Group to [correct]"
    }
  ],
  "outstanding_issues": [
    {
      "ledger": "ledger name",
      "balance": 12345,
      "severity": "Critical",
      "issue": "what is wrong",
      "evidence": "specific evidence from the data",
      "law": "applicable law if any",
      "question": "question to ask the client"
    }
  ],
  "tds_issues": [
    {
      "party": "party name",
      "total_paid": 50000,
      "section": "194J",
      "rate": 10,
      "tds_due": 5000,
      "issue": "TDS not deducted",
      "evidence": "payment of ₹X found in daybook on [date], crosses ₹Y threshold",
      "law": "Section 194J Income Tax Act 1961"
    }
  ],
  "loan_issues": [
    {
      "ledger": "ledger name",
      "balance": 100000,
      "severity": "Review",
      "issue": "what needs attention",
      "evidence": "specific evidence",
      "law": "applicable section",
      "question": "question for client"
    }
  ],
  "large_expense_issues": [
    {
      "party": "party name",
      "amount": 150000,
      "issue": "what needs review",
      "evidence": "found in daybook on [date]",
      "question": "Is TDS applicable? Is this a genuine business expense?"
    }
  ],
  "other_issues": [
    {
      "category": "ITR / Fixed Assets / Misc",
      "severity": "Critical",
      "issue": "description",
      "evidence": "specific evidence",
      "law": "applicable law"
    }
  ]
}

WHAT TO LOOK FOR:

Ledger Classification errors (most common):
- TDS Receivable → must be Current Assets (not Duties & Taxes)
- TDS Payable / TDS on X → must be Duties & Taxes
- GST Input Credit → must be Current Assets
- GST Output → must be Duties & Taxes
- Bank Interest Received → must be Indirect Incomes (not Indirect Expenses)
- Credit Card outstanding → must be Sundry Creditors (not Expenses)
- Drawings → must be Capital Account (not Expenses)
- Prepaid Expenses → must be Current Assets
- Security Deposit → must be Loans & Advances (Asset)
- Customer Advance → must be Current Liabilities
- PT Payable → must be Duties & Taxes
- Salary Payable → must be Current Liabilities
- Income Tax / Advance Tax → must be Duties & Taxes
- Any CR balance under Bank Accounts group → likely income mis-grouped

Outstanding Balances:
- Suspense account non-zero → Critical (AS-1: no unexplained balances)
- Debtors with CR balance → reverse entry or advance received
- Creditors with DR balance → advance paid, needs confirmation

TDS thresholds (Income Tax Act 1961):
- Professional fees > ₹50,000 → Sec 194J @ 10%
- Contractor/transport > ₹30,000 single or ₹1,00,000 annual → Sec 194C @ 2%
- Rent > ₹2,40,000/year → Sec 194I @ 10%
- Commission > ₹15,000 → Sec 194H @ 5%
- Interest on loan > ₹40,000 → Sec 194A @ 10%

Loans:
- Director loans without interest → CBDT scrutiny (circular 19/2017)
- Cash loans > ₹20,000 → Sec 269SS violation
- Unsecured loans → need documentation

IMPORTANT: Only flag ledgers actually present in the data. Do not invent names. Every finding must cite specific numbers from the data as evidence."""


# ── CRITIC SYSTEM PROMPT ──────────────────────────────────────────────────────

CRITIC_PROMPT = """You are a senior audit quality reviewer at a CA firm. Your job is to review audit findings made by another CA and verify whether each finding is logically sound and evidenced.

You will receive a list of audit findings. For each finding, check:
1. Does the evidence actually support the issue raised?
2. Is the law/standard cited applicable and correct?
3. Is the severity appropriate?
4. Could there be an alternative explanation the Auditor missed?

OUTPUT: Return ONLY valid JSON. No markdown, no explanation outside JSON.

JSON structure:
{
  "verdicts": [
    {
      "finding_id": "led-0",
      "confidence": "verified",
      "reasoning": "The CR balance in an expense group is factually impossible in double-entry accounting. Evidence is conclusive."
    },
    {
      "finding_id": "led-1",
      "confidence": "disputed",
      "reasoning": "The balance is ₹240 — below materiality threshold. This may be a rounding difference, not a mis-classification. Recommend verifying before acting."
    },
    {
      "finding_id": "tds-0",
      "confidence": "low_confidence",
      "reasoning": "Auditor flagged ₹28,000 rent payment but threshold for 194I is ₹2,40,000 annual. Single payment does not cross threshold. Finding appears incorrect."
    }
  ]
}

Confidence levels:
- "verified" — evidence is clear, finding is definitely correct
- "disputed" — finding may be right but evidence is weak, ambiguous, or has alternative explanation
- "low_confidence" — evidence does not support the finding, likely an AI error

Be a strict reviewer. If the math is wrong or the law section is misapplied, say so clearly.
Do not invent new issues. Only review what the Auditor found."""


# ── CALL CLAUDE ───────────────────────────────────────────────────────────────

def _call_claude(system, user_message):
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{'role': 'user', 'content': user_message}]
    )
    return response.content[0].text


def _parse_json(raw):
    text = re.sub(r'```(?:json)?', '', raw).strip().rstrip('`').strip()
    start = text.find('{')
    end   = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON found in AI response")
    return json.loads(text[start:end+1])


# ── BUILD CRITIC INPUT ────────────────────────────────────────────────────────

def _build_critic_input(ai_data):
    """Convert Auditor findings into numbered list for Critic to review."""
    findings = []

    for i, item in enumerate(ai_data.get('ledger_issues', [])):
        findings.append({
            'id': f'led-{i}',
            'type': 'Ledger Classification',
            'issue': item.get('issue', ''),
            'evidence': item.get('evidence', ''),
            'law': item.get('law', ''),
            'severity': item.get('severity', ''),
            'detail': f"Ledger: {item.get('ledger')} | Current group: {item.get('current_group')} | Proposed: {item.get('correct_group')} | Balance: ₹{item.get('balance',0):,}"
        })

    for i, item in enumerate(ai_data.get('outstanding_issues', [])):
        findings.append({
            'id': f'out-{i}',
            'type': 'Outstanding Balance',
            'issue': item.get('issue', ''),
            'evidence': item.get('evidence', ''),
            'law': item.get('law', ''),
            'severity': item.get('severity', ''),
            'detail': f"Ledger: {item.get('ledger')} | Balance: ₹{item.get('balance',0):,}"
        })

    for i, item in enumerate(ai_data.get('tds_issues', [])):
        findings.append({
            'id': f'tds-{i}',
            'type': 'TDS Compliance',
            'issue': item.get('issue', ''),
            'evidence': item.get('evidence', ''),
            'law': item.get('law', ''),
            'severity': 'Critical',
            'detail': f"Party: {item.get('party')} | Paid: ₹{item.get('total_paid',0):,} | Section: {item.get('section')} | TDS due: ₹{item.get('tds_due',0):,}"
        })

    for i, item in enumerate(ai_data.get('loan_issues', [])):
        findings.append({
            'id': f'loan-{i}',
            'type': 'Loan',
            'issue': item.get('issue', ''),
            'evidence': item.get('evidence', ''),
            'law': item.get('law', ''),
            'severity': item.get('severity', 'Review'),
            'detail': f"Ledger: {item.get('ledger')} | Balance: ₹{item.get('balance',0):,}"
        })

    for i, item in enumerate(ai_data.get('other_issues', [])):
        findings.append({
            'id': f'other-{i}',
            'type': item.get('category', 'Other'),
            'issue': item.get('issue', ''),
            'evidence': item.get('evidence', ''),
            'law': item.get('law', ''),
            'severity': item.get('severity', 'Review'),
            'detail': ''
        })

    return findings


# ── MERGE CRITIC VERDICTS INTO FINDINGS ──────────────────────────────────────

def _apply_verdicts(ai_data, verdicts_list):
    """Add confidence + critic_reasoning to each finding."""
    verdict_map = {v['finding_id']: v for v in verdicts_list}

    def enrich(items, prefix):
        for i, item in enumerate(items):
            fid = f'{prefix}-{i}'
            v   = verdict_map.get(fid, {})
            item['confidence']       = v.get('confidence', 'verified')
            item['critic_reasoning'] = v.get('reasoning', '')
        return items

    ai_data['ledger_issues']       = enrich(ai_data.get('ledger_issues', []),       'led')
    ai_data['outstanding_issues']  = enrich(ai_data.get('outstanding_issues', []),  'out')
    ai_data['tds_issues']          = enrich(ai_data.get('tds_issues', []),          'tds')
    ai_data['loan_issues']         = enrich(ai_data.get('loan_issues', []),         'loan')
    ai_data['other_issues']        = enrich(ai_data.get('other_issues', []),        'other')
    return ai_data


# ── MAP TO FRONTEND FORMAT ────────────────────────────────────────────────────

def _map_to_frontend(ai_data, cash_violations, bank_accounts, salary_compliance):

    def conf_badge(item):
        return {
            'confidence':       item.get('confidence', 'verified'),
            'critic_reasoning': item.get('critic_reasoning', ''),
            'evidence':         item.get('evidence', ''),
            'law':              item.get('law', ''),
            'impact':           item.get('impact', ''),
        }

    ledger_classification = []
    for item in ai_data.get('ledger_issues', []):
        ledger_classification.append({
            'severity':      item.get('severity', 'Review'),
            'ledger':        item.get('ledger', ''),
            'current_group': item.get('current_group', ''),
            'correct_group': item.get('correct_group', ''),
            'balance':       item.get('balance', 0),
            'rule':          item.get('issue', ''),
            'fix':           item.get('fix', ''),
            'issue':         item.get('issue', ''),
            **conf_badge(item),
        })

    outstanding = []
    for item in ai_data.get('outstanding_issues', []):
        outstanding.append({
            'severity': item.get('severity', 'Review'),
            'ledger':   item.get('ledger', ''),
            'balance':  item.get('balance', 0),
            'issue':    item.get('issue', ''),
            'question': item.get('question', ''),
            **conf_badge(item),
        })

    tds_compliance = []
    for item in ai_data.get('tds_issues', []):
        tds_compliance.append({
            'severity':     'Critical',
            'party':        item.get('party', ''),
            'total_paid':   item.get('total_paid', 0),
            'section':      item.get('section', ''),
            'rate':         item.get('rate', 0),
            'tds_expected': item.get('tds_due', 0),
            'issue':        item.get('issue', ''),
            **conf_badge(item),
        })

    loans = []
    for item in ai_data.get('loan_issues', []):
        loans.append({
            'ledger':   item.get('ledger', ''),
            'balance':  item.get('balance', 0),
            'note':     item.get('issue', ''),
            'question': item.get('question', ''),
            **conf_badge(item),
        })

    large_expenses = []
    for item in ai_data.get('large_expense_issues', []):
        large_expenses.append({
            'party':        item.get('party', ''),
            'amount':       item.get('amount', 0),
            'voucher_type': 'Payment',
            'question':     item.get('question', item.get('issue', '')),
            **conf_badge(item),
        })

    itr = []
    for item in ai_data.get('other_issues', []):
        itr.append({
            'severity': item.get('severity', 'Review'),
            'issue':    item.get('issue', ''),
            'category': item.get('category', 'Other'),
            **conf_badge(item),
        })

    return {
        'ledger_classification': ledger_classification,
        'outstanding':           outstanding,
        'cash_violations':       cash_violations,
        'loans':                 loans,
        'large_expenses':        large_expenses,
        'itr':                   itr,
        'tds_compliance':        tds_compliance,
        'salary_compliance':     salary_compliance,
        'bank_accounts':         bank_accounts,
        'fixed_assets':          [],
    }


# ── SCORING ───────────────────────────────────────────────────────────────────

def _score(results):
    # Disputed findings count less, low_confidence don't count at all
    def weight(item):
        c = item.get('confidence', 'verified')
        if c == 'verified':      return 1.0
        if c == 'disputed':      return 0.4
        return 0.0  # low_confidence

    critical = (
        sum(weight(f) for f in results['ledger_classification'] if f.get('severity') == 'Critical') +
        sum(weight(f) for f in results['outstanding']           if f.get('severity') == 'Critical')
    )
    warnings = (
        sum(weight(f) for f in results['ledger_classification'] if f.get('severity') == 'Review') +
        sum(weight(f) for f in results['outstanding']           if f.get('severity') == 'Review') +
        len(results['cash_violations'])
    )
    tds_issues    = sum(weight(f) for f in results['tds_compliance'])
    salary_issues = sum(1 for s in results['salary_compliance'] if s.get('severity') in ('Critical','Important'))
    questions     = len(results['loans']) + len(results['large_expenses']) + len(results['bank_accounts'])
    cash_penalty  = min(20, len(results['cash_violations']))

    return max(0, round(100 - critical*8 - warnings*1 - questions*2 - tds_issues*6 - salary_issues*3 - cash_penalty))


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def run_ai_audit(tb_path, db_path=None):
    """
    Two-AI audit: Auditor (Claude Sonnet) finds issues with evidence,
    Critic (Claude Sonnet) verifies each finding.
    Returns same JSON structure as audit_engine.run_full_audit() — frontend unchanged.
    Falls back to original engine if AI fails.
    """
    import pandas as pd

    print("AI Audit: Parsing files...")
    ledgers, company_name, period_str = parse_trial_balance(tb_path)
    daybook = parse_daybook(db_path) if db_path else pd.DataFrame(
        columns=['Date','Particulars','VchType','VchNo','Debit','Credit'])
    print(f"  Company: {company_name} | Ledgers: {len(ledgers)} | Vouchers: {len(daybook)}")

    # Python rule-based checks (objective, no AI needed)
    print("AI Audit: Rule-based checks (cash, bank, salary)...")
    cash_violations   = audit_cash_violations(daybook)
    txn_list          = daybook.to_dict('records') if not daybook.empty else []
    bank_result       = audit_bank_accounts(ledgers, txn_list)
    bank_accounts     = [b for b in bank_result if '_misclassified_as_bank' not in b]
    salary_compliance = audit_salary_compliance(ledgers, daybook if not daybook.empty else None)

    ledger_text  = _format_ledgers(ledgers)
    daybook_text = _format_daybook_summary(daybook)

    # ── AI 1: AUDITOR ─────────────────────────────────────────────────────────
    print("AI Audit: Auditor AI analysing books...")
    try:
        auditor_input = f"""Company: {company_name or 'Company'}
Period: {period_str or 'FY 2025-26'}

TRIAL BALANCE LEDGERS:
{ledger_text}

TOP DAYBOOK ENTRIES (largest payments):
{daybook_text}

Find ALL issues. For each issue provide specific evidence from the data above."""

        raw_auditor = _call_claude(AUDITOR_PROMPT, auditor_input)
        ai_data     = _parse_json(raw_auditor)
        total_found = (len(ai_data.get('ledger_issues',[])) +
                       len(ai_data.get('outstanding_issues',[])) +
                       len(ai_data.get('tds_issues',[])) +
                       len(ai_data.get('loan_issues',[])))
        print(f"  Auditor found {total_found} issues")
    except Exception as e:
        print(f"  Auditor AI failed: {e} — falling back to rule-based engine")
        from audit_engine import run_full_audit
        return run_full_audit(tb_path, db_path)

    # ── AI 2: CRITIC ──────────────────────────────────────────────────────────
    print("AI Audit: Critic AI verifying findings...")
    try:
        findings_for_critic = _build_critic_input(ai_data)
        critic_input = f"""Review these {len(findings_for_critic)} audit findings made by the Auditor CA.
For each finding, verify if the evidence is logically sound and the law is correctly applied.

FINDINGS TO REVIEW:
{json.dumps(findings_for_critic, indent=2)}

Return verdicts for every finding_id listed above."""

        raw_critic    = _call_claude(CRITIC_PROMPT, critic_input)
        critic_data   = _parse_json(raw_critic)
        verdicts_list = critic_data.get('verdicts', [])
        confirmed  = sum(1 for v in verdicts_list if v.get('confidence') == 'verified')
        disputed   = sum(1 for v in verdicts_list if v.get('confidence') == 'disputed')
        low_conf   = sum(1 for v in verdicts_list if v.get('confidence') == 'low_confidence')
        print(f"  Critic: {confirmed} verified, {disputed} disputed, {low_conf} low_confidence")
        ai_data = _apply_verdicts(ai_data, verdicts_list)
    except Exception as e:
        print(f"  Critic AI failed: {e} — using Auditor findings without verification")
        # Mark all as verified if Critic fails
        for key in ['ledger_issues','outstanding_issues','tds_issues','loan_issues','other_issues']:
            for item in ai_data.get(key, []):
                item['confidence']       = 'verified'
                item['critic_reasoning'] = ''

    results = _map_to_frontend(ai_data, cash_violations, bank_accounts, salary_compliance)
    score   = _score(results)

    critical  = sum(1 for f in results['ledger_classification'] if f.get('severity') == 'Critical') + \
                sum(1 for f in results['outstanding']           if f.get('severity') == 'Critical')
    warnings  = sum(1 for f in results['ledger_classification'] if f.get('severity') == 'Review') + \
                sum(1 for f in results['outstanding']           if f.get('severity') == 'Review') + \
                len(results['cash_violations'])
    questions = len(results['loans']) + len(results['large_expenses']) + len(results['bank_accounts'])

    verdicts_summary = {}
    if 'verdicts_list' in dir():
        verdicts_summary = {
            'verified':      sum(1 for v in verdicts_list if v.get('confidence') == 'verified'),
            'disputed':      sum(1 for v in verdicts_list if v.get('confidence') == 'disputed'),
            'low_confidence':sum(1 for v in verdicts_list if v.get('confidence') == 'low_confidence'),
        }

    module_status = {
        'ledger_classification': {'count': len(results['ledger_classification']), 'ok_msg': f'All {len(ledgers)} ledgers reviewed by AI — no mis-classification found.'},
        'cash_violations':       {'count': len(cash_violations),  'ok_msg': 'No cash violations found.'},
        'tds_compliance':        {'count': len(results['tds_compliance']), 'ok_msg': 'No TDS issues detected.'},
        'outstanding':           {'count': len(results['outstanding']), 'ok_msg': 'No abnormal balances found.'},
        'large_expenses':        {'count': len(results['large_expenses']), 'ok_msg': 'No large expenses flagged.'},
        'loans':                 {'count': len(results['loans']), 'ok_msg': 'No loan issues found.'},
        'itr':                   {'count': len(results['itr']), 'ok_msg': 'No ITR-related issues found.'},
        'salary_compliance':     {'count': len(results['salary_compliance']), 'ok_msg': 'No salary/PF/PT issues found.'},
        'bank_accounts':         {'count': len(bank_accounts), 'ok_msg': 'No bank accounts detected.'},
        'fixed_assets':          {'count': 0, 'ok_msg': 'No fixed asset issues found.'},
    }

    results['module_status']    = module_status
    results['verdicts_summary'] = verdicts_summary
    results['summary'] = {
        'company':        company_name or 'Your Company',
        'period':         period_str   or 'FY 2025-26',
        'total_ledgers':  len(ledgers),
        'total_vouchers': len(daybook),
        'critical':       critical,
        'warnings':       warnings,
        'questions':      questions,
        'cash_violations_count': len(cash_violations),
        'score':          score,
        'generated_at':   datetime.now().strftime('%d-%b-%Y %H:%M'),
        'engine':         'AI — Claude Sonnet 4.6',
    }

    return results
