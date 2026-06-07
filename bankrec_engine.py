"""
Bank Reconciliation Engine
Supports: ICICI, HDFC, SBI, Axis, Kotak, Yes Bank, PNB, BOB
Input : Bank Statement (PDF or CSV/Excel) + Tally Bank Ledger (Excel)
Output: matched, bank_only, tally_only, duplicates
"""

import re
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

try:
    import pdfplumber
    PDF_OK = True
except ImportError:
    PDF_OK = False


# ── date helpers ──────────────────────────────────────────────────────────────
DATE_FMTS = [
    '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
    '%d %b %Y', '%d %b %y', '%d-%b-%Y', '%d-%b-%y',
    '%d %B %Y', '%d/%b/%Y', '%Y-%m-%d',
]

def parse_date(s):
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    for fmt in DATE_FMTS:
        try:
            return datetime.strptime(s, fmt).date()
        except:
            pass
    return None

def clean_amount(s):
    if s is None: return 0.0
    if isinstance(s, (int, float)): return float(s)
    s = str(s).replace(',', '').replace(' ', '').strip()
    if s in ('', '-', 'nil', 'NIL'): return 0.0
    try:
        return abs(float(s))
    except:
        return 0.0


# ══════════════════════════════════════════════════════════════════════════════
# BANK PDF PARSERS
# ══════════════════════════════════════════════════════════════════════════════

def detect_bank(text: str) -> str:
    t = text.upper()
    if 'ICICI'    in t: return 'ICICI'
    if 'HDFC'     in t: return 'HDFC'
    if 'STATE BANK' in t or 'SBI' in t: return 'SBI'
    if 'AXIS BANK' in t or 'AXIS' in t: return 'AXIS'
    if 'KOTAK'    in t: return 'KOTAK'
    if 'YES BANK' in t: return 'YES'
    if 'PUNJAB NATIONAL' in t or 'PNB' in t: return 'PNB'
    if 'BANK OF BARODA' in t or 'BOB' in t: return 'BOB'
    if 'INDUSIND'  in t: return 'INDUSIND'
    if 'FEDERAL'   in t: return 'FEDERAL'
    return 'GENERIC'


def parse_pdf_statement(filepath: str) -> List[Dict]:
    if not PDF_OK:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

    with pdfplumber.open(filepath) as pdf:
        full_text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
        bank = detect_bank(full_text)

        rows = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                rows.extend(table)

    if bank == 'ICICI':   return _parse_icici(rows, full_text)
    if bank == 'HDFC':    return _parse_hdfc(rows, full_text)
    if bank == 'SBI':     return _parse_sbi(rows, full_text)
    if bank == 'AXIS':    return _parse_axis(rows, full_text)
    if bank == 'KOTAK':   return _parse_kotak(rows, full_text)
    return _parse_generic(rows, full_text, bank)


# ── ICICI ─────────────────────────────────────────────────────────────────────
def _parse_icici(rows, text):
    """
    ICICI columns: Date | Transaction Remarks | Ref No | Value Date | Withdrawal (Dr) | Deposit (Cr) | Balance
    """
    txns = []
    header_found = False
    col_map = {}

    for row in rows:
        if not row: continue
        cells = [str(c or '').strip() for c in row]

        # Detect header row
        if not header_found:
            joined = ' '.join(cells).upper()
            if 'DATE' in joined and ('WITHDRAWAL' in joined or 'DEBIT' in joined or 'DR' in joined):
                header_found = True
                for i, c in enumerate(cells):
                    cu = c.upper()
                    if 'DATE' in cu and 'VALUE' not in cu and 'col_date' not in col_map:
                        col_map['date'] = i
                    elif 'REMARK' in cu or 'NARRATION' in cu or 'DESCRIPTION' in cu or 'PARTICULARS' in cu:
                        col_map['narration'] = i
                    elif 'WITHDRAWAL' in cu or ('DR' in cu and 'CREDIT' not in cu):
                        col_map['debit'] = i
                    elif 'DEPOSIT' in cu or ('CR' in cu and 'DEBIT' not in cu):
                        col_map['credit'] = i
                continue

        if not header_found: continue
        if len(cells) < 4: continue

        date_str  = cells[col_map.get('date', 0)]
        narration = cells[col_map.get('narration', 1)]
        debit_str = cells[col_map.get('debit', 4)] if 'debit' in col_map else ''
        cred_str  = cells[col_map.get('credit', 5)] if 'credit' in col_map else ''

        dt = parse_date(date_str)
        if not dt: continue

        debit  = clean_amount(debit_str)
        credit = clean_amount(cred_str)
        amount = debit if debit else credit
        dr_cr  = 'Dr' if debit else 'Cr'

        if amount == 0: continue
        txns.append({'date': dt, 'narration': narration, 'amount': amount,
                     'dr_cr': dr_cr, 'source': 'bank'})
    return txns


