"""
Supabase client — storage + database for VirtualCA.
All file I/O and JSON state now goes through Supabase.
"""
import os
import json
import datetime
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


# ── FILE STORAGE ──────────────────────────────────────────────────────────────

def upload_file(local_path: str, remote_name: str) -> bool:
    """Upload a local file to Supabase storage. Returns True on success."""
    try:
        sb = get_client()
        with open(local_path, 'rb') as f:
            data = f.read()
        # upsert=True overwrites existing file
        sb.storage.from_(BUCKET).upload(
            path=remote_name,
            file=data,
            file_options={"upsert": "true"}
        )
        return True
    except Exception as e:
        print(f'[Supabase] upload_file error: {e}')
        return False


def download_file(remote_name: str, local_path: str) -> bool:
    """Download a file from Supabase storage to local_path. Returns True on success."""
    try:
        sb = get_client()
        data = sb.storage.from_(BUCKET).download(remote_name)
        with open(local_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f'[Supabase] download_file error ({remote_name}): {e}')
        return False


def file_exists_remote(remote_name: str) -> bool:
    """Check if a file exists in Supabase storage."""
    try:
        sb = get_client()
        files = sb.storage.from_(BUCKET).list()
        return any(f['name'] == remote_name for f in (files or []))
    except Exception:
        return False


# ── DATABASE: files_meta ──────────────────────────────────────────────────────

def load_files_meta() -> dict:
    try:
        sb = get_client()
        res = sb.table('files_meta').select('*').eq('id', 1).execute()
        if res.data:
            return res.data[0].get('meta', {})
        return {}
    except Exception as e:
        print(f'[Supabase] load_files_meta error: {e}')
        return {}


def save_files_meta(meta: dict):
    try:
        sb = get_client()
        sb.table('files_meta').upsert({'id': 1, 'meta': meta}).execute()
    except Exception as e:
        print(f'[Supabase] save_files_meta error: {e}')


# ── DATABASE: audit_history ───────────────────────────────────────────────────

def load_history() -> list:
    try:
        sb = get_client()
        res = sb.table('audit_history').select('*').order('audited_at', desc=True).limit(50).execute()
        return res.data or []
    except Exception as e:
        print(f'[Supabase] load_history error: {e}')
        return []


def save_history_entry(entry: dict):
    try:
        sb = get_client()
        sb.table('audit_history').insert(entry).execute()
    except Exception as e:
        print(f'[Supabase] save_history_entry error: {e}')


# ── DATABASE: personal_marks ──────────────────────────────────────────────────

def load_personal() -> list:
    try:
        sb = get_client()
        res = sb.table('personal_marks').select('*').execute()
        return res.data or []
    except Exception as e:
        print(f'[Supabase] load_personal error: {e}')
        return []


def save_personal_mark(entry: dict):
    try:
        sb = get_client()
        sb.table('personal_marks').insert(entry).execute()
    except Exception as e:
        print(f'[Supabase] save_personal_mark error: {e}')


def delete_personal_mark(date: str, party: str):
    try:
        sb = get_client()
        sb.table('personal_marks').delete().eq('date', date).eq('party', party).execute()
    except Exception as e:
        print(f'[Supabase] delete_personal_mark error: {e}')


# ── DATABASE: audit_result (latest) ──────────────────────────────────────────

def save_audit_result(result: dict):
    try:
        sb = get_client()
        sb.table('audit_result').upsert({'id': 1, 'result': result}).execute()
    except Exception as e:
        print(f'[Supabase] save_audit_result error: {e}')


def load_audit_result() -> dict:
    try:
        sb = get_client()
        res = sb.table('audit_result').select('*').eq('id', 1).execute()
        if res.data:
            return res.data[0].get('result', {})
        return {}
    except Exception as e:
        print(f'[Supabase] load_audit_result error: {e}')
        return {}
