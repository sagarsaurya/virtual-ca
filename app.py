from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, tempfile, datetime

# Load .env file if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from audit_engine import run_full_audit
from bankrec_engine import run_bankrec
import supabase_client as sb

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Local temp paths — used during request only, then uploaded to Supabase
CURRENT_TB     = os.path.join(DATA_DIR, 'current_tb.xlsx')
CURRENT_DB     = os.path.join(DATA_DIR, 'current_db.xlsx')
CURRENT_BS     = os.path.join(DATA_DIR, 'current_bs.xlsx')
CURRENT_PNL    = os.path.join(DATA_DIR, 'current_pnl.xlsx')
CURRENT_BSTMT  = os.path.join(DATA_DIR, 'current_bank_stmt.xlsx')
CURRENT_BTALLY = os.path.join(DATA_DIR, 'current_bank_tally.xlsx')

def _ensure_local(remote_name, local_path):
    """Download from Supabase if local copy missing."""
    if not os.path.exists(local_path):
        sb.download_file(remote_name, local_path)
    return os.path.exists(local_path)

# ── helpers — now Supabase-backed ─────────────────────────────────────────────
def load_personal():
    return sb.load_personal()

def save_personal(marks):
    pass  # handled individually via save_personal_mark / delete_personal_mark

def load_history():
    return sb.load_history()

def save_history(h):
    pass  # handled individually via save_history_entry

def load_files_meta():
    return sb.load_files_meta()

def save_files_meta(m):
    sb.save_files_meta(m)

def compute_score(results):
    critical = (
        sum(1 for f in results['ledger_classification'] if f['severity'] == 'Critical') +
        len(results['cash_violations']) +
        sum(1 for f in results['outstanding'] if f['severity'] == 'Critical')
    )
    warnings = (
        sum(1 for f in results['ledger_classification'] if f['severity'] == 'Review') +
        sum(1 for f in results['outstanding'] if f['severity'] == 'Review')
    )
    questions = len(results['loans']) + len(results['large_expenses'])
    score = max(0, 100 - (critical * 5) - (warnings * 2) - (questions * 1))
    return score, critical, warnings, questions

# ── static ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ── POST /api/upload/files ────────────────────────────────────────────────────
@app.route('/api/upload/files', methods=['POST'])
def upload_files():
    """
    Saves Trial Balance and/or Daybook permanently on the server.
    Either or both files can be sent in a single request.
    Returns current file status after saving.
    """
    meta = load_files_meta()
    saved = []

    tb_file = request.files.get('trial_balance')
    if tb_file and tb_file.filename:
        tb_file.save(CURRENT_TB)
        sb.upload_file(CURRENT_TB, 'current_tb.xlsx')
        meta['tb'] = {
            'filename':    tb_file.filename,
            'uploaded_at': datetime.datetime.now().isoformat(),
            'size':        os.path.getsize(CURRENT_TB),
        }
        saved.append('trial_balance')

    db_file = request.files.get('daybook')
    if db_file and db_file.filename:
        db_file.save(CURRENT_DB)
        sb.upload_file(CURRENT_DB, 'current_db.xlsx')
        meta['db'] = {
            'filename':    db_file.filename,
            'uploaded_at': datetime.datetime.now().isoformat(),
            'size':        os.path.getsize(CURRENT_DB),
        }
        saved.append('daybook')

    if not saved:
        return jsonify({'error': 'No files received'}), 400

    save_files_meta(meta)
    return jsonify({'saved': saved, 'status': meta})


# ── GET /api/files/status ─────────────────────────────────────────────────────
@app.route('/api/files/status', methods=['GET'])
def files_status():
    """Returns what files are currently saved on the server."""
    meta = load_files_meta()
    # Existence = file was uploaded (tracked in meta), not local disk presence
    meta['tb_exists']    = bool(meta.get('tb'))
    meta['db_exists']    = bool(meta.get('db'))
    meta['bs_exists']    = bool(meta.get('bs'))
    meta['pnl_exists']   = bool(meta.get('pnl'))
    meta['bstmt_exists'] = bool(meta.get('bstmt'))
    meta['btally_exists']= bool(meta.get('btally'))
    meta['bank_stmt_name']  = meta.get('bstmt', {}).get('filename', '')
    meta['bank_tally_name'] = meta.get('btally', {}).get('filename', '')
    return jsonify(meta)