# ── HDFC ──────────────────────────────────────────────────────────────────────
def _parse_hdfc(rows, text):
    """
    HDFC columns: Date | Narration | Chq./Ref.No | Value Dt | Withdrawal Amt | Deposit Amt | Closing Balance
    """
    txns = []
    header_found = False
    col_map = {}

    for row in rows:
        if not row: continue
        cells = [str(c or '').strip() for c in row]
        if not header_found:
            joined = ' '.join(cells).upper()
            if 'DATE' in joined and ('WITHDRAWAL' in joined or 'NARRATION' in joined):
                header_found = True
                for i, c in enumerate(cells):
                    cu = c.upper()
                    if 'DATE' in cu and 'VALUE' not in cu and 'date' not in col_map:
                        col_map['date'] = i
                    elif 'NARRATION' in cu or 'DESCRIPTION' in cu:
                        col_map['narration'] = i
                    elif 'WITHDRAWAL' in cu or 'DEBIT' in cu:
                        col_map['debit'] = i
                    elif 'DEPOSIT' in cu or 'CREDIT' in cu:
                        col_map['credit'] = i
                continue
        if not header_found: continue
        if len(cells) < 4: continue

        dt = parse_date(cells[col_map.get('date', 0)])
        if not dt: continue
        narration = cells[col_map.get('narration', 1)]
        debit  = clean_amount(cells[col_map.get('debit', 4)] if 'debit' in col_map else '')
        credit = clean_amount(cells[col_map.get('credit', 5)] if 'credit' in col_map else '')
        amount = debit if debit else credit
        if amount == 0: continue
        txns.append({'date': dt, 'narration': narration, 'amount': amount,
                     'dr_cr': 'Dr' if debit else 'Cr', 'source': 'bank'})
    return txns


# ── SBI ───────────────────────────────────────────────────────────────────────
def _parse_sbi(rows, text):
    """
    SBI columns: Txn Date | Value Date | Description | Ref No / Cheque No | Debit | Credit | Balance
    """
    txns = []
    header_found = False
    col_map = {}

    for row in rows:
        if not row: continue
        cells = [str(c or '').strip() for c in row]
        if not header_found:
            joined = ' '.join(cells).upper()
            if 'DATE' in joined and ('DEBIT' in joined or 'CREDIT' in joined):
                header_found = True
                for i, c in enumerate(cells):
                    cu = c.upper()
                    if ('TXN' in cu or 'TRANSACTION' in cu) and 'DATE' in cu:
                        col_map['date'] = i
                    elif 'DESCRIPTION' in cu or 'NARRATION' in cu or 'PARTICULARS' in cu:
                        col_map['narration'] = i
                    elif 'DEBIT' in cu and 'credit' not in col_map:
                        col_map['debit'] = i
                    elif 'CREDIT' in cu:
                        col_map['credit'] = i
                if 'date' not in col_map: col_map['date'] = 0
                if 'narration' not in col_map: col_map['narration'] = 2
                continue
        if not header_found: continue
        if len(cells) < 4: continue

        dt = parse_date(cells[col_map.get('date', 0)])
        if not dt: continue
        narration = cells[col_map.get('narration', 2)]
        debit  = clean_amount(cells[col_map.get('debit', 4)] if 'debit' in col_map else '')
        credit = clean_amount(cells[col_map.get('credit', 5)] if 'credit' in col_map else '')
        amount = debit if debit else credit
        if amount == 0: continue
        txns.append({'date': dt, 'narration': narration, 'amount': amount,
                     'dr_cr': 'Dr' if debit else 'Cr', 'source': 'bank'})
    return txns


