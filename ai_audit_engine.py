"""
ai_audit_engine.py — AI-powered audit using Groq (Llama 3.3-70B)

Strategy:
- Python handles: file parsing, cash violation check (objective rule), scoring
- AI handles: ledger classification, outstanding analysis, TDS applicability,
              loan questions, large expense review, anything needing CA judgment

Falls back to original audit_engine.run_full_audit() if AI call fails.
"""
import os
import json
import re
from datetime import datetime
from groq import Groq
from audit_engine import (
    parse_trial_balance, parse_daybook,
    audit_cash_violations, audit_bank_accounts,
    audit_salary_compliance, calc_pt
)


# ── BUILD COMPACT TEXT FOR AI ─────────────────────────────────────────────────

def _format_ledgers(ledgers):
    """Convert ledger list to compact text block for AI."""
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
    """Pull top cash payments and large expenses for AI context."""
    if daybook is None or daybook.empty:
        return "No daybook uploaded."

    lines = []
    # Top 30 largest debit entries
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


# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior Indian Chartered Accountant (CA) with 20+ years of experience in audit, tax, and compliance.

You will receive Trial Balance ledgers and Daybook entries from Tally. Your job is to find ALL accounting issues, mis-classifications, compliance violations, and red flags — like a real CA reviewing the books.

OUTPUT RULES (VERY IMPORTANT):
- Return ONLY valid JSON — no explanation, no markdown, no code blocks
- Use EXACTLY this JSON structure:

{
  "ledger_issues": [
    {
      "ledger": "ledger name",
      "current_group": "group in Tally",
      "correct_group": "what group it should be",
      "balance": 12345,
      "severity": "Critical",
      "issue": "short explanation of the problem",
      "fix": "Gateway → Accounts Info → Ledgers → Alter → [name] → Change Group to [correct]"
    }
  ],
  "outstanding_issues": [
    {
      "ledger": "ledger name",
      "balance": 12345,
      "severity": "Critical",
      "issue": "what is wrong or needs clarification",
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
      "issue": "TDS not deducted on professional fees above threshold"
    }
  ],
  "loan_issues": [
    {
      "ledger": "ledger name",
      "balance": 100000,
      "issue": "description",
      "question": "question to ask client"
    }
  ],
  "large_expense_issues": [
    {
      "party": "party name",
      "amount": 150000,
      "issue": "description",
      "question": "Is TDS applicable? Is this a business expense?"
    }
  ],
  "other_issues": [
    {
      "category": "ITR / Fixed Assets / Misc",
      "severity": "Critical",
      "issue": "description"
    }
  ]
}

WHAT TO LOOK FOR:

Ledger Classification (most common errors):
- TDS Receivable/Refund → must be Current Assets (not Duties & Taxes)
- TDS Payable/TDS on X → must be Duties & Taxes
- GST Input Credit → must be Current Assets
- GST Output → must be Duties & Taxes
- Bank Interest Received → must be Indirect Incomes (not Indirect Expenses)
- Credit Card outstanding → must be Sundry Creditors (not Expenses)
- Drawings → must be Capital Account (not Expenses)
- Prepaid Expenses → must be Current Assets
- Security Deposit → must be Loans & Advances (Asset)
- Customer Advance/Advance from Customer → must be Current Liabilities
- PT Payable → must be Duties & Taxes
- Salary Payable → must be Current Liabilities
- Income Tax / Advance Tax → must be Duties & Taxes
- Any ledger with credit balance under Bank Accounts → likely income, mis-grouped

Outstanding Balances:
- Suspense account with non-zero balance → Critical
- Debtors with credit balance → reverse entry needed
- Creditors with debit balance → advance paid, needs confirmation
- Opening balance difference → serious, affects audit trail

TDS (check from daybook large expenses):
- Professional fees/consultant > ₹50,000 → Sec 194J @ 10%
- Contractor/transport > ₹30,000 single or ₹1,00,000 annual → Sec 194C @ 2%
- Rent > ₹2,40,000/year → Sec 194I @ 10%
- Commission > ₹15,000 → Sec 194H @ 5%
- Interest on loan > ₹40,000 → Sec 194A @ 10%

