-- ============================================================================
-- ch15 / step 3 — 遅いクエリを Postgres 側で勝手に拾う設定。
-- ============================================================================
-- log_min_duration_statement = '200ms' を超えたクエリ + 実行計画が、
-- Postgres ログに自動で吐かれるようになる。
--
-- 注意: ALTER SYSTEM は server-wide な永続設定。 学習用 docker compose で
-- 立てた Postgres には気軽にやってよいが、 共有環境では避ける。
-- ============================================================================

-- 1. 200ms を超えたクエリ自体を全部ログ
ALTER SYSTEM SET log_min_duration_statement = '200ms';

-- 2. auto_explain 拡張をロード
ALTER SYSTEM SET shared_preload_libraries  = 'auto_explain';
ALTER SYSTEM SET auto_explain.log_min_duration = '200ms';
ALTER SYSTEM SET auto_explain.log_analyze       = on;
ALTER SYSTEM SET auto_explain.log_buffers       = on;

-- 設定を反映 (一部は再起動が必要。 docker compose restart db)
SELECT pg_reload_conf();

-- ----------------------------------------------------------------------------
-- 確認方法
-- ----------------------------------------------------------------------------
-- docker compose logs -f db | grep "duration:"
-- ↑ 200ms を超えたクエリと plan が流れてくる
--
-- ----------------------------------------------------------------------------
-- 元に戻す
-- ----------------------------------------------------------------------------
-- ALTER SYSTEM RESET log_min_duration_statement;
-- ALTER SYSTEM RESET shared_preload_libraries;
-- ALTER SYSTEM RESET auto_explain.log_min_duration;
-- ALTER SYSTEM RESET auto_explain.log_analyze;
-- ALTER SYSTEM RESET auto_explain.log_buffers;
-- SELECT pg_reload_conf();
