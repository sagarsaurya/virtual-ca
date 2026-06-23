-- Run this ONCE in Supabase SQL Editor
-- Stores last result of each feature per company so users don't re-run on navigation

CREATE TABLE IF NOT EXISTS feature_cache (
  id          BIGSERIAL PRIMARY KEY,
  company_id  INT  NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  feature     TEXT NOT NULL,
  result      JSONB NOT NULL DEFAULT '{}',
  updated_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (company_id, feature)
);

ALTER TABLE feature_cache DISABLE ROW LEVEL SECURITY;

-- Auto-update updated_at on every save
CREATE OR REPLACE FUNCTION update_feature_cache_timestamp()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS feature_cache_updated_at ON feature_cache;
CREATE TRIGGER feature_cache_updated_at
  BEFORE UPDATE ON feature_cache
  FOR EACH ROW EXECUTE FUNCTION update_feature_cache_timestamp();