# ── AXIS ──────────────────────────────────────────────────────────────────────
def _parse_axis(rows, text):
    """
    Axis Bank: Tran Date | CHQNO | PARTICULARS | DR | CR | BAL
    """
    txns = []
    header_found = False
    col_map = {}

    for row in rows:
        if not row: continue
        cells = [str(c or '').strip() for c in row]
        if not header_found:
            joined = ' '.join(cells).upper()
            if 'DATE' in joined and ('DR' in joined or 'CR' in joined or 'DEBIT' in joined):
                header_found = True
                for i, c in enumerate(cells):
                    cu = c.upper()
                    if 'DATE' in cu and 'date' not in col_map:
                        col_map['date'] = i
                    elif 'PARTICULAR' in cu or 'NARRATION' in cu or 'DESCRIPTION' in cu:
                        col_map['narration'] = i
                    elif cu in ('DR', 'DEBIT', 'WITHDRAWAL'):
                        col_map['debit'] = i
                    elif cu in ('CR', 'CREDIT', 'DEPOSIT'):
                        col_map['credit'] = i
                continue
        if not header_found: continue
        if len(cells) < 3: continue

        dt = parse_date(cells[col_map.get('date', 0)])
        if not dt: continue
        narration = cells[col_map.get('narration', 2)]
        debit  = clean_amount(cells[col_map.get('debit', 3)] if 'debit' in col_map else '')
        credit = clean_amount(cells[col_map.get('credit', 4)] if 'credit' in col_map else '')
        amount = debit if debit else credit
        if amount == 0: continue
        txns.append({'date': dt, 'narration': narration, 'amount': amount,
                     'dr_cr': 'Dr' if debit else 'Cr', 'source': 'bank'})
    return txns


# ── KOTAK ─────────────────────────────────────────────────────────────────────
def _parse_kotak(rows, text):
    """Kotak format similar to HDFC"""
    return _parse_hdfc(rows, text)  # same column structure


# ── GENERIC fallback ──────────────────────────────────────────────────────────
def _parse_generic(rows, text, bank_name='GENERIC'):
    """
    Tries to find a header row with Date + some amount column, then extract.
    Works for most Indian bank PDFs not explicitly covered above.
    """
    txns = []
    header_found = False
    date_col = narr_col = debit_col = credit_col = None

    for row in rows:
        if not row: continue
        cells = [str(c or '').strip() for c in row]

        if not header_found:
            joined = ' '.join(cells).upper()
            if re.search(r'\bDATE\b', joined) and re.search(r'(DEBIT|CREDIT|DR|CR|WITHDRAWAL|DEPOSIT|AMOUNT)', joined):
                header_found = True
                for i, c in enumerate(cells):
                    cu = c.upper()
                    if re.search(r'\bDATE\b', cu) and date_col is None: date_col = i
                    elif re.search(r'(NARRATION|DESCRIPTION|PARTICULARS|REMARK)', cu) and narr_col is None: narr_col = i
                    elif re.search(r'(WITHDRAWAL|DEBIT|\bDR\b)', cu) and debit_col is None: debit_col = i
                    elif re.search(r'(DEPOSIT|CREDIT|\bCR\b)', cu) and credit_col is None: credit_col = i
                if date_col is None: date_col = 0
                if narr_col is None: narr_col = 1
                continue

        if not header_found: continue
        if len(cells) <= max(filter(lambda x: x is not None, [date_col, narr_col, debit_col or 0, credit_col or 0])): continue

        dt = parse_date(cells[date_col])
        if not dt: continue
        narration = cells[narr_col] if narr_col is not None else ''
        debit  = clean_amount(cells[debit_col])  if debit_col  is not None and debit_col  < len(cells) else 0
        credit = clean_amount(cells[credit_col]) if credit_col is not None and credit_col < len(cells) else 0
        amount = debit if debit else credit
        if amount == 0: continue
        txns.append({'date': dt, 'narration': narration, 'amount': amount,
                     'dr_cr': 'Dr' if debit else 'Cr', 'source': 'bank'})

    return txns


