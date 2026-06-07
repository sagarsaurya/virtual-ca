from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, tempfile, datetime
from audit_engine import run_full_audit
from bankrec_engine import run_bankrec

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

PERSONAL_FILE  = os.path.join(DATA_DIR, 'personal_marks.json')
HISTORY_FILE   = os.path.join(DATA_DIR, 'audit_history.json')
RESULT_FILE    = os.path.join(DATA_DIR, 'audit_result.json')

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

# ── POST /api/audit ───────────────────────────────────────────────────────────
@app.route('/api/audit', methods=['POST'])
def run_audit():
    if 'trial_balance' not in request.files:
        return jsonify({'error': 'trial_balance file required'}), 400

    tb_file  = request.files['trial_balance']
    db_file  = request.files.get('daybook')
    tb_name  = tb_file.filename

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        tb_path = tmp.name; tb_file.save(tb_path)

    db_path = None
    if db_file:
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            db_path = tmp.name; db_file.save(db_path)

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
    finally:
        os.unlink(tb_path)
        if db_path: os.unlink(db_path)

# ── GET /api/audit/last ───────────────────────────────────────────────────────
@app.route('/api/audit/last', methods=['GET'])
def last_audit():
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE) as f: return jsonify(json.load(f))
    return jsonify({'error': 'No audit run yet'}), 404

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
    if 'bank_statement' not in request.files or 'tally_ledger' not in request.files:
        return jsonify({'error': 'Both bank_statement and tally_ledger files are required'}), 400

    bs_file = request.files['bank_statement']
    tl_file = request.files['tally_ledger']

    bs_ext = os.path.splitext(bs_file.filename)[1] or '.pdf'
    tl_ext = os.path.splitext(tl_file.filename)[1] or '.xlsx'

    with tempfile.NamedTemporaryFile(suffix=bs_ext, delete=False) as tmp:
        bs_path = tmp.name; bs_file.save(bs_path)
    with tempfile.NamedTemporaryFile(suffix=tl_ext, delete=False) as tmp:
        tl_path = tmp.name; tl_file.save(tl_path)

    try:
        result = run_bankrec(bs_path, tl_path, bs_file.filename)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        os.unlink(bs_path)
        os.unlink(tl_path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"VirtualCA backend running on port {port}")
    app.run(host='0.0.0.0', port=port)
