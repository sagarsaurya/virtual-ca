"""
Supabase client — storage + database for VirtualCA.
All functions accept company_id (cid) for multi-company support.
Auth: Supabase Auth (email/password) → JWT token → user_id → company_id
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://arlsvbjvsikzdeqfufut.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFybHN2Ymp2c2lremRlcWZ1ZnV0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTA4MTc1OCwiZXhwIjoyMDk2NjU3NzU4fQ.yNUJ_BT44FWuHIkZB_ziQI7kfUnerZgm8E2sQh4g14w')

BUCKET = 'virtualca-files'

def get_client() -> Client:
    # Create a fresh client per call — avoids [Errno 11] EAGAIN from shared
    # socket state when Flask handles concurrent requests in multiple threads.
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── AUTH ─────────────────────────────────────────────────────────────────────

def auth_signup(email: str, password: str) -> dict:
    """Create a new user. Returns {token, email} or {error}."""
    try:
        sb = get_client()
        res = sb.auth.sign_up({'email': email, 'password': password})
        if res.user is None:
            return {'error': 'Signup failed — check email format'}
        session = res.session
        if session:
            return {'token': session.access_token, 'email': res.user.email, 'user_id': res.user.id}
        # Email confirmation required
        return {'email': res.user.email, 'needs_confirmation': True}
    except Exception as e:
        msg = str(e)
        if 'already registered' in msg.lower() or 'already been registered' in msg.lower():
            return {'error': 'This email is already registered. Please sign in.'}
        return {'error': msg}


def auth_login(email: str, password: str) -> dict:
    """Sign in existing user. Returns {token, email, user_id} or {error}."""
    try:
        sb = get_client()
        res = sb.auth.sign_in_with_password({'email': email, 'password': password})
        if res.user is None:
            return {'error': 'Invalid email or password'}
        return {
            'token': res.session.access_token,
            'email': res.user.email,
            'user_id': res.user.id,
        }
    except Exception as e:
        msg = str(e)
        if 'invalid' in msg.lower() or 'credentials' in msg.lower():
            return {'error': 'Invalid email or password'}
        return {'error': msg}


def get_user_from_token(token: str) -> str | None:
    """Verify JWT and return user_id, or None if invalid."""
    try:
        sb = get_client()
        res = sb.auth.get_user(token)
        return res.user.id if res.user else None
    except Exception:
        return None


def get_or_create_company_for_user(user_id: str, email: str = None) -> int:
    """Return the company_id for this user, creating one if needed."""
    sb = get_client()

    # Check if this user already has a company via map table
    res = sb.table('user_company_map').select('company_id').eq('user_id', user_id).execute()
    if res.data:
        return res.data[0]['company_id']

    # Also check companies table directly (for users created before map table)
    res2 = sb.table('companies').select('id').eq('user_id', user_id).limit(1).execute()
    if res2.data:
        cid = res2.data[0]['id']
        # Backfill map table
        try:
            sb.table('user_company_map').insert({'user_id': user_id, 'company_id': cid}).execute()
        except Exception:
            pass
        return cid

    # No company yet — create one called "My Books"
    co = create_company_for_user('My Books', user_id)
    cid = co.get('id')
    if not cid:
        raise Exception(f'Failed to create company for user {user_id}')

    sb.table('user_company_map').insert({'user_id': user_id, 'company_id': cid}).execute()
    print(f'[Auth] Created company {cid} for user {user_id}')
    return cid


# ── COMPANIES ─────────────────────────────────────────────────────────────────

def load_companies(user_id: str = None) -> list:
    """Return only companies belonging to this user."""
    try:
        sb = get_client()
        if user_id:
            res = sb.table('companies').select('*').eq('user_id', user_id).order('id').execute()
        else:
            res = sb.table('companies').select('*').order('id').execute()
        return res.data or []
    except Exception as e:
        print(f'[Supabase] load_companies error: {e}')
        return []


def create_company(name: str) -> dict:
    """Create company without user_id (legacy/admin use)."""
    try:
        sb = get_client()
        res = sb.table('companies').insert({'name': name}).execute()
        if not res.data:
            return {}
        co = res.data[0]
        try:
            sb.table('files_meta').insert({'company_id': co['id'], 'meta': {}}).execute()
        except Exception as e2:
            print(f'[Supabase] pre-create files_meta error: {e2}')
        return co
    except Exception as e:
        print(f'[Supabase] create_company error: {e}')
        return {}


def create_company_for_user(name: str, user_id: str) -> dict:
    """Create a company tagged to a specific user."""
    try:
        sb = get_client()
        res = sb.table('companies').insert({'name': name, 'user_id': user_id}).execute()
        if not res.data:
            return {}
        co = res.data[0]
        try:
            sb.table('files_meta').insert({'company_id': co['id'], 'meta': {}}).execute()
        except Exception as e2:
            print(f'[Supabase] pre-create files_meta error: {e2}')
        return co
    except Exception as e:
        print(f'[Supabase] create_company_for_user error: {e}')
        return {}


def delete_company(cid: int):
    try:
        sb = get_client()
        sb.table('companies').delete().eq('id', cid).execute()
        sb.table('files_meta').delete().eq('company_id', cid).execute()
        sb.table('audit_result').delete().eq('company_id', cid).execute()
        sb.table('audit_history').delete().eq('company_id', cid).execute()
        sb.table('personal_marks').delete().eq('company_id', cid).execute()
        sb.table('user_company_map').delete().eq('company_id', cid).execute()
    except Exception as e:
        print(f'[Supabase] delete_company error: {e}')


def rename_company(cid: int, name: str):
    try:
        sb = get_client()
        sb.table('companies').update({'name': name}).eq('id', cid).execute()
    except Exception as e:
        print(f'[Supabase] rename_company error: {e}')


# ── FILE STORAGE ──────────────────────────────────────────────────────────────

def upload_file(local_path: str, remote_name: str) -> bool:
    try:
        sb = get_client()
        with open(local_path, 'rb') as f:
            data = f.read()
        sb.storage.from_(BUCKET).upload(path=remote_name, file=data, file_options={"upsert": "true"})
        return True
    except Exception as e:
        print(f'[Supabase] upload_file error: {e}')
        return False


def download_file(remote_name: str, local_path: str) -> bool:
    try:
        sb = get_client()
        data = sb.storage.from_(BUCKET).download(remote_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f'[Supabase] download_file error ({remote_name}): {e}')
        return False


# ── DATABASE: files_meta ──────────────────────────────────────────────────────

def load_files_meta(cid: int = 1) -> dict:
    try:
        sb = get_client()
        res = sb.table('files_meta').select('*').eq('company_id', cid).execute()
        if res.data:
            return res.data[0].get('meta', {})
        return {}
    except Exception as e:
        print(f'[Supabase] load_files_meta error: {e}')
        return {}


def save_files_meta(meta: dict, cid: int = 1):
    import sys
    try:
        sb = get_client()
        res = sb.table('files_meta').select('id').eq('company_id', cid).execute()
        print(f'[save_files_meta] cid={cid} existing={res.data}', file=sys.stderr, flush=True)
        if res.data:
            r2 = sb.table('files_meta').update({'meta': meta}).eq('company_id', cid).execute()
            print(f'[save_files_meta] updated cid={cid} result={r2.data}', file=sys.stderr, flush=True)
        else:
            r2 = sb.table('files_meta').insert({'company_id': cid, 'meta': meta}).execute()
            print(f'[save_files_meta] inserted cid={cid} result={r2.data}', file=sys.stderr, flush=True)
    except Exception as e:
        print(f'[save_files_meta] ERROR cid={cid}: {e}', file=sys.stderr, flush=True)


# ── DATABASE: audit_history ───────────────────────────────────────────────────

def load_history(cid: int = 1) -> list:
    try:
        sb = get_client()
        res = sb.table('audit_history').select('*').eq('company_id', cid).order('audited_at', desc=True).limit(50).execute()
        return res.data or []
    except Exception as e:
        print(f'[Supabase] load_history error: {e}')
        return []


def save_history_entry(entry: dict, cid: int = 1):
    try:
        sb = get_client()
        entry['company_id'] = cid
        sb.table('audit_history').insert(entry).execute()
    except Exception as e:
        print(f'[Supabase] save_history_entry error: {e}')


# ── DATABASE: personal_marks ──────────────────────────────────────────────────

def load_personal(cid: int = 1) -> list:
    try:
        sb = get_client()
        res = sb.table('personal_marks').select('*').eq('company_id', cid).execute()
        return res.data or []
    except Exception as e:
        print(f'[Supabase] load_personal error: {e}')
        return []


def save_personal_mark(entry: dict, cid: int = 1):
    try:
        sb = get_client()
        entry['company_id'] = cid
        sb.table('personal_marks').insert(entry).execute()
    except Exception as e:
        print(f'[Supabase] save_personal_mark error: {e}')


def delete_personal_mark(date: str, party: str, cid: int = 1):
    try:
        sb = get_client()
        sb.table('personal_marks').delete().eq('date', date).eq('party', party).eq('company_id', cid).execute()
    except Exception as e:
        print(f'[Supabase] delete_personal_mark error: {e}')


# ── DATABASE: audit_result (latest per company) ───────────────────────────────

def save_audit_result(result: dict, cid: int = 1):
    import sys
    try:
        sb = get_client()
        res = sb.table('audit_result').select('id').eq('company_id', cid).execute()
        print(f'[save_audit_result] cid={cid} existing={bool(res.data)}', file=sys.stderr, flush=True)
        if res.data:
            sb.table('audit_result').update({'result': result}).eq('company_id', cid).execute()
        else:
            sb.table('audit_result').insert({'company_id': cid, 'result': result}).execute()
        print(f'[save_audit_result] cid={cid} saved ok', file=sys.stderr, flush=True)
    except Exception as e:
        print(f'[save_audit_result] ERROR cid={cid}: {e}', file=sys.stderr, flush=True)


def load_audit_result(cid: int = 1) -> dict:
    try:
        sb = get_client()
        res = sb.table('audit_result').select('*').eq('company_id', cid).execute()
        if res.data:
            return res.data[0].get('result', {})
        return {}
    except Exception as e:
        print(f'[Supabase] load_audit_result error: {e}')
        return {}


# ── DATABASE: feature_cache (one row per company per feature) ─────────────────

def save_feature_cache(feature: str, result: dict, cid: int = 1):
    """Save a feature result so it persists across page navigation."""
    try:
        sb = get_client()
        res = sb.table('feature_cache').select('id').eq('company_id', cid).eq('feature', feature).execute()
        if res.data:
            sb.table('feature_cache').update({'result': result}).eq('company_id', cid).eq('feature', feature).execute()
        else:
            sb.table('feature_cache').insert({'company_id': cid, 'feature': feature, 'result': result}).execute()
    except Exception as e:
        print(f'[Supabase] save_feature_cache error ({feature}): {e}')


def load_feature_cache(feature: str, cid: int = 1) -> dict:
    """Load last saved result for a feature. Returns {} if not yet run."""
    try:
        sb = get_client()
        res = sb.table('feature_cache').select('result').eq('company_id', cid).eq('feature', feature).execute()
        if res.data:
            return res.data[0].get('result', {})
        return {}
    except Exception as e:
        print(f'[Supabase] load_feature_cache error ({feature}): {e}')
        return {}
