"""
ca_agent.py — VirtualCA's AI CA powered by Groq API (Llama 3.1 70B)
Reads last audit result as context, answers accounting questions like a senior CA.
"""
import os
from groq import Groq

SYSTEM_PROMPT = """You are a senior Chartered Accountant (CA) based in India with 20+ years of experience.
You are advising a client named Sagar whose accounting data has been uploaded and analysed.

Your role:
- Give specific, data-driven answers based on the actual numbers provided in the context
- Identify TDS issues, mis-classifications, missing entries, compliance violations
- Suggest journal entries in Tally format when relevant (Dr/Cr with ledger names)
- Be concise — like a CA in a WhatsApp call, not a textbook
- Use ₹ symbol for amounts, Indian format (lakhs/crores)
- Reference correct IT Act sections (194C, 194H, 194I, 40A3 etc.), GST rules, Companies Act as needed
- If the user asks something not in the data, say so clearly and give general guidance
- Never make up numbers that aren't in the data

Format:
- Use short paragraphs or bullet points
- Bold key figures and section numbers
- If recommending a journal entry, format it clearly as Dr/Cr
- Keep replies under 300 words unless the question genuinely needs more detail

Tone: Professional but direct. Like a CA who knows your books well and respects your time.
"""


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

    # Large expenses
    large_exp = audit_data.get('large_expenses', [])
    if large_exp:
        lines.append(f"\nLARGE EXPENSES — TDS threshold check ({len(large_exp)}):")
        for e in large_exp[:10]:
            lines.append(f"  {e.get('date','')}  {e.get('party','')}  ₹{e.get('amount',0):,.0f}  [{e.get('voucher_type','')}]")

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
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        return (
            "⚠️ GROQ_API_KEY is not set. "
            "Add it to your .env file or Render environment variables, then restart the server."
        )

    client = Groq(api_key=api_key)

    context = build_context(audit_data)
    system  = SYSTEM_PROMPT + f"\n\n## CLIENT'S ACCOUNTING DATA (use this for specific answers):\n{context}"

    # Build message list — keep last 10 turns to save tokens
    messages = [{'role': 'system', 'content': system}]
    if history:
        for turn in history[-10:]:
            role    = turn.get('role', 'user')
            content = turn.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content})

    messages.append({'role': 'user', 'content': user_message})

    response = client.chat.completions.create(
        model='llama-3.1-70b-versatile',
        max_tokens=1024,
        messages=messages,
    )

    return response.choices[0].message.content
