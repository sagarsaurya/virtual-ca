import pandas as pd
from datetime import datetime, date

LTCG_EXEMPT = 100000   # ₹1L exempt for equity LTCG
LTCG_RATE   = 0.10
STCG_RATE   = 0.15
HOLDING_MONTHS_LONG = 12  # >12 months = LTCG for equity

INVESTMENT_KEYWORDS = ['shares','equity','stock','nse','bse','mutual fund','mf','etf',
                       'zerodha','groww','angel','icicidirect','hdfc sec','sbi sec',
                       'investment','portfolio','demat']
BUY_KEYWORDS  = ['purchase','buy','bought','subscribed','allotment','invest']
SELL_KEYWORDS = ['sale','sell','sold','redemption','redeemed','exit']

def _parse_date(d):
    if not d or str(d).strip() in ('', 'nan', 'NaT'):
        return None
    try:
        if isinstance(d, (datetime, date)):
            return d if isinstance(d, date) else d.date()
        for fmt in ('%d-%m-%Y','%d/%m/%Y','%Y-%m-%d','%d %b %Y','%b %d %Y'):
            try:
                return datetime.strptime(str(d).strip(), fmt).date()
            except:
                pass
    except:
        pass
    return None

def _holding_months(buy_date, sell_date):
    if not buy_date or not sell_date:
        return 0
    delta = sell_date - buy_date
    return delta.days / 30.44

def calculate_shares_pnl(tb_path, daybook_path=None):
    from audit_engine import parse_trial_balance
    ledgers, _, _ = parse_trial_balance(tb_path)

    # Find investment-related ledgers from TB
    inv_ledgers = []
    for l in ledgers:
        name  = l.get('name') or ''
        group = (l.get('group') or '').lower()
        n     = name.lower()
        if any(kw in n for kw in INVESTMENT_KEYWORDS) or 'investment' in group:
            inv_ledgers.append(l)

    # Try to parse daybook for buy/sell transactions
    transactions = []
    if daybook_path:
        try:
            df = pd.read_excel(daybook_path, header=None)
            # Look for rows with investment keywords + amounts
            for _, row in df.iterrows():
                row_str = ' '.join(str(c).lower() for c in row if pd.notna(c))
                if not any(kw in row_str for kw in INVESTMENT_KEYWORDS):
                    continue
                # Try to extract date, party, amount
                date_val = None
                amount   = 0
                narration = row_str
                for cell in row:
                    if pd.notna(cell):
                        d = _parse_date(cell)
                        if d:
                            date_val = d
                        try:
                            v = float(str(cell).replace(',',''))
                            if v > 100:
                                amount = v
                        except:
                            pass
                if date_val and amount > 0:
                    tx_type = 'sell' if any(kw in row_str for kw in SELL_KEYWORDS) else 'buy'
                    scrip   = next((kw for kw in INVESTMENT_KEYWORDS if kw in row_str), 'Unknown')
                    transactions.append({
                        'date': date_val, 'type': tx_type,
                        'scrip': narration[:40], 'amount': amount,
                    })
        except:
            pass

    # FIFO matching of buy/sell
    buys  = [t for t in transactions if t['type'] == 'buy']
    sells = [t for t in transactions if t['type'] == 'sell']
    trades = []
    buy_queue = list(buys)

    for sell in sells:
        if not buy_queue:
            break
        buy = buy_queue.pop(0)
        gain    = sell['amount'] - buy['amount']
        months  = _holding_months(buy['date'], sell['date'])
        is_long = months >= HOLDING_MONTHS_LONG

        if is_long:
            taxable_gain = max(0, gain - LTCG_EXEMPT) if gain > 0 else 0
            tax = round(taxable_gain * LTCG_RATE, 0)
            gain_type = 'LTCG'
        else:
            taxable_gain = max(0, gain)
            tax = round(taxable_gain * STCG_RATE, 0)
            gain_type = 'STCG'

        trades.append({
            'scrip': sell['scrip'][:30],
            'buy_date': str(buy['date']),
            'sell_date': str(sell['date']),
            'buy_value': round(buy['amount'], 0),
            'sell_value': round(sell['amount'], 0),
            'gain': round(gain, 0),
            'holding_months': round(months, 1),
            'type': gain_type,
            'tax': tax,
        })

    # If no daybook transactions, estimate from TB balances
    if not trades and inv_ledgers:
        for l in inv_ledgers:
            bal = abs(float(l.get('debit') or 0) - float(l.get('credit') or 0))
            if bal > 0:
                trades.append({
                    'scrip': l.get('name', '')[:30],
                    'buy_date': '—',
                    'sell_date': '—',
                    'buy_value': round(bal, 0),
                    'sell_value': 0,
                    'gain': 0,
                    'holding_months': 0,
                    'type': 'Open Position',
                    'tax': 0,
                    'note': 'Upload daybook for P&L calculation',
                })

    stcg_total = sum(t['gain'] for t in trades if t['type'] == 'STCG' and t['gain'] > 0)
    ltcg_total = sum(t['gain'] for t in trades if t['type'] == 'LTCG' and t['gain'] > 0)
    stcg_tax   = sum(t['tax'] for t in trades if t['type'] == 'STCG')
    ltcg_tax   = sum(t['tax'] for t in trades if t['type'] == 'LTCG')
    total_gain = stcg_total + ltcg_total
    total_tax  = stcg_tax + ltcg_tax

    return {
        'trades': trades,
        'stcg_total': round(stcg_total, 0),
        'ltcg_total': round(ltcg_total, 0),
        'stcg_tax': round(stcg_tax, 0),
        'ltcg_tax': round(ltcg_tax, 0),
        'total_gain': round(total_gain, 0),
        'total_tax': round(total_tax, 0),
        'ltcg_exempt': LTCG_EXEMPT,
        'open_positions': len([t for t in trades if t['type'] == 'Open Position']),
        'closed_trades': len([t for t in trades if t['type'] in ('STCG','LTCG')]),
        'investment_ledgers': [l.get('name','') for l in inv_ledgers],
    }