# ══════════════════════════════════════════════════════════════════════════════
# CSV / EXCEL BANK STATEMENT PARSER
# ══════════════════════════════════════════════════════════════════════════════

def parse_csv_excel_statement(filepath: str) -> List[Dict]:
    ext = filepath.lower()
    if ext.endswith('.csv'):
        try:
            df = pd.read_csv(filepath, skiprows=_detect_header_row_csv(filepath))
        except:
            df = pd.read_csv(filepath, encoding='latin1', skiprows=_detect_header_row_csv(filepath))
    else:
        df = pd.read_excel(filepath, header=None)
        # find header row
        hrow = 0
        for i, row in df.iterrows():
            vals = ' '.join(str(v).upper() for v in row if pd.notna(v))
            if re.search(r'\bDATE\b', vals) and re.search(r'(DEBIT|CREDIT|DR|CR|AMOUNT)', vals):
                hrow = i; break
        df = pd.read_excel(filepath, header=hrow)

    df.columns = [str(c).strip().upper() for c in df.columns]
    return _df_to_txns(df, 'bank')


def _detect_header_row_csv(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f):
                if re.search(r'DATE', line.upper()) and re.search(r'(DEBIT|CREDIT|DR|CR|AMOUNT)', line.upper()):
                    return i
    except:
        pass
    return 0


def _df_to_txns(df, source):
    txns = []
    # find columns
    date_col = narr_col = debit_col = credit_col = amount_col = drcrtype_col = None
    for c in df.columns:
        cu = c.upper()
        if re.search(r'\bDATE\b', cu) and date_col is None: date_col = c
        elif re.search(r'(NARRATION|DESCRIPTION|PARTICULARS|REMARK|TRANSACTION DETAILS)', cu) and narr_col is None: narr_col = c
        elif re.search(r'(WITHDRAWAL|DEBIT|\bDR\b)', cu) and debit_col is None: debit_col = c
        elif re.search(r'(DEPOSIT|CREDIT|\bCR\b)', cu) and credit_col is None: credit_col = c
        elif re.search(r'\bAMOUNT\b', cu) and amount_col is None: amount_col = c
        elif re.search(r'(TYPE|DR/CR|DR\.CR)', cu) and drcrtype_col is None: drcrtype_col = c

    if date_col is None: return txns

    for _, row in df.iterrows():
        dt = parse_date(str(row.get(date_col, '')))
        if not dt: continue
        narration = str(row.get(narr_col, '')) if narr_col else ''

        if debit_col and credit_col:
            debit  = clean_amount(row.get(debit_col))
            credit = clean_amount(row.get(credit_col))
            amount = debit if debit else credit
            dr_cr  = 'Dr' if debit else 'Cr'
        elif amount_col:
            amount = clean_amount(row.get(amount_col))
            if drcrtype_col:
                dc = str(row.get(drcrtype_col, '')).upper()
                dr_cr = 'Dr' if 'DR' in dc or 'DEBIT' in dc or 'W' in dc else 'Cr'
            else:
                dr_cr = 'Dr'
        else:
            continue

        if amount == 0: continue
        txns.append({'date': dt, 'narration': narration, 'amount': amount,
                     'dr_cr': dr_cr, 'source': source})
    return txns


# ══════════════════════════════════════════════════════════════════════════════
# TALLY BANK LEDGER PARSER
# ══════════════════════════════════════════════════════════════════════════════

def parse_tally_ledger(filepath: str) -> List[Dict]:
    ext = filepath.lower()
    if ext.endswith('.csv'):
        df = pd.read_csv(filepath, header=None)
    else:
        df = pd.read_excel(filepath, header=None)

    # Find header row
    hrow = 0
    for i, row in df.iterrows():
        vals = ' '.join(str(v).upper() for v in row if pd.notna(v))
        if re.search(r'\bDATE\b', vals):
            hrow = i; break

    df = pd.read_excel(filepath, header=hrow) if not ext.endswith('.csv') else pd.read_csv(filepath, header=hrow)
    df.columns = [str(c).strip().upper() for c in df.columns]
    return _df_to_txns(df, 'tally')


