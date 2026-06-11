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

# ── Multi-company helpers ──────────────────────────────────────────────────────
def get_cid() -> int:
    """Get company_id from request header. Defaults to 1."""
    try:
        return int(request.headers.get('X-Company-ID', 1))
    except (ValueError, TypeError):
        return 1

def company_dir(cid: int) -> str:
    """Local temp directory for a company."""
    d = os.path.join(DATA_DIR, f'company_{cid}')
    os.makedirs(d, exist_ok=True)
    return d

def cpath(cid: int, filename: str) -> str:
    """Local file path for a company file."""
    return os.path.join(company_dir(cid), filename)

def rname(cid: int, filename: str) -> str:
    """Remote Supabase storage path for a company file."""
    return f'company_{cid}/{filename}'

def _ensure_local(remote_name, local_path):
    """Download from Supabase if local copy missing."""
    if not os.path.exists(local_path):
        sb.download_file(remote_name, local_path)
    return os.path.exists(local_path)

def _cross_check_bank(violations, bstmt_path, bstmt_filename):
    """Remove cash violations that have a matching debit in the bank statement.
    Returns (remaining, cleared) tuple."""
    try:
        from bankrec_engine import parse_bank_statement
        from datetime import timedelta
        bank_txns  = parse_bank_statement(bstmt_path, bstmt_filename)
        bank_debits = [t for t in bank_txns if t.get('dr_cr') in ('Dr', 'Debit', 'DR')]
    except Exception as e:
        print(f'[cross-check] parse error: {e}')
        return violations, []

    remaining, cleared = [], []
    for v in violations:
        v_amount = float(v.get('amount', 0))
        v_date = None
        try:
            v_date = datetime.datetime.strptime(v['date'], '%Y-%m-%d').date() if v.get('date') else None
        except Exception:
            pass

        matched = False
        for bt in bank_debits:
            bt_amount = float(bt.get('amount', 0))
            if bt_amount == 0 or abs(bt_amount - v_amount) / max(bt_amount, v_amount) > 0.01:
                continue
            if v_date and bt.get('date'):
                try:
                    bt_date = bt['date'].date() if hasattr(bt['date'], 'date') else bt['date']
                    if abs((bt_date - v_date).days) <= 3:
                        matched = True; break
                except Exception:
                    pass
            elif not v_date:
                matched = True; break

        if matched:
            v['_cleared_by_bank'] = True
            cleared.append(v)
        else:
            remaining.append(v)

    return remaining, cleared


# ── helpers — now Supabase-backed (all cid-aware) ─────────────────────────────
def load_personal(cid=1):
    return sb.load_personal(cid)

def load_history(cid=1):
    return sb.load_history(cid)

def load_files_meta(cid=1):
    return sb.load_files_meta(cid)

def save_files_meta(m, cid=1):
    sb.save_files_meta(m, cid)

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
@app.route('/api/companies', methods=['GET'])
def get_companies():
    return jsonify(sb.load_companies())

