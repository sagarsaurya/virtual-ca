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
    '%d.%m.%Y', '%d.%m.%y',
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


def parse_pdf_statement(filepath: str):
    """Returns (txns, closing_balance_or_None)"""
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

    # Try table-based parsing first
    txns = []
    closing_balance = None
    if bank == 'ICICI':
        txns, closing_balance = _parse_icici(rows, full_text)
    elif bank == 'HDFC':  txns = _parse_hdfc(rows, full_text)
    elif bank == 'SBI':   txns = _parse_sbi(rows, full_text)
    elif bank == 'AXIS':  txns = _parse_axis(rows, full_text)
    elif bank == 'KOTAK': txns = _parse_kotak(rows, full_text)
    else:                 txns = _parse_generic(rows, full_text, bank)

    # If table parsing failed, fall back to text-based parsing
    if not txns:
        txns = _parse_text_fallback(full_text, bank)

    return txns, closing_balance


def _parse_text_fallback(text: str, bank: str) -> List[Dict]:
    """
    Regex-based fallback for PDFs where pdfplumber can't extract tables.
    Works by finding date patterns followed by amounts on the same line.
    Handles ICICI, HDFC, SBI and generic Indian bank statement text layouts.
    """
    txns = []

    # Date pattern: dd/mm/yyyy or dd-mm-yyyy or dd Mon yyyy or dd-Mon-yyyy
    DATE_PAT = r'(\d{2}[\/\-]\d{2}[\/\-]\d{4}|\d{2}[\/\-]\d{2}[\/\-]\d{2}|\d{2}[\s\-][A-Za-z]{3}[\s\-]\d{4}|\d{2}[\s\-][A-Za-z]{3}[\s\-]\d{2})'
    # Amount: numbers with optional commas, optional decimal
    AMT_PAT  = r'([\d,]+\.?\d{0,2})'

    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if len(line) < 10: continue

        # Try to find a date at start of line
        m = re.match(r'^' + DATE_PAT + r'(.{0,80}?)\s+' + AMT_PAT + r'\s+' + AMT_PAT + r'(?:\s+' + AMT_PAT + r')?', line)
        if m:
            dt = parse_date(m.group(1))
            if not dt: continue
            narration = m.group(2).strip()
            # Last two amounts before balance = debit/credit
            amounts = [clean_amount(m.group(i)) for i in [3,4,5] if m.group(i)]
            amounts = [a for a in amounts if a > 0]
            if len(amounts) >= 2:
                # debit, credit, balance OR credit, debit, balance
                debit  = amounts[0]
                credit = amounts[1]
                amount = debit if debit else credit
                dr_cr  = 'Dr' if debit else 'Cr'
            elif len(amounts) == 1:
                amount = amounts[0]
                dr_cr  = _guess_dr_cr(narration)
            else:
                continue
            if amount == 0: continue
            txns.append({'date': dt, 'narration': narration, 'amount': amount, 'dr_cr': dr_cr, 'source': 'bank'})
            continue

        # Single-amount line (some banks show one amount column with Dr/Cr indicator)
        m2 = re.match(r'^' + DATE_PAT + r'(.{5,60}?)\s+' + AMT_PAT + r'\s*(Dr|CR|Cr|DR)?\s*$', line, re.IGNORECASE)
        if m2:
            dt = parse_date(m2.group(1))
            if not dt: continue
            narration = m2.group(2).strip()
            amount    = clean_amount(m2.group(3))
            dr_cr_raw = (m2.group(4) or '').upper()
            dr_cr = 'Dr' if 'DR' in dr_cr_raw else ('Cr' if 'CR' in dr_cr_raw else _guess_dr_cr(narration))
            if amount == 0: continue
            txns.append({'date': dt, 'narration': narration, 'amount': amount, 'dr_cr': dr_cr, 'source': 'bank'})

    return txns


def _guess_dr_cr(narration: str) -> str:
    n = narration.upper()
    if any(x in n for x in ['PAYMENT','DEBIT','DR','TRANSFER OUT','WITHDRAWAL','NEFT OUT','IMPS OUT','UPI OUT','EMI','CHARGES']): return 'Dr'
    if any(x in n for x in ['RECEIPT','CREDIT','CR','TRANSFER IN','DEPOSIT','NEFT IN','IMPS IN','UPI IN','SALARY','INTEREST']): return 'Cr'
    return 'Dr'


