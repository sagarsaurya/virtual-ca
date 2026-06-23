from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os, json, tempfile, datetime

# Load .env file if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from audit_engine import run_full_audit
from ai_audit_engine import run_ai_audit
from bankrec_engine import run_bankrec
import supabase_client as sb

BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'build')
app = Flask(__name__, static_folder=os.path.join(BUILD_DIR, 'static'), static_url_path='/static')
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# ── Auth helpers ──────────────────────────────────────────────────────────────
def _get_token() -> str:
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get('Authorization', '')
    return auth.replace('Bearer ', '').strip()


def get_cid() -> int | None:
    """
    Get company_id for the current request.
    If a valid token is present, ALWAYS use that user's company.
    Never fall back to company 1 when a real token exists.
    Returns None if token is invalid (caller should return 401).
    """
    token = _get_token()
    if token:
        try:
            sb_client = sb.get_client()
            res = sb_client.auth.get_user(token)
            if res.user:
                user_id = res.user.id
                email   = res.user.email
                return sb.get_or_create_company_for_user(user_id, email)
            else:
                return None  # invalid token — don't fall back
        except Exception as e:
            print(f'[Auth] get_cid token error: {e}')
            return None  # error verifying token — don't fall back
    # No token at all — legacy header fallback (admin panel only)
    try:
        return int(request.headers.get('X-Company-ID', 1))
    except (ValueError, TypeError):
        return 1


# ── Auth endpoints ────────────────────────────────────────────────────────────
@app.route('/api/auth/signup', methods=['POST'])
def api_auth_signup():
    data = request.json or {}
    email    = data.get('email', '').strip()
    password = data.get('password', '')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    result = sb.auth_signup(email, password)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    data = request.json or {}
    email    = data.get('email', '').strip()
    password = data.get('password', '')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    result = sb.auth_login(email, password)
    if 'error' in result:
        return jsonify(result), 401
    return jsonify(result)


@app.route('/api/auth/me', methods=['GET'])
def api_auth_me():
    token = _get_token()
    if not token:
        return jsonify({'error': 'No token'}), 401
    user_id = sb.get_user_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid or expired token'}), 401
    cid = sb.get_or_create_company_for_user(user_id)
    return jsonify({'user_id': user_id, 'company_id': cid})

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


# ── POST /api/upload/files ────────────────────────────────────────────────────
def _require_cid():
    """Get company_id or return a 401 response. Use in endpoints that need auth."""
    cid = get_cid()
    if cid is None:
        return None, jsonify({'error': 'Unauthorized'}), 401
    return cid, None, None


def _get_user_id() -> str | None:
    """Extract verified user_id from Bearer token, or None."""
    token = _get_token()
    if not token:
        return None
    try:
        res = sb.get_client().auth.get_user(token)
        return res.user.id if res.user else None
    except Exception:
        return None


@app.route('/api/companies', methods=['GET'])
def get_companies():
    user_id = _get_user_id()
    return jsonify(sb.load_companies(user_id))