Loans:
- Director loans without interest → CBDT scrutiny risk
- Cash loans > ₹20,000 → Sec 269SS violation
- Unsecured loans from related parties → need confirmation and interest calculation

Be thorough. A real CA would flag EVERYTHING suspicious, not just obvious errors.
Do not invent ledger names not present in the data. Only flag what you actually see.
"""


# ── CALL AI ───────────────────────────────────────────────────────────────────

def _call_groq(ledger_text, daybook_text, company, period):
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    client = Groq(api_key=api_key)

    user_message = f"""Company: {company}
Period: {period}

TRIAL BALANCE LEDGERS:
{ledger_text}

TOP DAYBOOK ENTRIES (largest payments):
{daybook_text}

Analyse all the above and return ONLY the JSON with all issues found."""

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        max_tokens=4096,
        temperature=0.1,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user',   'content': user_message},
        ]
    )
    return response.choices[0].message.content


def _parse_ai_response(raw):
    """Extract JSON from AI response — strips any markdown if present."""
    # Remove ```json ... ``` or ``` ... ``` wrappers
    text = re.sub(r'```(?:json)?', '', raw).strip().rstrip('`').strip()
    # Find first { to last }
    start = text.find('{')
    end   = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in AI response")
    return json.loads(text[start:end+1])


# ── MAP AI OUTPUT → FRONTEND FORMAT ──────────────────────────────────────────

def _map_to_frontend(ai, cash_violations, bank_accounts, salary_compliance, ledgers):
    """Convert AI JSON output + Python rule results → format expected by frontend."""

    # Ledger classification
    ledger_classification = []
    for item in ai.get('ledger_issues', []):
        ledger_classification.append({
            'severity':      item.get('severity', 'Review'),
            'ledger':        item.get('ledger', ''),
            'current_group': item.get('current_group', ''),
            'correct_group': item.get('correct_group', ''),
            'balance':       item.get('balance', 0),
            'rule':          item.get('issue', ''),
            'fix':           item.get('fix', ''),
            'issue':         item.get('issue', ''),
        })

    # Outstanding
    outstanding = []
    for item in ai.get('outstanding_issues', []):
        outstanding.append({
            'severity': item.get('severity', 'Review'),
            'ledger':   item.get('ledger', ''),
            'balance':  item.get('balance', 0),
            'issue':    item.get('issue', ''),
            'question': item.get('question', ''),
        })

    # TDS compliance
    tds_compliance = []
    for item in ai.get('tds_issues', []):
        tds_compliance.append({
            'severity':     'Critical',
            'party':        item.get('party', ''),
            'total_paid':   item.get('total_paid', 0),
            'section':      item.get('section', ''),
            'rate':         item.get('rate', 0),
            'tds_expected': item.get('tds_due', 0),
            'issue':        item.get('issue', ''),
        })

    # Loans
    loans = []
    for item in ai.get('loan_issues', []):
        loans.append({
            'ledger':   item.get('ledger', ''),
            'balance':  item.get('balance', 0),
            'note':     item.get('issue', ''),
            'question': item.get('question', ''),
        })

    # Large expenses
    large_expenses = []
    for item in ai.get('large_expense_issues', []):
        large_expenses.append({
            'party':        item.get('party', ''),
            'amount':       item.get('amount', 0),
            'voucher_type': 'Payment',
            'question':     item.get('question', item.get('issue', '')),
        })

    # Other issues → itr list
    itr = []
    for item in ai.get('other_issues', []):
        itr.append({
            'severity': item.get('severity', 'Review'),
            'issue':    item.get('issue', ''),
            'category': item.get('category', 'Other'),
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
    critical = (
        sum(1 for f in results['ledger_classification'] if f.get('severity') == 'Critical') +
        sum(1 for f in results['outstanding']           if f.get('severity') == 'Critical')
    )
    warnings = (
        sum(1 for f in results['ledger_classification'] if f.get('severity') == 'Review') +
        sum(1 for f in results['outstanding']           if f.get('severity') == 'Review') +
        len(results['cash_violations'])
    )
    tds_issues    = len(results['tds_compliance'])
    salary_issues = sum(1 for s in results['salary_compliance'] if s.get('severity') in ('Critical','Important'))
    questions     = len(results['loans']) + len(results['large_expenses']) + len(results['bank_accounts'])
    cash_penalty  = min(20, len(results['cash_violations']))
    return max(0, 100 - critical*8 - warnings*1 - questions*2 - tds_issues*6 - salary_issues*3 - cash_penalty)


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def run_ai_audit(tb_path, db_path=None):
    """
    AI-powered audit. Returns same JSON structure as audit_engine.run_full_audit()
    so the frontend needs zero changes.
    Falls back to original engine if AI fails.
    """
    import pandas as pd

    print("AI Audit: Parsing files...")
    ledgers, company_name, period_str = parse_trial_balance(tb_path)
    daybook = parse_daybook(db_path) if db_path else pd.DataFrame(
        columns=['Date','Particulars','VchType','VchNo','Debit','Credit'])
    print(f"  Company: {company_name} | Ledgers: {len(ledgers)} | Vouchers: {len(daybook)}")

    # Python rule-based checks (objective, no AI needed)
    print("AI Audit: Running rule-based checks (cash, bank, salary)...")
    cash_violations  = audit_cash_violations(daybook)
    txn_list         = daybook.to_dict('records') if not daybook.empty else []
    bank_result      = audit_bank_accounts(ledgers, txn_list)
    bank_accounts    = [b for b in bank_result if '_misclassified_as_bank' not in b]
    salary_compliance = audit_salary_compliance(ledgers, daybook if not daybook.empty else None)

    # Build AI input
    ledger_text  = _format_ledgers(ledgers)
    daybook_text = _format_daybook_summary(daybook)

    print("AI Audit: Calling Groq AI for analysis...")
    try:
        raw      = _call_groq(ledger_text, daybook_text, company_name or 'Company', period_str or 'FY 2025-26')
        ai_data  = _parse_ai_response(raw)
        print(f"  AI found: {len(ai_data.get('ledger_issues',[]))} ledger issues, "
              f"{len(ai_data.get('tds_issues',[]))} TDS issues, "
              f"{len(ai_data.get('loan_issues',[]))} loan issues")
    except Exception as e:
        print(f"  AI call failed: {e} — falling back to rule-based engine")
        from audit_engine import run_full_audit
        return run_full_audit(tb_path, db_path)

    results = _map_to_frontend(ai_data, cash_violations, bank_accounts, salary_compliance, ledgers)
    score   = _score(results)

    critical  = sum(1 for f in results['ledger_classification'] if f.get('severity') == 'Critical') + \
                sum(1 for f in results['outstanding']           if f.get('severity') == 'Critical')
    warnings  = sum(1 for f in results['ledger_classification'] if f.get('severity') == 'Review') + \
                sum(1 for f in results['outstanding']           if f.get('severity') == 'Review') + \
                len(results['cash_violations'])
    questions = len(results['loans']) + len(results['large_expenses']) + len(results['bank_accounts'])

    module_status = {
        'ledger_classification': {'count': len(results['ledger_classification']), 'ok_msg': f'All {len(ledgers)} ledgers reviewed by AI — no mis-classification found.'},
        'cash_violations':       {'count': len(cash_violations),  'ok_msg': 'No cash violations found.'},
        'tds_compliance':        {'count': len(results['tds_compliance']), 'ok_msg': 'No TDS issues detected by AI.'},
        'outstanding':           {'count': len(results['outstanding']), 'ok_msg': 'No abnormal balances found.'},
        'large_expenses':        {'count': len(results['large_expenses']), 'ok_msg': 'No large expenses flagged.'},
        'loans':                 {'count': len(results['loans']), 'ok_msg': 'No loan issues found.'},
        'itr':                   {'count': len(results['itr']), 'ok_msg': 'No personal or ITR-related issues found.'},
        'salary_compliance':     {'count': len(results['salary_compliance']), 'ok_msg': 'No salary/PF/PT issues found.'},
        'bank_accounts':         {'count': len(bank_accounts), 'ok_msg': 'No bank accounts detected.'},
        'fixed_assets':          {'count': 0, 'ok_msg': 'No fixed asset issues found.'},
    }

    results['module_status'] = module_status
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
        'engine':         'AI (Groq Llama 3.3-70B)',
    }

    return results