@app.route('/api/companies', methods=['POST'])
def add_company():
    name = (request.json or {}).get('name', '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400
    co = sb.create_company(name)
    return jsonify(co)

@app.route('/api/companies/<int:cid>', methods=['DELETE'])
def del_company(cid):
    if cid == 1:
        return jsonify({'error': 'Cannot delete default company'}), 400
    sb.delete_company(cid)
    return jsonify({'ok': True})

@app.route('/api/companies/<int:cid>/rename', methods=['POST'])
def rename_company(cid):
    name = (request.json or {}).get('name', '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400
    sb.rename_company(cid, name)
    return jsonify({'ok': True})


@app.route('/api/upload/files', methods=['POST'])
def upload_files():
    cid  = get_cid()
    meta = load_files_meta(cid)
    saved = []

    tb_file = request.files.get('trial_balance')
    if tb_file and tb_file.filename:
        lp = cpath(cid, 'current_tb.xlsx')
        tb_file.save(lp)
        sb.upload_file(lp, rname(cid, 'current_tb.xlsx'))
        meta['tb'] = {'filename': tb_file.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(lp)}
        saved.append('trial_balance')

    db_file = request.files.get('daybook')
    if db_file and db_file.filename:
        lp = cpath(cid, 'current_db.xlsx')
        db_file.save(lp)
        sb.upload_file(lp, rname(cid, 'current_db.xlsx'))
        meta['db'] = {'filename': db_file.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(lp)}
        saved.append('daybook')

    if not saved:
        return jsonify({'error': 'No files received'}), 400

    save_files_meta(meta, cid)
    return jsonify({'saved': saved, 'status': meta})


# ── GET /api/files/status ─────────────────────────────────────────────────────
@app.route('/api/files/status', methods=['GET'])
def files_status():
    cid  = get_cid()
    meta = load_files_meta(cid)
    meta['tb_exists']       = bool(meta.get('tb'))
    meta['db_exists']       = bool(meta.get('db'))
    meta['bs_exists']       = bool(meta.get('bs'))
    meta['pnl_exists']      = bool(meta.get('pnl'))
    meta['bstmt_exists']    = bool(meta.get('bstmt'))
    meta['btally_exists']   = bool(meta.get('btally'))
    meta['bank_stmt_name']  = meta.get('bstmt', {}).get('filename', '')
    meta['bank_tally_name'] = meta.get('btally', {}).get('filename', '')
    return jsonify(meta)


# ── POST /api/audit ───────────────────────────────────────────────────────────
@app.route('/api/audit', methods=['POST'])
def run_audit():
    cid     = get_cid()
    tb_file = request.files.get('trial_balance')
    db_file = request.files.get('daybook')
    meta    = load_files_meta(cid)
    tb_path = db_path = tb_name = None

    if tb_file and tb_file.filename:
        lp = cpath(cid, 'current_tb.xlsx')
        tb_file.save(lp)
        sb.upload_file(lp, rname(cid, 'current_tb.xlsx'))
        meta['tb'] = {'filename': tb_file.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(lp)}
        save_files_meta(meta, cid)
        tb_path = lp; tb_name = tb_file.filename
    else:
        lp = cpath(cid, 'current_tb.xlsx')
        if _ensure_local(rname(cid, 'current_tb.xlsx'), lp):
            tb_path = lp; tb_name = meta.get('tb', {}).get('filename', 'trial_balance.xlsx')
        else:
            return jsonify({'error': 'No Trial Balance uploaded. Please upload a file first.'}), 400

    if db_file and db_file.filename:
        lp = cpath(cid, 'current_db.xlsx')
        db_file.save(lp)
        sb.upload_file(lp, rname(cid, 'current_db.xlsx'))
        meta['db'] = {'filename': db_file.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(lp)}
        save_files_meta(meta, cid)
        db_path = lp
    else:
        lp = cpath(cid, 'current_db.xlsx')
        db_path = lp if _ensure_local(rname(cid, 'current_db.xlsx'), lp) else None

    try:
        results = run_full_audit(tb_path, db_path)

        personal_marks = load_personal(cid)
        results['cash_violations'] = [v for v in results['cash_violations']
            if not any(m['date'] == v['date'] and m['party'] == v['party'] for m in personal_marks)]
        results['large_expenses']  = [e for e in results['large_expenses']
            if not any(m['date'] == e['date'] and m['party'] == e['party'] for m in personal_marks)]
        results['personal_marks']  = personal_marks

        bstmt_lp = cpath(cid, 'current_bank_stmt.xlsx')
        bstmt_found = _ensure_local(rname(cid, 'current_bank_stmt.xlsx'), bstmt_lp)
        # Fallback: try old pre-multi-company path (migration support)
        if not bstmt_found:
            bstmt_found = sb.download_file('current_bank_stmt.xlsx', bstmt_lp)
        if bstmt_found:
            bstmt_fn = load_files_meta(cid).get('bstmt', {}).get('filename', 'bank_statement.xlsx')
            remaining, cleared = _cross_check_bank(results['cash_violations'], bstmt_lp, bstmt_fn)
            results['cash_violations']              = remaining
            results['cash_violations_bank_cleared'] = cleared
            results['bank_crosscheck_status']       = 'done'
        else:
            results['bank_crosscheck_status'] = 'no_bank_statement'

        score, critical, warnings, questions = compute_score(results)
        results['summary']['score']     = score
        results['summary']['critical']  = critical
        results['summary']['warnings']  = warnings
        results['summary']['questions'] = questions
        results['tb_filename']          = tb_name
        results['audited_at']           = datetime.datetime.now().isoformat()

        sb.save_audit_result(results, cid)
        sb.save_history_entry({'filename': tb_name, 'audited_at': results['audited_at'],
            'company': results['summary'].get('company', ''), 'period': results['summary'].get('period', ''),
            'score': score, 'critical': critical, 'warnings': warnings, 'questions': questions}, cid)
        return jsonify(results)

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ── GET /api/audit/last ───────────────────────────────────────────────────────
@app.route('/api/audit/last', methods=['GET'])
def last_audit():
    cid  = get_cid()
    data = sb.load_audit_result(cid)
    if data:
        s = data.get('summary', {})
        if (s.get('critical', 0) == 0 and s.get('warnings', 0) == 0
                and s.get('questions', 0) == 0 and s.get('score', 0) == 0
                and sb.load_files_meta(cid).get('tb')):
            data['_stale_warning'] = 'Saved result shows 0 issues — please re-run audit.'
        return jsonify(data)
    return jsonify({'error': 'No audit run yet'}), 404

@app.route('/api/audit/clear', methods=['POST'])
def clear_audit():
    sb.save_audit_result({}, get_cid())
    return jsonify({'ok': True})

@app.route('/api/audit/history', methods=['GET'])
def audit_history():
    return jsonify(load_history(get_cid()))

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    cid     = get_cid()
    history = load_history(cid)
    last    = sb.load_audit_result(cid) or {}
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
    cid   = get_cid()
    data  = request.json
    marks = load_personal(cid)
    entry = {'date': data['date'], 'party': data['party'], 'amount': data['amount'], 'reason': data.get('reason', 'Personal')}
    if not any(m['date'] == entry['date'] and m['party'] == entry['party'] for m in marks):
        sb.save_personal_mark(entry, cid)
    return jsonify({'success': True, 'total_marks': len(marks) + 1})

@app.route('/api/audit/mark-personal', methods=['DELETE'])
def unmark_personal():
    cid  = get_cid()
    data = request.json
    sb.delete_personal_mark(data['date'], data['party'], cid)
    return jsonify({'success': True})

@app.route('/api/audit/personal-marks', methods=['GET'])
def get_personal_marks():
    return jsonify(load_personal(get_cid()))

# ── POST /api/bankrec-existing ────────────────────────────────────────────────
@app.route('/api/bankrec-existing', methods=['POST'])
def bank_reconciliation_existing():
    cid  = get_cid()
    meta = load_files_meta(cid)
    if not meta.get('bstmt'):
        return jsonify({'error': 'No bank statement uploaded yet. Upload files first.'}), 400
    bstmt_lp  = cpath(cid, 'current_bank_stmt.xlsx')
    if not _ensure_local(rname(cid, 'current_bank_stmt.xlsx'), bstmt_lp):
        return jsonify({'error': 'Bank statement file not found. Please re-upload.'}), 400
    btally_lp = cpath(cid, 'current_bank_tally.xlsx')
    db_lp     = cpath(cid, 'current_db.xlsx')
    if meta.get('btally') and _ensure_local(rname(cid, 'current_bank_tally.xlsx'), btally_lp):
        tl_path = btally_lp
    elif _ensure_local(rname(cid, 'current_db.xlsx'), db_lp):
        tl_path = db_lp
    else:
        return jsonify({'error': 'No Tally ledger or Daybook found.'}), 400
    try:
        return jsonify(run_bankrec(bstmt_lp, tl_path, meta['bstmt'].get('filename', 'bank_statement.xlsx')))
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /api/bankrec ─────────────────────────────────────────────────────────
@app.route('/api/bankrec', methods=['POST'])
def bank_reconciliation():
    cid     = get_cid()
    bs_file = request.files.get('bank_statement')
    tl_file = request.files.get('tally_ledger')
    if not bs_file or not bs_file.filename:
        return jsonify({'error': 'bank_statement file is required'}), 400

    bs_ext = os.path.splitext(bs_file.filename)[1] or '.pdf'
    with tempfile.NamedTemporaryFile(suffix=bs_ext, delete=False) as tmp:
        bs_path = tmp.name; bs_file.save(bs_path)

    meta = load_files_meta(cid)
    sb.upload_file(bs_path, rname(cid, 'current_bank_stmt.xlsx'))
    meta['bstmt'] = {'filename': bs_file.filename, 'uploaded_at': datetime.datetime.now().isoformat()}
    save_files_meta(meta, cid)

    tmp_tl  = None
    db_lp   = cpath(cid, 'current_db.xlsx')
    if tl_file and tl_file.filename:
        tl_ext = os.path.splitext(tl_file.filename)[1] or '.xlsx'
        with tempfile.NamedTemporaryFile(suffix=tl_ext, delete=False) as tmp:
            tl_path = tmp.name; tl_file.save(tl_path); tmp_tl = tl_path
        sb.upload_file(tl_path, rname(cid, 'current_bank_tally.xlsx'))
        meta['btally'] = {'filename': tl_file.filename, 'uploaded_at': datetime.datetime.now().isoformat()}
        save_files_meta(meta, cid)
    elif _ensure_local(rname(cid, 'current_db.xlsx'), db_lp):
        tl_path = db_lp
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

    audit_data = sb.load_audit_result(get_cid()) or None

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
    cid  = get_cid()
    meta = load_files_meta(cid)

    bs_file = request.files.get('balance_sheet')
    if bs_file and bs_file.filename:
        lp = cpath(cid, 'current_bs.xlsx')
        bs_file.save(lp)
        sb.upload_file(lp, rname(cid, 'current_bs.xlsx'))
        meta['bs'] = {'filename': bs_file.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(lp)}

    pnl_file = request.files.get('pnl')
    if pnl_file and pnl_file.filename:
        lp = cpath(cid, 'current_pnl.xlsx')
        pnl_file.save(lp)
        sb.upload_file(lp, rname(cid, 'current_pnl.xlsx'))
        meta['pnl'] = {'filename': pnl_file.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(lp)}

    save_files_meta(meta, cid)

    tb_lp = cpath(cid, 'current_tb.xlsx')
    db_lp = cpath(cid, 'current_db.xlsx')
    if not _ensure_local(rname(cid, 'current_tb.xlsx'), tb_lp):
        return jsonify({'error': 'Trial Balance not found. Run Quick Audit first.'}), 400
    if not _ensure_local(rname(cid, 'current_db.xlsx'), db_lp):
        return jsonify({'error': 'Daybook not found. Run Quick Audit first.'}), 400

    try:
        from audit_engine import run_full_audit
        results = run_full_audit(tb_lp, db_lp)

        personal_marks = load_personal(cid)
        results['cash_violations'] = [v for v in results['cash_violations']
            if not any(m['date'] == v['date'] and m['party'] == v['party'] for m in personal_marks)]
        results['large_expenses']  = [e for e in results['large_expenses']
            if not any(m['date'] == e['date'] and m['party'] == e['party'] for m in personal_marks)]

        bs_findings = pnl_findings = []
        bankrec_result = None
        bs_lp  = cpath(cid, 'current_bs.xlsx')
        pnl_lp = cpath(cid, 'current_pnl.xlsx')
        _ensure_local(rname(cid, 'current_bs.xlsx'),  bs_lp)
        _ensure_local(rname(cid, 'current_pnl.xlsx'), pnl_lp)

        if os.path.exists(bs_lp) or os.path.exists(pnl_lp):
            try:
                from bs_pnl_audit import audit_bs_pnl
                bs_findings, pnl_findings = audit_bs_pnl(
                    bs_lp  if os.path.exists(bs_lp)  else None,
                    pnl_lp if os.path.exists(pnl_lp) else None,
                    results)
            except Exception as e:
                bs_findings = [{'type': 'error', 'message': f'BS/P&L audit error: {e}', 'severity': 'Info'}]

        bstmt_lp  = cpath(cid, 'current_bank_stmt.xlsx')
        btally_lp = cpath(cid, 'current_bank_tally.xlsx')
        if _ensure_local(rname(cid, 'current_bank_stmt.xlsx'), bstmt_lp):
            try:
                _ensure_local(rname(cid, 'current_bank_tally.xlsx'), btally_lp)
                tally_path     = btally_lp if os.path.exists(btally_lp) else db_lp
                bstmt_filename = meta.get('bstmt', {}).get('filename', 'bank_statement.xlsx')
                bankrec_result = run_bankrec(bstmt_lp, tally_path, bstmt_filename)
                remaining, cleared = _cross_check_bank(results['cash_violations'], bstmt_lp, bstmt_filename)
                results['cash_violations']              = remaining
                results['cash_violations_bank_cleared'] = cleared
            except Exception as e:
                bankrec_result = {'error': str(e)}

        score, critical, warnings, questions = compute_score(results)
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

        sb.save_audit_result(results, cid)
        return jsonify(results)

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /api/upload/bank-files ───────────────────────────────────────────────
@app.route('/api/upload/bank-files', methods=['POST'])
def upload_bank_files():
    """Save bank statement and/or bank tally ledger persistently."""
    cid  = get_cid()
    meta = load_files_meta(cid)
    saved = []

    bstmt = request.files.get('bank_statement')
    if bstmt and bstmt.filename:
        lp = cpath(cid, 'current_bank_stmt.xlsx')
        bstmt.save(lp)
        sb.upload_file(lp, rname(cid, 'current_bank_stmt.xlsx'))
        meta['bstmt'] = {'filename': bstmt.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(lp)}
        saved.append('bank_statement')

    btally = request.files.get('tally_ledger')
    if btally and btally.filename:
        lp = cpath(cid, 'current_bank_tally.xlsx')
        btally.save(lp)
        sb.upload_file(lp, rname(cid, 'current_bank_tally.xlsx'))
        meta['btally'] = {'filename': btally.filename, 'uploaded_at': datetime.datetime.now().isoformat(), 'size': os.path.getsize(lp)}
        saved.append('tally_ledger')

    if not saved:
        return jsonify({'error': 'No files received'}), 400

    save_files_meta(meta, cid)
    return jsonify({'saved': saved, 'status': meta})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"VirtualCA backend running on port {port}")
    app.run(host='0.0.0.0', port=port)
