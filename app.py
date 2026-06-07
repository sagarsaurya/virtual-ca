from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, tempfile
from audit_engine import run_full_audit

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

PERSONAL_FILE = os.path.join(DATA_DIR, 'personal_marks.json')

def load_personal():
    if os.path.exists(PERSONAL_FILE):
        with open(PERSONAL_FILE) as f:
            return json.load(f)
    return []

def save_personal(marks):
    with open(PERSONAL_FILE, 'w') as f:
        json.dump(marks, f, indent=2)

# ── Serve index.html ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ── POST /api/audit — upload files and run audit ──────────────────────────────
@app.route('/api/audit', methods=['POST'])
def run_audit():
    if 'trial_balance' not in request.files:
        return jsonify({'error': 'trial_balance file required'}), 400

    tb_file = request.files['trial_balance']
    db_file = request.files.get('daybook')

    # Save to temp files
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        tb_path = tmp.name
        tb_file.save(tb_path)

    db_path = None
    if db_file:
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            db_path = tmp.name
            db_file.save(db_path)

    try:
        results = run_full_audit(tb_path, db_path)

        # Apply personal marks — exclude marked entries from cash violations
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

        # Recalculate score
        s = results['summary']
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
        results['summary']['score']     = score
        results['summary']['critical']  = critical
        results['summary']['warnings']  = warnings
        results['summary']['questions'] = questions

        # Cache result
        with open(os.path.join(DATA_DIR, 'audit_result.json'), 'w') as f:
            json.dump(results, f, indent=2, default=str)

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.unlink(tb_path)
        if db_path:
            os.unlink(db_path)

# ── GET /api/audit/last — return last cached audit ────────────────────────────
@app.route('/api/audit/last', methods=['GET'])
def last_audit():
    path = os.path.join(DATA_DIR, 'audit_result.json')
    if os.path.exists(path):
        with open(path) as f:
            return jsonify(json.load(f))
    return jsonify({'error': 'No audit run yet'}), 404

# ── POST /api/audit/mark-personal — mark entry as personal ───────────────────
@app.route('/api/audit/mark-personal', methods=['POST'])
def mark_personal():
    data = request.json
    marks = load_personal()
    entry = {'date': data['date'], 'party': data['party'], 'amount': data['amount'], 'reason': data.get('reason', 'Personal')}
    # avoid duplicates
    if not any(m['date'] == entry['date'] and m['party'] == entry['party'] for m in marks):
        marks.append(entry)
        save_personal(marks)
    return jsonify({'success': True, 'total_marks': len(marks)})

# ── DELETE /api/audit/mark-personal — unmark ─────────────────────────────────
@app.route('/api/audit/mark-personal', methods=['DELETE'])
def unmark_personal():
    data = request.json
    marks = load_personal()
    marks = [m for m in marks if not (m['date'] == data['date'] and m['party'] == data['party'])]
    save_personal(marks)
    return jsonify({'success': True})

# ── GET /api/audit/personal-marks ────────────────────────────────────────────
@app.route('/api/audit/personal-marks', methods=['GET'])
def get_personal_marks():
    return jsonify(load_personal())

if __name__ == '__main__':
    print("VirtualCA backend running on http://localhost:5050")
    app.run(debug=True, port=5050)
