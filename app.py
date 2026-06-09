from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, tempfile, datetime

# Load .env file if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — use system env vars (Render sets them directly)
from audit_engine import run_full_audit
from bankrec_engine import run_bankrec

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

PERSONAL_FILE  = os.path.join(DATA_DIR, 'personal_marks.json')
HISTORY_FILE   = os.path.join(DATA_DIR, 'audit_history.json')
RESULT_FILE    = os.path.join(DATA_DIR, 'audit_result.json')
FILES_META     = os.path.join(DATA_DIR, 'uploaded_files.json')   # tracks what's saved
CURRENT_TB     = os.path.join(DATA_DIR, 'current_tb.xlsx')       # persistent trial balance
CURRENT_DB     = os.path.join(DATA_DIR, 'current_db.xlsx')       # persistent daybook

# ── helpers ───────────────────────────────────────────────────────────────────
def load_personal():
    if os.path.exists(PERSONAL_FILE):
        with open(PERSONAL_FILE) as f: return json.load(f)
    return []

def save_personal(marks):
    with open(PERSONAL_FILE, 'w') as f: json.dump(marks, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f: return json.load(f)
    return []

def save_history(h):
    with open(HISTORY_FILE, 'w') as f: json.dump(h, f, indent=2, default=str)

def load_files_meta():
    if os.path.exists(FILES_META):
        with open(FILES_META) as f: return json.load(f)
    return {}

def save_files_meta(m):
    with open(FILES_META, 'w') as f: json.dump(m, f, indent=2)

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
        meta['tb'] = {
            'filename':    tb_file.filename,
            'uploaded_at': datetime.datetime.now().isoformat(),
            'size':        os.path.getsize(CURRENT_TB),
        }
        saved.append('trial_balance')

    db_file = request.files.get('daybook')
    if db_file and db_file.filename:
        db_file.save(CURRENT_DB)
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
    meta['tb_exists'] = os.path.exists(CURRENT_TB)
    meta['db_exists'] = os.path.exists(CURRENT_DB)
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

    if tb_file and tb_file.filename:
        # new file sent — save permanently AND use for this audit
        tb_file.save(CURRENT_TB)
        meta = load_files_meta()
        meta['tb'] = {'filename': tb_file.filename,
                      'uploaded_at': datetime.datetime.now().isoformat(),
                      'size': os.path.getsize(CURRENT_TB)}
        save_files_meta(meta)
        tb_path = CURRENT_TB
        tb_name = tb_file.filename
    elif os.path.exists(CURRENT_TB):
        tb_path = CURRENT_TB
        tb_name = load_files_meta().get('tb', {}).get('filename', 'trial_balance.xlsx')
    else:
        return jsonify({'error': 'No Trial Balance uploaded. Please upload a file first.'}), 400

    if db_file and db_file.filename:
        db_file.save(CURRENT_DB)
        meta = load_files_meta()
        meta['db'] = {'filename': db_file.filename,
                      'uploaded_at': datetime.datetime.now().isoformat(),
                      'size': os.path.getsize(CURRENT_DB)}
        save_files_meta(meta)
        db_path = CURRENT_DB
    elif os.path.exists(CURRENT_DB):
        db_path = CURRENT_DB

    try:
        results = run_full_audit(tb_path, db_path)

        # apply personal marks
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

        # save as last result
        with open(RESULT_FILE, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # append to history
        history = load_history()
        history.insert(0, {
            'id':          len(history) + 1,
            'filename':    tb_name,
            'audited_at':  results['audited_at'],
            'company':     results['summary'].get('company', ''),
            'period':      results['summary'].get('period', ''),
            'score':       score,
            'critical':    critical,
            'warnings':    warnings,
            'questions':   questions,
        })
        save_history(history[:50])   # keep last 50

        return jsonify(results)

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ── GET /api/audit/last ───────────────────────────────────────────────────────
@app.route('/api/audit/last', methods=['GET'])
def last_audit():
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE) as f:
            data = json.load(f)
        # Safety: if saved result has 0 issues but files exist, flag it as stale
        s = data.get('summary', {})
        if (s.get('critical', 0) == 0 and s.get('warnings', 0) == 0
                and s.get('questions', 0) == 0 and s.get('score', 0) == 0
                and os.path.exists(CURRENT_TB)):
            data['_stale_warning'] = 'Saved result shows 0 issues — please re-run audit to get fresh results.'
        return jsonify(data)
    return jsonify({'error': 'No audit run yet'}), 404

# ── DELETE /api/audit/clear ───────────────────────────────────────────────────
@app.route('/api/audit/clear', methods=['POST'])
def clear_audit():
    """Clears saved audit result so next page load starts fresh."""
    if os.path.exists(RESULT_FILE):
        os.remove(RESULT_FILE)
    return jsonify({'ok': True})

# ── GET /api/audit/history ────────────────────────────────────────────────────
@app.route('/api/audit/history', methods=['GET'])
def audit_history():
    return jsonify(load_history())

# ── GET /api/dashboard ────────────────────────────────────────────────────────
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    history = load_history()
    last = {}
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE) as f: last = json.load(f)
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
    data   = request.json
    marks  = load_personal()
    entry  = {'date': data['date'], 'party': data['party'], 'amount': data['amount'], 'reason': data.get('reason', 'Personal')}
    if not any(m['date'] == entry['date'] and m['party'] == entry['party'] for m in marks):
        marks.append(entry)
        save_personal(marks)
    return jsonify({'success': True, 'total_marks': len(marks)})

@app.route('/api/audit/mark-personal', methods=['DELETE'])
def unmark_personal():
    data  = request.json
    marks = load_personal()
    marks = [m for m in marks if not (m['date'] == data['date'] and m['party'] == data['party'])]
    save_personal(marks)
    return jsonify({'success': True})

@app.route('/api/audit/personal-marks', methods=['GET'])
def get_personal_marks():
    return jsonify(load_personal())

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

    if tl_file and tl_file.filename:
        tl_ext = os.path.splitext(tl_file.filename)[1] or '.xlsx'
        with tempfile.NamedTemporaryFile(suffix=tl_ext, delete=False) as tmp:
            tl_path = tmp.name; tl_file.save(tl_path)
            tmp_tl  = tl_path
        tl_filename = tl_file.filename
    elif os.path.exists(CURRENT_DB):
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

    # Load last audit result as context (may be None if no audit run yet)
    audit_data = None
    if os.path.exists(RESULT_FILE):
        try:
            with open(RESULT_FILE) as f:
                audit_data = json.load(f)
        except Exception:
            pass

    try:
        from ca_agent import chat as ca_chat_fn
        reply = ca_chat_fn(user_msg, audit_data, history)
        return jsonify({'reply': reply})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"VirtualCA backend running on port {port}")
    app.run(host='0.0.0.0', port=port)
