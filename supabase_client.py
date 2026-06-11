"""
Supabase client — storage + database for VirtualCA.
All functions accept company_id (cid) for multi-company support.
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://arlsvbjvsikzdeqfufut.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFybHN2Ymp2c2lremRlcWZ1ZnV0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTA4MTc1OCwiZXhwIjoyMDk2NjU3NzU4fQ.yNUJ_BT44FWuHIkZB_ziQI7kfUnerZgm8E2sQh4g14w')

BUCKET = 'virtualca-files'

_client: Client = None

def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── COMPANIES ─────────────────────────────────────────────────────────────────

def load_companies() -> list:
    try:
        sb = get_client()
        res = sb.table('companies').select('*').order('id').execute()
        return res.data or []
    except Exception as e:
        print(f'[Supabase] load_companies error: {e}')
        return [{'id': 1, 'name': 'Default Company'}]


def create_company(name: str) -> dict:
    try:
        sb = get_client()
        res = sb.table('companies').insert({'name': name}).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f'[Supabase] create_company error: {e}')
        return {}


def delete_company(cid: int):
    try:
        sb = get_client()
        sb.table('companies').delete().eq('id', cid).execute()
        sb.table('files_meta').delete().eq('company_id', cid).execute()
        sb.table('audit_result').delete().eq('company_id', cid).execute()
        sb.table('audit_history').delete().eq('company_id', cid).execute()
        sb.table('personal_marks').delete().eq('company_id', cid).execute()
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
    try:
        sb = get_client()
        # Check if row exists for this company
        res = sb.table('files_meta').select('id').eq('company_id', cid).execute()
        if res.data:
            sb.table('files_meta').update({'meta': meta}).eq('company_id', cid).execute()
        else:
            sb.table('files_meta').insert({'company_id': cid, 'meta': meta}).execute()
    except Exception as e:
        print(f'[Supabase] save_files_meta error: {e}')


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
    try:
        sb = get_client()
        res = sb.table('audit_result').select('id').eq('company_id', cid).execute()
        if res.data:
            sb.table('audit_result').update({'result': result}).eq('company_id', cid).execute()
        else:
            sb.table('audit_result').insert({'company_id': cid, 'result': result}).execute()
    except Exception as e:
        print(f'[Supabase] save_audit_result error: {e}')


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