# ── POST /api/audit ───────────────────────────────────────────────────────────
@app.route('/api/audit', methods=['POST'])
def run_audit():
    tb_file = request.files.get('trial_balance')
    db_file = request.files.get('daybook')

    # ── use newly uploaded files, or fall back to saved files ──
    tb_path  = None
    db_path  = None
    tb_name  = ''
    tmp_tb   = None
    tmp_db   = None

    meta = load_files_meta()

    if tb_file and tb_file.filename:
        tb_file.save(CURRENT_TB)
        sb.upload_file(CURRENT_TB, 'current_tb.xlsx')
        meta['tb'] = {'filename': tb_file.filename,
                      'uploaded_at': datetime.datetime.now().isoformat(),
                      'size': os.path.getsize(CURRENT_TB)}
        save_files_meta(meta)
        tb_path = CURRENT_TB
        tb_name = tb_file.filename
    elif _ensure_local('current_tb.xlsx', CURRENT_TB):
        tb_path = CURRENT_TB
        tb_name = meta.get('tb', {}).get('filename', 'trial_balance.xlsx')
    else:
        return jsonify({'error': 'No Trial Balance uploaded. Please upload a file first.'}), 400

    if db_file and db_file.filename:
        db_file.save(CURRENT_DB)
        sb.upload_file(CURRENT_DB, 'current_db.xlsx')
        meta['db'] = {'filename': db_file.filename,
                      'uploaded_at': datetime.datetime.now().isoformat(),
                      'size': os.path.getsize(CURRENT_DB)}
        save_files_meta(meta)
        db_path = CURRENT_DB
    elif _ensure_local('current_db.xlsx', CURRENT_DB):
        db_path = CURRENT_DB
    else:
        db_path = None

    try:
        results = run_full_audit(tb_path, db_path)

        personal_marks = load_personal()
        results['cash_violations'] = [
            v for v in results['cash_violations']
            if not any(m['date'] == v['date'] and m['party'] == v['party'] for m in personal_marks)
        ]
        results['large_expenses'] = [
            e for e in results['large_expenses']
            if not any(m['date'] == e['date'] and m['party'] == e['party'] for m in personal_marks)
        ]
        results['personal_marks'] = personal_marks

        score, critical, warnings, questions = compute_score(results)
        results['summary']['score']     = score
        results['summary']['critical']  = critical
        results['summary']['warnings']  = warnings
        results['summary']['questions'] = questions
        results['tb_filename']          = tb_name
        results['audited_at']           = datetime.datetime.now().isoformat()

        sb.save_audit_result(results)
        sb.save_history_entry({
            'filename':   tb_name,
            'audited_at': results['audited_at'],
            'company':    results['summary'].get('company', ''),
            'period':     results['summary'].get('period', ''),
            'score':      score,
            'critical':   critical,
            'warnings':   warnings,
            'questions':  questions,
        })

        return jsonify(results)

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ── GET /api/audit/last ───────────────────────────────────────────────────────
@app.route('/api/audit/last', methods=['GET'])
def last_audit():
    data = sb.load_audit_result()
    if data:
        s = data.get('summary', {})
        if (s.get('critical', 0) == 0 and s.get('warnings', 0) == 0
                and s.get('questions', 0) == 0 and s.get('score', 0) == 0
                and sb.load_files_meta().get('tb')):
            data['_stale_warning'] = 'Saved result shows 0 issues — please re-run audit to get fresh results.'
        return jsonify(data)
    return jsonify({'error': 'No audit run yet'}), 404

# ── DELETE /api/audit/clear ───────────────────────────────────────────────────
@app.route('/api/audit/clear', methods=['POST'])
def clear_audit():
    sb.save_audit_result({})
    return jsonify({'ok': True})