# ── ICICI ─────────────────────────────────────────────────────────────────────
def _parse_icici(rows, text):
    """
    ICICI text layout (actual format seen in real PDFs):
    Each transaction appears as:
      [Party Name line]
      [S.No.] [DD.MM.YYYY] [optional ChequeNo] [Amount] [Balance]
      [Narration detail lines...]

    Dr/Cr determined by balance movement (balance up = Credit, down = Debit).
    Date format: DD.MM.YYYY
    """
    txns = []
    lines = text.split('\n')

    # Pattern: serial_no  DD.MM.YYYY  [optional cheque]  amount  balance
    TXN_LINE = re.compile(
        r'^\s*(\d{1,4})\s+(\d{2}\.\d{2}\.\d{4})\s+(?:\d+\s+)?([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*$'
    )
    # Skip lines
    SKIP = re.compile(r'S\s*No\.|Transaction|Withdrawal|Deposit|Balance|Statement of|AJAY KUMAR|ICICI BANK|WEST BENGAL|BALLYGUNGE|ASHUTOSH', re.IGNORECASE)

    prev_balance = None
    prev_line    = ''
    last_balance = None   # will be closing balance

    for i, line in enumerate(lines):
        line = line.strip()
        m = TXN_LINE.match(line)
        if not m:
            prev_line = line
            continue

        date_str    = m.group(2)          # DD.MM.YYYY
        amount      = clean_amount(m.group(3))
        balance     = clean_amount(m.group(4))

        # Convert DD.MM.YYYY → date
        dt = None
        try:
            dt = datetime.strptime(date_str, '%d.%m.%Y').date()
        except:
            prev_line = line
            continue

        # Dr or Cr based on balance movement
        if prev_balance is not None:
            dr_cr = 'Cr' if balance > prev_balance else 'Dr'
        else:
            dr_cr = 'Dr'  # fallback

        # Narration = party name (line before) + detail lines after
        party = prev_line if prev_line and not SKIP.search(prev_line) else ''
        # Grab next 1-2 lines as detail
        detail_parts = []
        for j in range(i+1, min(i+3, len(lines))):
            nxt = lines[j].strip()
            if TXN_LINE.match(nxt): break
            if nxt and not SKIP.search(nxt) and not nxt.lower() in ('debit trxn','fund transfer','debit transaction'):
                detail_parts.append(nxt)
        narration = party + (' / ' if party and detail_parts else '') + ' '.join(detail_parts[:1])
        narration = narration.strip()[:100]

        prev_balance = balance
        last_balance = balance  # track last seen balance
        prev_line    = line

        if amount == 0: continue
        txns.append({'date': dt, 'narration': narration or date_str,
                     'amount': amount, 'dr_cr': dr_cr, 'source': 'bank'})
    return txns, last_balance


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

def parse_tally_ledger(filepath: str):
    ext = filepath.lower()

    # Read raw to find header row
    if ext.endswith('.csv'):
        raw = pd.read_csv(filepath, header=None)
    else:
        raw = pd.read_excel(filepath, header=None)

    # Find header row (contains 'Date' and 'Debit' or 'Credit')
    hrow = 0
    for i, row in raw.iterrows():
        vals = ' '.join(str(v).upper() for v in row if pd.notna(v))
        if re.search(r'\bDATE\b', vals) and re.search(r'(DEBIT|CREDIT)', vals):
            hrow = i; break

    # Re-read with correct header
    if ext.endswith('.csv'):
        df = pd.read_csv(filepath, header=hrow)
    else:
        df = pd.read_excel(filepath, header=hrow)

    # Tally ledger specific format:
    # Col 0 = Date, Col 1 = Dr/Cr indicator, Col 2 = Particulars,
    # Col 7 = Debit amount, Col 8 = Credit amount (typical Tally export)
    cols = list(df.columns)
    txns = []
    tally_closing_balance = None
    tally_closing_dr_cr   = None

    for _, row in df.iterrows():
        # Date
        date_val = row.iloc[0]
        if pd.isna(date_val): continue
        if hasattr(date_val, 'date'):
            dt = date_val.date()
        else:
            dt = parse_date(str(date_val))
        if not dt: continue

        # Particulars / narration — column 2 (index 2)
        narration = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else ''
        if not narration or narration == 'nan':
            continue

        # Capture Closing Balance row before skipping
        if narration in ('Closing Balance', 'Opening Balance'):
            if narration == 'Closing Balance':
                # Extract amount from debit/credit columns
                cb_debit = cb_credit = 0.0
                for ci, col in enumerate(cols):
                    col_u = str(col).upper()
                    val   = row.iloc[ci]
                    if pd.isna(val): continue
                    amt = clean_amount(val)
                    if 'DEBIT' in col_u and amt:  cb_debit  = amt
                    if 'CREDIT' in col_u and amt: cb_credit = amt
                if cb_debit == 0 and cb_credit == 0 and len(row) > 8:
                    cb_debit  = clean_amount(row.iloc[7])
                    cb_credit = clean_amount(row.iloc[8])
                if cb_debit:
                    tally_closing_balance = cb_debit
                    tally_closing_dr_cr   = 'Dr'
                elif cb_credit:
                    tally_closing_balance = cb_credit
                    tally_closing_dr_cr   = 'Cr'
            continue  # skip Opening/Closing Balance rows from txns

        # Dr/Cr indicator in col 1
        drcr_raw = str(row.iloc[1]).strip().upper() if len(row) > 1 and pd.notna(row.iloc[1]) else ''

        # Amounts — find debit and credit columns dynamically
        debit = credit = 0.0
        for ci, col in enumerate(cols):
            col_u = str(col).upper()
            val   = row.iloc[ci]
            if pd.isna(val): continue
            amt = clean_amount(val)
            if 'DEBIT' in col_u and amt: debit  = amt
            if 'CREDIT' in col_u and amt: credit = amt

        # Fallback: use Dr/Cr indicator + whichever amount is non-zero
        if debit == 0 and credit == 0:
            # Try raw positional (col 7 = debit, col 8 = credit for Tally export)
            if len(row) > 7: debit  = clean_amount(row.iloc[7])
            if len(row) > 8: credit = clean_amount(row.iloc[8])

        amount = debit if debit else credit
        if amount == 0: continue

        # Determine Dr/Cr
        if drcr_raw in ('DR', 'DR.'):
            dr_cr = 'Dr'
        elif drcr_raw in ('CR', 'CR.'):
            dr_cr = 'Cr'
        else:
            dr_cr = 'Dr' if debit else 'Cr'

        txns.append({'date': dt, 'narration': narration, 'amount': amount,
                     'dr_cr': dr_cr, 'source': 'tally'})
    return txns, tally_closing_balance, tally_closing_dr_cr