@app.route('/api/companies', methods=['POST'])
def add_company():
    name = (request.json or {}).get('name', '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400
    user_id = _get_user_id()
    if user_id:
        co = sb.create_company_for_user(name, user_id)
        # Also map it
        try:
            sb.get_client().table('user_company_map').insert({
                'user_id': user_id, 'company_id': co['id']
            }).execute()
        except Exception:
            pass
    else:
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
    cid, err, code = _require_cid()
    if err: return err, code
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
    cid, err, code = _require_cid()
    if err: return err, code
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
    cid, err, code = _require_cid()
    if err: return err, code
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
        results = run_ai_audit(tb_path, db_path)

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
    cid, err, code = _require_cid()
    if err: return err, code
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
    cid, err, code = _require_cid()
    if err: return err, code
    sb.save_audit_result({}, cid)
    return jsonify({'ok': True})

@app.route('/api/audit/history', methods=['GET'])
def audit_history():
    cid, err, code = _require_cid()
    if err: return err, code
    return jsonify(load_history(cid))

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    cid, err, code = _require_cid()
    if err: return err, code
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
    cid, err, code = _require_cid()
    if err: return err, code
    data  = request.json
    marks = load_personal(cid)
    entry = {'date': data['date'], 'party': data['party'], 'amount': data['amount'], 'reason': data.get('reason', 'Personal')}
    if not any(m['date'] == entry['date'] and m['party'] == entry['party'] for m in marks):
        sb.save_personal_mark(entry, cid)
    return jsonify({'success': True, 'total_marks': len(marks) + 1})

@app.route('/api/audit/mark-personal', methods=['DELETE'])
def unmark_personal():
    cid, err, code = _require_cid()
    if err: return err, code
    data = request.json
    sb.delete_personal_mark(data['date'], data['party'], cid)
    return jsonify({'success': True})

@app.route('/api/audit/personal-marks', methods=['GET'])
def get_personal_marks():
    cid, err, code = _require_cid()
    if err: return err, code
    return jsonify(load_personal(cid))

# ── POST /api/bankrec-existing ────────────────────────────────────────────────
@app.route('/api/bankrec-existing', methods=['POST'])
def bank_reconciliation_existing():
    cid, err, code = _require_cid()
    if err: return err, code
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
    cid, err, code = _require_cid()
    if err: return err, code
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

# ── POST /api/ai-explain ─────────────────────────────────────────────────────
@app.route('/api/ai-explain', methods=['POST'])
def ai_explain():
    """
    Explain any audit finding using the knowledge base.
    Used by Full Audit, Quick Audit, Bank Recon to give AI explanations per finding.
    POST body: { "finding": {...}, "type": "ledger|cash|tds|bankrec|bs|pnl" }
    """
    data    = request.json or {}
    finding = data.get('finding', {})
    ftype   = data.get('type', 'ledger')
    cid, err, code = _require_cid()
    if err: return err, code

    if not finding:
        return jsonify({'error': 'finding required'}), 400

    # Build a focused question based on finding type
    if ftype == 'ledger':
        question = (
            f"Ledger '{finding.get('ledger')}' is grouped under '{finding.get('group')}' in Tally. "
            f"Issue: {finding.get('issue')}. Balance: ₹{finding.get('amount', 0):,.0f}. "
            f"Severity: {finding.get('severity')}. "
            f"Explain: (1) why this is wrong, (2) what the correct group should be, "
            f"(3) the exact Tally journal entry to fix it, (4) which accounting standard or law is violated."
        )
    elif ftype == 'cash':
        question = (
            f"Cash payment of ₹{finding.get('amount', 0):,.0f} made to '{finding.get('party')}' "
            f"on {finding.get('date')}. "
            f"Explain: (1) why this violates Section 40A(3), (2) how much will be disallowed, "
            f"(3) what should be done to avoid this in future."
        )
    elif ftype == 'tds':
        question = (
            f"TDS issue: {finding.get('note', finding.get('issue', ''))}. "
            f"Party: {finding.get('party', finding.get('ledger', ''))}. "
            f"Amount: ₹{finding.get('amount', 0):,.0f}. "
            f"Explain: (1) which TDS section applies, (2) what rate should be deducted, "
            f"(3) interest/penalty for non-compliance, (4) Tally entry to rectify."
        )
    elif ftype == 'bankrec':
        question = (
            f"Bank reconciliation issue: {finding.get('type', '')}. "
            f"Entry: {finding.get('narration', '')}. Amount: ₹{finding.get('amount', 0):,.0f}. "
            f"Date: {finding.get('date', '')}. "
            f"Explain: (1) what this means, (2) what action to take in Tally, "
            f"(3) the journal entry if needed."
        )
    elif ftype in ('bs', 'pnl'):
        question = (
            f"{'Balance Sheet' if ftype == 'bs' else 'P&L'} finding: {finding.get('message', '')}. "
            f"Severity: {finding.get('severity', '')}. "
            f"Explain: (1) why this is an issue, (2) which accounting standard applies, "
            f"(3) how to fix it in Tally."
        )
    else:
        question = f"Audit finding: {finding}. Explain the issue and how to fix it."

    try:
        from ca_agent import chat as ca_chat_fn
        audit_data = sb.load_audit_result(cid) or None
        reply = ca_chat_fn(question, audit_data, [])
        return jsonify({'explanation': reply})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /api/ca-chat ─────────────────────────────────────────────────────────
@app.route('/api/ca-chat', methods=['POST'])
def ca_chat():
    data        = request.json or {}
    user_msg    = data.get('message', '').strip()
    history     = data.get('history', [])   # [{role, content}, ...]

    if not user_msg:
        return jsonify({'error': 'message required'}), 400

    audit_data = sb.load_audit_result(get_cid() or 1) or None

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
    cid, err, code = _require_cid()
    if err: return err, code
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


# ── POST /api/clear-bank-files ───────────────────────────────────────────────
@app.route('/api/clear-bank-files', methods=['POST'])
def clear_bank_files():
    cid, err, code = _require_cid()
    if err: return err, code
    meta = load_files_meta(cid)
    meta.pop('bstmt', None)
    meta.pop('btally', None)
    save_files_meta(meta, cid)
    for fname in ('current_bank_stmt.xlsx', 'current_bank_tally.xlsx'):
        lp = cpath(cid, fname)
        if os.path.exists(lp):
            os.remove(lp)
    return jsonify({'ok': True})

# ── POST /api/upload/bank-files ───────────────────────────────────────────────
@app.route('/api/upload/bank-files', methods=['POST'])
def upload_bank_files():
    """Save bank statement and/or bank tally ledger persistently."""
    cid, err, code = _require_cid()
    if err: return err, code
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


# ── NEW FEATURES (Sandeep Bajoria) ────────────────────────────────────────────

def _ensure_tb_db(cid):
    """Download TB and DB from Supabase if not present locally. Returns (tb_path, db_path)."""
    tb = cpath(cid, 'current_tb.xlsx')
    db = cpath(cid, 'current_db.xlsx')
    if not os.path.exists(tb):
        _ensure_local(rname(cid, 'current_tb.xlsx'), tb)
    if not os.path.exists(db):
        _ensure_local(rname(cid, 'current_db.xlsx'), db)
    return tb, db

@app.route('/api/balance-sheet', methods=['POST'])
def api_balance_sheet():
    cid, err, code = _require_cid()
    if err: return err, code
    tb, _ = _ensure_tb_db(cid)
    if not os.path.exists(tb):
        return jsonify({'error': 'Upload Trial Balance first'}), 400
    try:
        from balance_sheet import generate_balance_sheet
        return jsonify(generate_balance_sheet(tb))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tds-detect', methods=['POST'])
def api_tds_detect():
    cid, err, code = _require_cid()
    if err: return err, code
    tb, db = _ensure_tb_db(cid)
    if not os.path.exists(tb):
        return jsonify({'error': 'Upload Trial Balance first'}), 400
    try:
        from tds_detector import detect_missed_tds
        return jsonify(detect_missed_tds(tb, db if os.path.exists(db) else None))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gst-return', methods=['POST'])
def api_gst_return():
    cid, err, code = _require_cid()
    if err: return err, code
    tb, db = _ensure_tb_db(cid)
    if not os.path.exists(tb):
        return jsonify({'error': 'Upload Trial Balance first'}), 400
    try:
        from gst_return import parse_gst_data
        return jsonify(parse_gst_data(tb, db if os.path.exists(db) else None))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shares-pnl', methods=['POST'])
def api_shares_pnl():
    cid, err, code = _require_cid()
    if err: return err, code
    tb, db = _ensure_tb_db(cid)
    if not os.path.exists(tb):
        return jsonify({'error': 'Upload Trial Balance first'}), 400
    try:
        from shares_pnl import calculate_shares_pnl
        return jsonify(calculate_shares_pnl(tb, db if os.path.exists(db) else None))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cash-flow', methods=['POST'])
def api_cash_flow():
    cid, err, code = _require_cid()
    if err: return err, code
    tb, db = _ensure_tb_db(cid)
    if not os.path.exists(tb):
        return jsonify({'error': 'Upload Trial Balance first'}), 400
    try:
        from cash_flow import generate_cash_flow
        return jsonify(generate_cash_flow(tb, db if os.path.exists(db) else None))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/doc-checker', methods=['POST'])
def api_doc_checker():
    cid, err, code = _require_cid()
    if err: return err, code
    tb, db = _ensure_tb_db(cid)
    try:
        from doc_checker import check_documents
        return jsonify(check_documents(
            db if os.path.exists(db) else None,
            tb if os.path.exists(tb) else None
        ))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/party-rec', methods=['POST'])
def api_party_rec():
    cid, err, code = _require_cid()
    if err: return err, code
    headers = {'X-Company-ID': str(cid)}
    tally_file = request.files.get('tally_ledger')
    party_file = request.files.get('party_statement')
    party_name = request.form.get('party_name', 'Party')
    if not tally_file or not party_file:
        return jsonify({'error': 'Upload both Tally ledger and party statement'}), 400
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tf:
            tally_file.save(tf.name)
            tp = tf.name
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as pf:
            party_file.save(pf.name)
            pp = pf.name
        from party_rec import reconcile_party
        result = reconcile_party(tp, pp, party_name)
        os.unlink(tp); os.unlink(pp)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/broker-rec', methods=['POST'])
def api_broker_rec():
    if 'tally_file' not in request.files or 'broker_file' not in request.files:
        return jsonify({'error': 'Upload both tally_file and broker_file'}), 400
    broker = request.form.get('broker', 'zerodha')
    try:
        import tempfile, pandas as pd
        tf = request.files['tally_file']
        bf = request.files['broker_file']
        tp = tempfile.mktemp(suffix='.xlsx'); bp = tempfile.mktemp(suffix='.xlsx')
        tf.save(tp); bf.save(bp)
        tally_df = pd.read_excel(tp, header=None) if tp.endswith('.xlsx') else pd.read_csv(tp)
        broker_df = pd.read_excel(bp, header=None) if bp.endswith('.xlsx') else pd.read_csv(bp)
        os.unlink(tp); os.unlink(bp)
        return jsonify({
            'matched_count': 0,
            'unmatched_count': 0,
            'value_diff': 0,
            'is_reconciled': False,
            'unmatched': [],
            'note': f'Broker reconciliation for {broker} — upload parsed correctly. Manual column mapping needed for full match.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pt-analysis', methods=['POST'])
def api_pt_analysis():
    cid, err, code = _require_cid()
    if err: return err, code
    tb, db = _ensure_tb_db(cid)
    if not os.path.exists(tb):
        return jsonify({'error': 'Upload Trial Balance first'}), 400
    try:
        from pt_engine import run_pt_analysis
        return jsonify(run_pt_analysis(tb, db if os.path.exists(db) else None))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(BUILD_DIR, 'favicon.ico')

@app.route('/asset-manifest.json')
def asset_manifest():
    return send_from_directory(BUILD_DIR, 'asset-manifest.json')

# Catch-all — serves index.html for all React Router paths
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    resp = make_response(send_from_directory(BUILD_DIR, 'index.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"VirtualCA backend running on port {port}")
    app.run(host='0.0.0.0', port=port)