# ── GET /api/audit/history ────────────────────────────────────────────────────
@app.route('/api/audit/history', methods=['GET'])
def audit_history():
    return jsonify(load_history())

# ── GET /api/dashboard ────────────────────────────────────────────────────────
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    history = load_history()
    last    = sb.load_audit_result() or {}
    return jsonify({
        'total_audits': len(history),
        'last_score':   last.get('summary', {}).get('score'),
        'last_critical':last.get('summary', {}).get('critical'),
        'last_warnings':last.get('summary', {}).get('warnings'),
        'recent':       history[:3],
        'company':      last.get('summary', {}).get('company', ''),
        'period':       last.get('summary', {}).get('period', ''),
    })

# ── GET /api/compliance ───────────────────────────────────────────────────────
@app.route('/api/compliance', methods=['GET'])
def compliance():
    today = datetime.date.today()
    year  = today.year
    month = today.month

    items = []

    # TDS deposit — 7th of next month
    tds_month = month + 1 if month < 12 else 1
    tds_year  = year if month < 12 else year + 1
    tds_due   = datetime.date(tds_year, tds_month, 7)
    diff      = (tds_due - today).days
    items.append({
        'title': f'TDS Deposit — {tds_due.strftime("%B %Y")}',
        'due':   tds_due.isoformat(),
        'days':  diff,
        'status': 'overdue' if diff < 0 else ('upcoming' if diff <= 7 else 'ok'),
        'note':  'Sec 200 — deposit by 7th of following month',
        'category': 'TDS',
    })

    # PT Kolkata — 21st of current month
    pt_due  = datetime.date(year, month, 21)
    if pt_due < today:
        pt_due = datetime.date(year if month < 12 else year+1, month+1 if month < 12 else 1, 21)
    diff = (pt_due - today).days
    items.append({
        'title': f'PT Deposit (WB) — {pt_due.strftime("%B %Y")}',
        'due':   pt_due.isoformat(),
        'days':  diff,
        'status': 'overdue' if diff < 0 else ('upcoming' if diff <= 7 else 'ok'),
        'note':  'Deposit via GRIPS portal by 21st',
        'category': 'PT',
    })

    # GSTR-3B — 20th of next month
    gst_month = month + 1 if month < 12 else 1
    gst_year  = year if month < 12 else year + 1
    gst_due   = datetime.date(gst_year, gst_month, 20)
    diff      = (gst_due - today).days
    items.append({
        'title': f'GSTR-3B — {gst_due.strftime("%B %Y")}',
        'due':   gst_due.isoformat(),
        'days':  diff,
        'status': 'overdue' if diff < 0 else ('upcoming' if diff <= 7 else 'ok'),
        'note':  'Monthly GST return + payment',
        'category': 'GST',
    })

    # Advance Tax — quarterly
    adv_dates = [
        datetime.date(year, 6, 15),
        datetime.date(year, 9, 15),
        datetime.date(year, 12, 15),
        datetime.date(year+1, 3, 15),
    ]
    for d in adv_dates:
        if d >= today:
            diff = (d - today).days
            items.append({
                'title': f'Advance Tax — {d.strftime("%d %b %Y")}',
                'due':   d.isoformat(),
                'days':  diff,
                'status': 'ok' if diff > 30 else ('upcoming' if diff <= 30 else 'overdue'),
                'note':  '15% / 45% / 75% / 100% cumulative',
                'category': 'Income Tax',
            })
            break

    # ITR Filing
    itr_due = datetime.date(year if month <= 7 else year+1, 7, 31)
    diff = (itr_due - today).days
    items.append({
        'title': f'ITR Filing — {itr_due.strftime("%d %b %Y")}',
        'due':   itr_due.isoformat(),
        'days':  diff,
        'status': 'overdue' if diff < 0 else ('upcoming' if diff <= 30 else 'ok'),
        'note':  'Individual / business ITR deadline',
        'category': 'Income Tax',
    })

    items.sort(key=lambda x: x['due'])
    return jsonify(items)

