-- ============================================================================
-- ch14 / step 1 — 「DB 自身が記憶する適用ログ」 schema_migrations。
-- ============================================================================
-- ファイル名を PK にして、 同じファイルを 2 回流せないようにする。
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT        PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 動作確認
-- ----------------------------------------------------------------------------
-- (a) 同じファイル名は 2 回入らない:
--   INSERT INTO schema_migrations (filename) VALUES ('0001_initial.sql');
--   INSERT INTO schema_migrations (filename) VALUES ('0001_initial.sql');  -- ← PK 違反
--
-- (b) ランナーから見たい列:
--   SELECT filename, applied_at FROM schema_migrations ORDER BY filename;
