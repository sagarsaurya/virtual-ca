"""
ca_agent.py — VirtualCA's Ask Your CA powered by Claude Haiku 4.5
Reads last audit result + full knowledge base as context.
"""
import os
from openrouter_client import get_client as _or_client, MODEL as _OR_MODEL
from knowledge_loader import load_knowledge

SYSTEM_PROMPT = """You are a senior CA in India. Answer in plain text only — no markdown, no stars, no hashes, no bold, no bullet dashes, no em-dashes, no headers.

STRICT RULES:
- Maximum 5 lines. Never more.
- Plain sentences only.
- Use Rs. for amounts (not symbols).
- Cite one law section if relevant.
- If you don't have the data, say so in one line.

Tone: WhatsApp message from a CA. Short, direct, useful.
"""

# Load knowledge base once at import time
_KNOWLEDGE = load_knowledge('ask_ca')


def build_context(audit_data: dict) -> str:
    """Convert audit result dict into a text context block for Claude."""
    if not audit_data:
        return "No audit data has been uploaded yet. Answer general accounting questions."

    lines = []
    summary = audit_data.get('summary', {})

    if summary.get('company'):
        lines.append(f"Company: {summary['company']}")
    if summary.get('period'):
        lines.append(f"Period: {summary['period']}")
    if summary.get('score') is not None:
        lines.append(f"Compliance Health Score: {summary['score']}/100")

    critical_count  = summary.get('critical', 0)
    warnings_count  = summary.get('warnings', 0)
    questions_count = summary.get('questions', 0)
    lines.append(f"Issues: {critical_count} Critical | {warnings_count} Warnings | {questions_count} Questions")
    lines.append("NOTE: All amounts below are pre-computed by the audit engine. Use them exactly — do NOT re-calculate or second-guess these figures.")

    # Ledger classification issues
    ledger_issues = audit_data.get('ledger_classification', [])
    if ledger_issues:
        lines.append(f"\nLEDGER CLASSIFICATION ISSUES ({len(ledger_issues)}):")
        for item in ledger_issues[:15]:
            sev   = item.get('severity', '')
            ledg  = item.get('ledger', '')
            issue = item.get('issue', '')
            grp   = item.get('group', '')
            amt   = item.get('amount', 0)
            lines.append(f"  [{sev}] {ledg} (Group: {grp}) — {issue} | Balance: ₹{amt:,.0f}")

    # Cash violations
    cash_v = audit_data.get('cash_violations', [])
    if cash_v:
        lines.append(f"\nCASH VIOLATIONS >₹10,000 — Sec 40A(3) ({len(cash_v)}):")
        for v in cash_v[:10]:
            lines.append(f"  {v.get('date','')}  {v.get('party','')}  ₹{v.get('amount',0):,.0f}")

    # Outstanding balances
    outstanding = audit_data.get('outstanding', [])
    if outstanding:
        lines.append(f"\nOUTSTANDING / ABNORMAL BALANCES ({len(outstanding)}):")
        for o in outstanding[:10]:
            lines.append(f"  [{o.get('severity','')}] {o.get('ledger','')} — {o.get('issue','')} | ₹{o.get('balance',0):,.0f}")

    # Large expenses — GROUP by party so AI sees the same totals as the query cards
    large_exp = audit_data.get('large_expenses', [])
    if large_exp:
        # Build grouped totals (mirrors buildCAQueries logic in the frontend)
        party_totals = {}
        for e in large_exp:
            p = e.get('party', 'Unknown')
            if p not in party_totals:
                party_totals[p] = {'total': 0, 'count': 0, 'dates': []}
            party_totals[p]['total'] += e.get('amount', 0)
            party_totals[p]['count'] += 1
            party_totals[p]['dates'].append(e.get('date', ''))
        lines.append(f"\nLARGE EXPENSES — grouped by party ({len(party_totals)} parties, {len(large_exp)} payments total):")
        lines.append("  IMPORTANT: Always use these TOTAL figures when discussing payments to any party.")
        for party, info in sorted(party_totals.items(), key=lambda x: -x[1]['total']):
            count = info['count']
            total = info['total']
            dates = ', '.join(sorted(set(info['dates']))[:3])
            suffix = f"({count} payments on {dates})" if count > 1 else f"(on {dates})"
            lines.append(f"  {party}: ₹{total:,.0f} total {suffix}")

    # TDS items (if engine returns them)
    tds_items = audit_data.get('tds_items', [])
    if tds_items:
        lines.append(f"\nTDS ITEMS ({len(tds_items)}):")
        for t in tds_items[:10]:
            lines.append(f"  {t.get('ledger','')} — ₹{t.get('amount',0):,.0f} | {t.get('note','')}")

    # Loans
    loans = audit_data.get('loans', [])
    if loans:
        lines.append(f"\nLOANS / DIRECTOR LOANS ({len(loans)}):")
        for l in loans[:5]:
            lines.append(f"  {l.get('ledger','')} — ₹{l.get('balance',0):,.0f} | {l.get('note','')}")

    # Bank accounts
    bank_accounts = audit_data.get('bank_accounts', [])
    if bank_accounts:
        lines.append(f"\nBANK ACCOUNTS IN BOOKS ({len(bank_accounts)}):")
        for b in bank_accounts:
            lines.append(f"  {b.get('ledger','')} — Rs.{b.get('balance',0):,.0f} {b.get('dr_cr','')}")

    # TDS compliance
    tds_comp = audit_data.get('tds_compliance', [])
    if tds_comp:
        lines.append(f"\nTDS COMPLIANCE ISSUES ({len(tds_comp)}):")
        for t in tds_comp:
            if t.get('tds_expected', 0) > 0:
                lines.append(f"  [Sec {t.get('section','')}] {t.get('party','')} — Paid Rs.{t.get('total_paid',0):,.0f} | TDS expected Rs.{t.get('tds_expected',0):,.0f} @ {t.get('rate',0)}%")
            else:
                lines.append(f"  {t.get('issue','')}")

    # Salary compliance
    sal_comp = audit_data.get('salary_compliance', [])
    if sal_comp:
        lines.append(f"\nSALARY / PF / PT COMPLIANCE ({len(sal_comp)}):")
        for s in sal_comp:
            lines.append(f"  [{s.get('severity','')}] {s.get('issue','')}")

    # Personal marks
    personal = audit_data.get('personal_marks', [])
    if personal:
        lines.append(f"\nITEMS MARKED AS PERSONAL by user ({len(personal)}):")
        for p in personal[:5]:
            lines.append(f"  {p.get('date','')}  {p.get('party','')}  ₹{p.get('amount',0):,.0f}")

    return '\n'.join(lines)


def chat(user_message: str, audit_data: dict = None, history: list = None) -> str:
    """
    Call Claude API and return the CA's response as a string.

    user_message : the user's question
    audit_data   : dict from last audit result (or None)
    history      : list of {role, content} — prior turns (client manages state)
    """
    client = _or_client()

    context = build_context(audit_data)
    system  = (
        SYSTEM_PROMPT
        + f"\n\n## KNOWLEDGE BASE (Indian CA rules — GST, TDS, Audit, Accounting, Tally):\n{_KNOWLEDGE}"
        + f"\n\n## CLIENT'S ACCOUNTING DATA (use this for specific answers):\n{context}"
    )

    messages = [{'role': 'system', 'content': system}]
    if history:
        for turn in history[-10:]:
            role    = turn.get('role', 'user')
            content = turn.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content})

    messages.append({'role': 'user', 'content': user_message})

    try:
        response = client.chat.completions.create(
            model=_OR_MODEL,
            max_tokens=300,
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        import sys
        print(f'[AskCA] OpenRouter error: {e}', file=sys.stderr, flush=True)
        raise