# ── mark/unmark personal ──────────────────────────────────────────────────────
@app.route('/api/audit/mark-personal', methods=['POST'])
def mark_personal():
    data  = request.json
    marks = load_personal()
    entry = {'date': data['date'], 'party': data['party'], 'amount': data['amount'], 'reason': data.get('reason', 'Personal')}
    if not any(m['date'] == entry['date'] and m['party'] == entry['party'] for m in marks):
        sb.save_personal_mark(entry)
    return jsonify({'success': True, 'total_marks': len(marks) + 1})

@app.route('/api/audit/mark-personal', methods=['DELETE'])
def unmark_personal():
    data = request.json
    sb.delete_personal_mark(data['date'], data['party'])
    return jsonify({'success': True})

@app.route('/api/audit/personal-marks', methods=['GET'])
def get_personal_marks():
    return jsonify(load_personal())

# ── POST /api/bankrec-existing ────────────────────────────────────────────────
@app.route('/api/bankrec-existing', methods=['POST'])
def bank_reconciliation_existing():
    """Run bank recon using already-saved bank files (no re-upload needed)."""
    meta = load_files_meta()
    if not meta.get('bstmt'):
        return jsonify({'error': 'No bank statement uploaded yet. Upload files first.'}), 400

    bs_ok = _ensure_local('current_bank_stmt.xlsx', CURRENT_BSTMT)
    if not bs_ok:
        return jsonify({'error': 'Bank statement file not found. Please re-upload.'}), 400

    tl_path     = None
    tl_filename = ''
    if meta.get('btally') and _ensure_local('current_bank_tally.xlsx', CURRENT_BTALLY):
        tl_path     = CURRENT_BTALLY
        tl_filename = meta['btally'].get('filename', 'tally_ledger.xlsx')
    elif _ensure_local('current_db.xlsx', CURRENT_DB):
        tl_path     = CURRENT_DB
        tl_filename = meta.get('db', {}).get('filename', 'daybook.xlsx')
    else:
        return jsonify({'error': 'No Tally ledger or Daybook found. Upload files first.'}), 400

    try:
        result = run_bankrec(CURRENT_BSTMT, tl_path, meta['bstmt'].get('filename', 'bank_statement.xlsx'))
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /api/bankrec ─────────────────────────────────────────────────────────
@app.route('/api/bankrec', methods=['POST'])
def bank_reconciliation():
    bs_file = request.files.get('bank_statement')
    tl_file = request.files.get('tally_ledger')

    if not bs_file or not bs_file.filename:
        return jsonify({'error': 'bank_statement file is required'}), 400

    # tally_ledger: use uploaded file OR fall back to saved daybook
    bs_ext = os.path.splitext(bs_file.filename)[1] or '.pdf'
    with tempfile.NamedTemporaryFile(suffix=bs_ext, delete=False) as tmp:
        bs_path = tmp.name; bs_file.save(bs_path)

    tl_path     = None
    tmp_tl      = None
    tl_filename = ''

    # Save bank stmt to Supabase
    sb.upload_file(bs_path, 'current_bank_stmt.xlsx')
    meta = load_files_meta()
    meta['bstmt'] = {'filename': bs_file.filename, 'uploaded_at': datetime.datetime.now().isoformat()}
    save_files_meta(meta)

    if tl_file and tl_file.filename:
        tl_ext = os.path.splitext(tl_file.filename)[1] or '.xlsx'
        with tempfile.NamedTemporaryFile(suffix=tl_ext, delete=False) as tmp:
            tl_path = tmp.name; tl_file.save(tl_path)
            tmp_tl  = tl_path
        sb.upload_file(tl_path, 'current_bank_tally.xlsx')
        meta['btally'] = {'filename': tl_file.filename, 'uploaded_at': datetime.datetime.now().isoformat()}
        save_files_meta(meta)
        tl_filename = tl_file.filename
    elif _ensure_local('current_db.xlsx', CURRENT_DB):
        tl_path     = CURRENT_DB
        tl_filename = load_files_meta().get('db', {}).get('filename', 'daybook.xlsx')
    else:
        os.unlink(bs_path)
        return jsonify({'error': 'No Daybook uploaded. Upload it here or via the Upload page first.'}), 400

    try:
        result = run_bankrec(bs_path, tl_path, bs_file.filename)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        os.unlink(bs_path)
        if tmp_tl and os.path.exists(tmp_tl): os.unlink(tmp_tl)

