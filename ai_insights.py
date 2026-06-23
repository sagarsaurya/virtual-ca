"""
ai_insights.py — Short AI insight for every VirtualCA feature.
Takes feature name + Python result dict → returns 2-4 line CA commentary.
Uses Claude Haiku 4.5 (fast + cheap for short insights).
"""
import os
import json
import anthropic

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    return _client


FEATURE_PROMPTS = {

    'balance_sheet': """You are a senior Indian CA. Analyse this Balance Sheet data and give a 3-line insight.
Cover: Current Ratio (Current Assets / Current Liabilities), any alarming liability, and one action point.
Use ₹ Indian format. Cite Companies Act 2013 Schedule III or AS if relevant. Be direct, no fluff.""",

    'cash_flow': """You are a senior Indian CA. Analyse this Cash Flow Statement (AS-3) and give a 3-line insight.
Cover: Is operating cash flow positive or negative? Is the company funding operations from debt/investments?
One clear risk or positive. Use ₹ Indian format. Be direct.""",

    'tds_analysis': """You are a senior Indian CA. Analyse this TDS data and give a 3-line insight.
Cover: Total TDS liability, any missed deductions, estimated interest under Sec 201(1A) if applicable.
Cite specific IT Act sections (194C, 194J, 194I etc). Use ₹ Indian format. Be direct.""",

    'tds_detect': """You are a senior Indian CA. Analyse these missed TDS detections from the daybook.
Give a 3-line insight: total payments where TDS was missed, estimated TDS amount, penalty risk.
Cite IT Act sections. Use ₹ Indian format. Be direct.""",

    'gst_return': """You are a senior Indian CA. Analyse this GST data from the books.
Give a 3-line insight: ITC available vs claimed, output tax liability, any mismatch risk.
Cite CGST Act 2017 sections where relevant. Use ₹ Indian format. Be direct.""",

    'pt_analysis': """You are a senior Indian CA. Analyse this Professional Tax data.
Give a 3-line insight: total PT liability, monthly deposit status, penalty risk.
Reference WB PT Act 1979 (or applicable state act). Use ₹ Indian format. Be direct.""",

    'bank_rec': """You are a senior Indian CA. Analyse this Bank Reconciliation result.
Give a 3-line insight: number of unmatched items, likely cause, risk to financial statements.
Reference AS-1 / Companies Act Sec 128 if books don't match bank. Be direct.""",

    'party_rec': """You are a senior Indian CA. Analyse this Party Ledger Reconciliation result.
Give a 3-line insight: total gap amount, likely cause (timing difference vs actual error), action needed.
Reference AS-1 consistency principle. Use ₹ Indian format. Be direct.""",

    'shares_pnl': """You are a senior Indian CA. Analyse this Shares P&L data.
Give a 3-line insight: STCG vs LTCG breakdown, estimated tax liability, ITR form applicable.
Cite IT Act Sec 111A (STCG) and 112A (LTCG). Use ₹ Indian format. Be direct.""",

    'doc_checker': """You are a senior Indian CA. Analyse this Missing Documents report.
Give a 3-line insight: total payment amount without supporting docs, audit risk, recommended action.
Reference IT Act Sec 40A(3) and ICAI SA-500. Use ₹ Indian format. Be direct.""",
}


def generate_insight(feature: str, data: dict) -> str:
    """
    Generate a short CA insight for a feature result.
    Returns insight string, or empty string on failure.
    """
    prompt = FEATURE_PROMPTS.get(feature)
    if not prompt:
        return ''

    # Summarise the data — don't send entire raw dict (saves tokens)
    try:
        summary = _summarise(feature, data)
    except Exception:
        summary = json.dumps(data, default=str)[:2000]

    try:
        client = _get_client()
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            messages=[{
                'role': 'user',
                'content': f"{prompt}\n\nDATA:\n{summary}\n\nWrite your insight now (3 lines max, no headings):"
            }]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f'[AI Insight] {feature} error: {e}')
        return ''