# ══════════════════════════════════════════════════════════════════════════════
# MATCHING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def reconcile(bank_txns: List[Dict], tally_txns: List[Dict]) -> Dict:
    matched    = []
    bank_only  = []
    tally_only = []
    duplicates = []

    # Detect duplicates within each list
    def find_dupes(txns, label):
        seen = {}
        dupes = []
        for t in txns:
            key = (t['date'], round(t['amount'], 2))
            if key in seen:
                dupes.append({**t, 'duplicate_of': seen[key]['narration'], 'in': label})
            else:
                seen[key] = t
        return dupes, [t for t in txns if (t['date'], round(t['amount'],2)) not in {(d['date'], round(d['amount'],2)) for d in dupes}]

    bank_dupes,  bank_clean  = find_dupes(bank_txns,  'Bank')
    tally_dupes, tally_clean = find_dupes(tally_txns, 'Tally')
    duplicates = bank_dupes + tally_dupes

    # Match bank vs tally (date ±1 day, amount exact)
    tally_used = [False] * len(tally_clean)

    for bt in bank_clean:
        found = False
        for j, tt in enumerate(tally_clean):
            if tally_used[j]: continue
            date_diff = abs((bt['date'] - tt['date']).days)
            amt_match = abs(bt['amount'] - tt['amount']) < 1.0  # allow Rs.1 rounding
            if date_diff <= 1 and amt_match:
                matched.append({
                    'date':          str(bt['date']),
                    'bank_narration': bt['narration'],
                    'tally_narration':tt['narration'],
                    'amount':        bt['amount'],
                    'dr_cr':         bt['dr_cr'],
                    'date_diff':     date_diff,
                })
                tally_used[j] = True
                found = True
                break
        if not found:
            bank_only.append({
                'date':      str(bt['date']),
                'narration': bt['narration'],
                'amount':    bt['amount'],
                'dr_cr':     bt['dr_cr'],
                'issue':     'In bank statement but not in Tally',
            })

    for j, tt in enumerate(tally_clean):
        if not tally_used[j]:
            tally_only.append({
                'date':      str(tt['date']),
                'narration': tt['narration'],
                'amount':    tt['amount'],
                'dr_cr':     tt['dr_cr'],
                'issue':     'In Tally but not in bank statement',
            })

    # format duplicates
    dupes_out = [{
        'date':      str(d['date']),
        'narration': d['narration'],
        'amount':    d['amount'],
        'dr_cr':     d['dr_cr'],
        'in':        d.get('in', ''),
        'issue':     f"Duplicate entry in {d.get('in','')} — same date & amount appears twice",
    } for d in duplicates]

    return {
        'matched':    matched,
        'bank_only':  bank_only,
        'tally_only': tally_only,
        'duplicates': dupes_out,
        'summary': {
            'total_bank':    len(bank_txns),
            'total_tally':   len(tally_txns),
            'matched':       len(matched),
            'bank_only':     len(bank_only),
            'tally_only':    len(tally_only),
            'duplicates':    len(dupes_out),
            'match_pct':     round(len(matched) / max(len(bank_txns), 1) * 100, 1),
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def run_bankrec(bank_path: str, tally_path: str, bank_filename: str = '') -> Dict:
    # Parse bank statement
    ext = bank_filename.lower() if bank_filename else bank_path.lower()
    if ext.endswith('.pdf'):
        bank_txns = parse_pdf_statement(bank_path)
        if not bank_txns:
            raise ValueError("Could not extract transactions from PDF. Make sure it's a digital (not scanned) bank statement.")
    else:
        bank_txns = parse_csv_excel_statement(bank_path)

    if not bank_txns:
        raise ValueError("No transactions found in bank statement. Please check the file format.")

    # Parse tally ledger
    tally_txns = parse_tally_ledger(tally_path)
    if not tally_txns:
        raise ValueError("No transactions found in Tally ledger. Please check the file format.")

    return reconcile(bank_txns, tally_txns)