# ── POST /api/ca-chat ─────────────────────────────────────────────────────────
@app.route('/api/ca-chat', methods=['POST'])
def ca_chat():
    data        = request.json or {}
    user_msg    = data.get('message', '').strip()
    history     = data.get('history', [])   # [{role, content}, ...]

    if not user_msg:
        return jsonify({'error': 'message required'}), 400

    audit_data = sb.load_audit_result() or None

    try:
        from ca_agent import chat as ca_chat_fn
        reply = ca_chat_fn(user_msg, audit_data, history)
        return jsonify({'reply': reply})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /api/full-audit ──────────────────────────────────────────────────────
@app.route('/api/full-audit', methods=['POST'])
def run_full_audit_all():
    """
    Full Audit — accepts BS + P&L uploads, auto-pulls TB/DB/bank files.
    Runs all 9 existing modules + BS/P&L compliance modules.
    """
    meta = load_files_meta()

    # Save BS if uploaded
    bs_file = request.files.get('balance_sheet')
    if bs_file and bs_file.filename:
        bs_ext = os.path.splitext(bs_file.filename)[1] or '.xlsx'
        bs_save = CURRENT_BS if bs_ext in ('.xlsx','.xls') else CURRENT_BS.replace('.xlsx', bs_ext)
        bs_file.save(CURRENT_BS)
        meta['bs'] = {'filename': bs_file.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(CURRENT_BS)}

    # Save P&L if uploaded
    pnl_file = request.files.get('pnl')
    if pnl_file and pnl_file.filename:
        pnl_file.save(CURRENT_PNL)
        meta['pnl'] = {'filename': pnl_file.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(CURRENT_PNL)}

    save_files_meta(meta)

    # Ensure local copies (download from Supabase if needed)
    if not _ensure_local('current_tb.xlsx', CURRENT_TB):
        return jsonify({'error': 'Trial Balance not found. Run Quick Audit first to upload TB + Daybook.'}), 400
    if not _ensure_local('current_db.xlsx', CURRENT_DB):
        return jsonify({'error': 'Daybook not found. Run Quick Audit first to upload TB + Daybook.'}), 400

    try:
        from audit_engine import run_full_audit
        results = run_full_audit(CURRENT_TB, CURRENT_DB)

        # Apply personal marks
        personal_marks = load_personal()
        results['cash_violations'] = [
            v for v in results['cash_violations']
            if not any(m['date'] == v['date'] and m['party'] == v['party'] for m in personal_marks)
        ]
        results['large_expenses'] = [
            e for e in results['large_expenses']
            if not any(m['date'] == e['date'] and m['party'] == e['party'] for m in personal_marks)
        ]

        # Run BS + P&L audit if files present
        bs_findings   = []
        pnl_findings  = []
        bankrec_result = None

        if os.path.exists(CURRENT_BS) or os.path.exists(CURRENT_PNL):
            try:
                from bs_pnl_audit import audit_bs_pnl
                bs_findings, pnl_findings = audit_bs_pnl(
                    CURRENT_BS   if os.path.exists(CURRENT_BS)    else None,
                    CURRENT_PNL  if os.path.exists(CURRENT_PNL)   else None,
                    results,
                )
            except Exception as e:
                bs_findings  = [{'type': 'error', 'message': f'BS/P&L audit error: {e}', 'severity': 'Info'}]

        # Run bank recon if files present + cross-check cash violations against bank statement
        if _ensure_local('current_bank_stmt.xlsx', CURRENT_BSTMT):
            try:
                from bankrec_engine import run_bankrec, parse_bank_statement
                _ensure_local('current_bank_tally.xlsx', CURRENT_BTALLY)
                tally_path = CURRENT_BTALLY if os.path.exists(CURRENT_BTALLY) else CURRENT_DB
                bstmt_filename = meta.get('bstmt', {}).get('filename', 'bank_statement.xlsx')
                bankrec_result = run_bankrec(CURRENT_BSTMT, tally_path, bstmt_filename)

                # ── Cross-check cash violations against bank statement ──────────
                # If a "cash violation" entry has a matching bank debit (same amount
                # within ±1% and within ±3 days) it was actually paid via bank.
                try:
                    bank_txns = parse_bank_statement(CURRENT_BSTMT, bstmt_filename)
                    bank_debits = [t for t in bank_txns if t.get('dr_cr') in ('Dr', 'Debit', 'DR')]

                    cleared_by_bank = []
                    remaining_violations = []

                    for v in results['cash_violations']:
                        v_amount = float(v.get('amount', 0))
                        v_date   = None
                        try:
                            from datetime import date as dt_date, timedelta
                            v_date = datetime.datetime.strptime(v['date'], '%Y-%m-%d').date() if v.get('date') else None
                        except Exception:
                            pass

                        matched = False
                        for bt in bank_debits:
                            bt_amount = float(bt.get('amount', 0))
                            # Amount match within 1%
                            if bt_amount == 0 or abs(bt_amount - v_amount) / max(bt_amount, v_amount) > 0.01:
                                continue
                            # Date match within ±3 days
                            if v_date and bt.get('date'):
                                try:
                                    bt_date = bt['date'].date() if hasattr(bt['date'], 'date') else bt['date']
                                    if abs((bt_date - v_date).days) <= 3:
                                        matched = True
                                        break
                                except Exception:
                                    pass
                            elif not v_date:
                                matched = True  # no date to compare — give benefit of doubt
                                break

                        if matched:
                            v['_cleared_by_bank'] = True
                            cleared_by_bank.append(v)
                        else:
                            remaining_violations.append(v)

                    results['cash_violations']           = remaining_violations
                    results['cash_violations_bank_cleared'] = cleared_by_bank
                except Exception as e:
                    print(f'[cross-check] bank cross-check error: {e}')

            except Exception as e:
                bankrec_result = {'error': str(e)}

        score, critical, warnings, questions = compute_score(results)
        # Deduct for BS/P&L findings
        for f in bs_findings + pnl_findings:
            if f.get('severity') == 'Critical': critical += 1; score = max(0, score - 5)
            elif f.get('severity') == 'Review':  warnings += 1; score = max(0, score - 2)

        results['summary']['score']     = score
        results['summary']['critical']  = critical
        results['summary']['warnings']  = warnings
        results['summary']['questions'] = questions
        results['bs_findings']          = bs_findings
        results['pnl_findings']         = pnl_findings
        results['bankrec']              = bankrec_result
        results['audited_at']           = datetime.datetime.now().isoformat()
        results['audit_type']           = 'full'

        sb.save_audit_result(results)
        return jsonify(results)

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /api/upload/bank-files ───────────────────────────────────────────────
@app.route('/api/upload/bank-files', methods=['POST'])
def upload_bank_files():
    """Save bank statement and/or bank tally ledger persistently."""
    meta = load_files_meta()
    saved = []

    bstmt = request.files.get('bank_statement')
    if bstmt and bstmt.filename:
        bstmt.save(CURRENT_BSTMT)
        meta['bstmt'] = {'filename': bstmt.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(CURRENT_BSTMT)}
        saved.append('bank_statement')

    btally = request.files.get('tally_ledger')
    if btally and btally.filename:
        btally.save(CURRENT_BTALLY)
        meta['btally'] = {'filename': btally.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(CURRENT_BTALLY)}
        saved.append('tally_ledger')

    if not saved:
        return jsonify({'error': 'No files received'}), 400

    save_files_meta(meta)
    return jsonify({'saved': saved, 'status': meta})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"VirtualCA backend running on port {port}")
    app.run(host='0.0.0.0', port=port)