# ══════════════════════════════════════════════════════════════════════════════
# MATCHING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def reconcile(bank_txns: List[Dict], tally_txns: List[Dict],
              closing_balance_bank=None, closing_balance_tally=None,
              closing_dr_cr_tally=None) -> Dict:
    matched    = []
    bank_only  = []
    tally_only = []
    duplicates = []

    # Bank statement: NO duplicate detection — every bank line is a real unique
    # transaction. Same party, same amount, same date = two real payments.
    bank_clean = bank_txns

    # Tally duplicate detection:
    # Step 1 — find Tally entries with identical date + amount + exact narration
    # Step 2 — cross-check bank: count how many times that date+amount appears
    #           in bank statement (±1 day). If bank count >= Tally count, it is
    #           NOT a duplicate — both entries are real. Only flag as duplicate
    #           if Tally has MORE occurrences than the bank has.
    from collections import Counter

    # Count occurrences in bank by (date, amount)
    bank_count = Counter((t['date'], round(t['amount'], 2)) for t in bank_txns)

    # Group Tally entries by (date, amount, exact narration)
    tally_groups = {}
    for t in tally_txns:
        key = (t['date'], round(t['amount'], 2), str(t['narration']).upper().strip())
        tally_groups.setdefault(key, []).append(t)

    tally_dupes = []
    tally_clean = []
    for key, entries in tally_groups.items():
        date, amt, _ = key
        bank_occurrences = bank_count.get((date, amt), 0)
        # Also check ±1 day in bank
        from datetime import timedelta
        bank_occurrences = max(
            bank_occurrences,
            bank_count.get((date - timedelta(days=1), amt), 0),
            bank_count.get((date + timedelta(days=1), amt), 0),
        )
        real_count = max(bank_occurrences, 1)  # at least 1 is always real
        # First `real_count` entries are real, rest are duplicates
        for i, entry in enumerate(entries):
            if i < real_count:
                tally_clean.append(entry)
            else:
                tally_dupes.append({
                    **entry,
                    'duplicate_of': entries[0]['narration'],
                    'in': 'Tally',
                    'issue': f"Duplicate entry in Tally — bank has {real_count} occurrence(s) but Tally has {len(entries)}",
                })

    duplicates = tally_dupes

    # Match bank vs tally (date ±1 day, amount within Rs.1)
    tally_used = [False] * len(tally_clean)
    amount_mismatches = []   # matched entries where amount differs by paise

    for bt in bank_clean:
        found = False
        for j, tt in enumerate(tally_clean):
            if tally_used[j]: continue
            date_diff = abs((bt['date'] - tt['date']).days)
            amt_diff  = round(bt['amount'] - tt['amount'], 2)
            amt_match = abs(amt_diff) < 1.0  # allow Rs.1 rounding
            if date_diff <= 1 and amt_match:
                entry = {
                    'date':           str(bt['date']),
                    'bank_narration': bt['narration'],
                    'tally_narration':tt['narration'],
                    'bank_amount':    round(bt['amount'], 2),
                    'tally_amount':   round(tt['amount'], 2),
                    'amount':         bt['amount'],
                    'dr_cr':          bt['dr_cr'],
                    'date_diff':      date_diff,
                    'amt_diff':       amt_diff,
                }
                matched.append(entry)
                # Track paise-level mismatches within matched entries
                if abs(amt_diff) >= 0.01:
                    amount_mismatches.append({
                        'date':           str(bt['date']),
                        'narration':      bt['narration'],
                        'bank_amount':    round(bt['amount'], 2),
                        'tally_amount':   round(tt['amount'], 2),
                        'difference':     amt_diff,          # positive = bank higher
                        'dr_cr':          bt['dr_cr'],
                        'issue':          f"Paise difference: Bank ₹{bt['amount']:.2f} vs Tally ₹{tt['amount']:.2f} (diff ₹{amt_diff:+.2f})",
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

    # ── Wrong date detection ──────────────────────────────────────────────────
    # Bank is ground truth. For each bank_only entry, check if same amount exists
    # in tally_only — if yes, the entry exists in Tally but with a wrong date.
    wrong_date = []
    tally_only_used = [False] * len(tally_only)
    remaining_bank_only = []

    for bo in bank_only:
        found_wrong = False
        for k, to in enumerate(tally_only):
            if tally_only_used[k]: continue
            amt_match = abs(bo['amount'] - to['amount']) < 1.0
            if amt_match:
                wrong_date.append({
                    'bank_date':      bo['date'],
                    'tally_date':     to['date'],
                    'narration':      bo['narration'],
                    'tally_narration':to['narration'],
                    'amount':         bo['amount'],
                    'dr_cr':          bo['dr_cr'],
                    'issue':          f"Entry exists in Tally but with WRONG DATE — Bank: {bo['date']} | Tally: {to['date']} → Fix date in Tally",
                })
                tally_only_used[k] = True
                found_wrong = True
                break
        if not found_wrong:
            remaining_bank_only.append(bo)

    # Remaining tally_only (not matched by amount to any bank_only)
    remaining_tally_only = [to for k, to in enumerate(tally_only) if not tally_only_used[k]]

    # Closing balance comparison
    cb_bank   = round(closing_balance_bank,   2) if closing_balance_bank   is not None else None
    cb_tally  = round(closing_balance_tally,  2) if closing_balance_tally  is not None else None
    cb_diff   = round(abs(cb_bank - cb_tally), 2) if (cb_bank is not None and cb_tally is not None) else None
    cb_match  = (cb_diff is not None and cb_diff < 1.0)   # within Re.1 = match

    # Total paise difference explained by amount mismatches
    total_paise_diff = round(sum(m['difference'] for m in amount_mismatches), 2)

    return {
        'matched':          matched,
        'bank_only':        remaining_bank_only,
        'tally_only':       remaining_tally_only,
        'duplicates':       dupes_out,
        'wrong_date':       wrong_date,
        'amount_mismatches':amount_mismatches,
        'summary': {
            'total_bank':        len(bank_txns),
            'total_tally':       len(tally_txns),
            'matched':           len(matched),
            'bank_only':         len(remaining_bank_only),
            'tally_only':        len(remaining_tally_only),
            'duplicates':        len(dupes_out),
            'wrong_date':        len(wrong_date),
            'amount_mismatches': len(amount_mismatches),
            'total_paise_diff':  total_paise_diff,
            'match_pct':         round(len(matched) / max(len(bank_txns), 1) * 100, 1),
            'closing_balance_bank':  cb_bank,
            'closing_balance_tally': cb_tally,
            'closing_dr_cr_tally':   closing_dr_cr_tally,
            'closing_balance_diff':  cb_diff,
            'closing_balance_match': cb_match,
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def run_bankrec(bank_path: str, tally_path: str, bank_filename: str = '') -> Dict:
    # Parse bank statement
    ext = bank_filename.lower() if bank_filename else bank_path.lower()
    closing_balance_bank = None
    if ext.endswith('.pdf'):
        bank_txns, closing_balance_bank = parse_pdf_statement(bank_path)
        if not bank_txns:
            raise ValueError("Could not extract transactions from PDF. Make sure it's a digital (not scanned) bank statement.")
    else:
        bank_txns = parse_csv_excel_statement(bank_path)

    if not bank_txns:
        raise ValueError("No transactions found in bank statement. Please check the file format.")

    # Parse tally ledger
    tally_txns, closing_balance_tally, closing_dr_cr_tally = parse_tally_ledger(tally_path)
    if not tally_txns:
        raise ValueError("No transactions found in Tally ledger. Please check the file format.")

    return reconcile(bank_txns, tally_txns, closing_balance_bank, closing_balance_tally, closing_dr_cr_tally)