def _summarise(feature: str, data: dict) -> str:
    """Convert feature result to compact text for Claude."""
    lines = []

    if feature == 'balance_sheet':
        assets = data.get('assets', {})
        liab   = data.get('liabilities', {})
        lines.append(f"Fixed Assets: ₹{assets.get('fixed_assets', 0):,.0f}")
        lines.append(f"Current Assets: ₹{assets.get('current_assets', 0):,.0f}")
        lines.append(f"Current Liabilities: ₹{liab.get('current_liabilities', 0):,.0f}")
        lines.append(f"Long Term Liabilities: ₹{liab.get('long_term', 0):,.0f}")
        lines.append(f"Capital & Reserves: ₹{liab.get('capital', 0):,.0f}")
        lines.append(f"Total Assets: ₹{data.get('total_assets', 0):,.0f}")

    elif feature == 'cash_flow':
        lines.append(f"Operating Cash Flow: ₹{data.get('operating', {}).get('net', 0):,.0f}")
        lines.append(f"Investing Cash Flow: ₹{data.get('investing', {}).get('net', 0):,.0f}")
        lines.append(f"Financing Cash Flow: ₹{data.get('financing', {}).get('net', 0):,.0f}")
        lines.append(f"Net Change in Cash: ₹{data.get('net_change', 0):,.0f}")

    elif feature == 'tds_analysis':
        sections = data.get('sections', [])
        total_liability = sum(s.get('tds_payable', 0) for s in sections)
        total_deposited = sum(s.get('tds_deposited', 0) for s in sections)
        lines.append(f"TDS Liability: ₹{total_liability:,.0f}")
        lines.append(f"TDS Deposited: ₹{total_deposited:,.0f}")
        lines.append(f"Pending: ₹{total_liability - total_deposited:,.0f}")
        for s in sections[:5]:
            lines.append(f"  {s.get('section','')}: Payable ₹{s.get('tds_payable',0):,.0f} | Deposited ₹{s.get('tds_deposited',0):,.0f}")

    elif feature == 'tds_detect':
        missed = data.get('missed', [])
        total  = sum(m.get('tds_amount', 0) for m in missed)
        lines.append(f"Payments where TDS missed: {len(missed)}")
        lines.append(f"Estimated TDS not deducted: ₹{total:,.0f}")
        for m in missed[:5]:
            lines.append(f"  {m.get('party','')} ₹{m.get('amount',0):,.0f} → TDS ₹{m.get('tds_amount',0):,.0f} ({m.get('section','')})")

    elif feature == 'gst_return':
        lines.append(f"Output GST (Sales): ₹{data.get('output_gst', 0):,.0f}")
        lines.append(f"Input Tax Credit: ₹{data.get('input_credit', 0):,.0f}")
        lines.append(f"Net GST Payable: ₹{data.get('net_payable', 0):,.0f}")
        lines.append(f"Pending GST: ₹{data.get('pending', 0):,.0f}")

    elif feature == 'pt_analysis':
        lines.append(f"Total Salary: ₹{data.get('total_salary', 0):,.0f}")
        lines.append(f"PT Liability: ₹{data.get('pt_liability', 0):,.0f}")
        lines.append(f"PT Deposited: ₹{data.get('pt_deposited', 0):,.0f}")
        lines.append(f"PT Pending: ₹{data.get('pt_pending', 0):,.0f}")

    elif feature == 'bank_rec':
        s = data.get('summary', {})
        lines.append(f"Matched: {s.get('matched', 0)}")
        lines.append(f"Missing in Tally: {s.get('bank_only', 0)}")
        lines.append(f"Extra in Tally: {s.get('tally_only', 0)}")
        lines.append(f"Wrong Date: {s.get('wrong_date', 0)}")
        lines.append(f"Duplicates: {s.get('duplicates', 0)}")

    elif feature == 'party_rec':
        lines.append(f"Party: {data.get('party_name', '')}")
        lines.append(f"Your Books Balance: ₹{data.get('tally_balance', 0):,.0f}")
        lines.append(f"Party's Books Balance: ₹{data.get('party_balance', 0):,.0f}")
        lines.append(f"Gap: ₹{data.get('gap', 0):,.0f}")
        lines.append(f"Unmatched entries: {len(data.get('unmatched_tally', []))} in your books, {len(data.get('unmatched_party', []))} in party books")

    elif feature == 'shares_pnl':
        lines.append(f"Total Trades: {data.get('total_trades', 0)}")
        lines.append(f"STCG: ₹{data.get('stcg', 0):,.0f} — Tax: ₹{data.get('stcg_tax', 0):,.0f}")
        lines.append(f"LTCG: ₹{data.get('ltcg', 0):,.0f} — Tax: ₹{data.get('ltcg_tax', 0):,.0f}")
        lines.append(f"Total P&L: ₹{data.get('total_pnl', 0):,.0f}")

    elif feature == 'doc_checker':
        items = data.get('items', []) if isinstance(data, dict) else data
        high  = [i for i in items if i.get('risk') == 'high']
        total_amt = sum(i.get('amount', 0) for i in high)
        lines.append(f"High risk missing docs: {len(high)}")
        lines.append(f"Total amount at risk: ₹{total_amt:,.0f}")
        for i in high[:5]:
            lines.append(f"  {i.get('date','')} {i.get('party','')} ₹{i.get('amount',0):,.0f}")

    return '\n'.join(lines) if lines else json.dumps(data, default=str)[:1500]
