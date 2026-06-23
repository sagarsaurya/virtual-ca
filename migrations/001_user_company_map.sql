-- Run this ONCE in Supabase SQL Editor
-- Dashboard → SQL Editor → paste and run

CREATE TABLE IF NOT EXISTS user_company_map (
  user_id    TEXT PRIMARY KEY,
  company_id INT  NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Disable RLS (backend uses service key, handles security in code)
ALTER TABLE user_company_map DISABLE ROW LEVEL SECURITY;
