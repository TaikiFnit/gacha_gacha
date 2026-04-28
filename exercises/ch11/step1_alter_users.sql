-- ============================================================================
-- ch11 / step 1 — users に last_collected_at を生やし、 equipped_characters を作る。
-- ============================================================================
-- 装備しているキャラの rarity 合計 = 1 秒あたりの取得 coin、 という設計。
--
-- 実行:
--   psql "$DATABASE_URL" -f exercises/ch11/step1_alter_users.sql
-- ============================================================================

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TABLE IF NOT EXISTS equipped_characters (
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE RESTRICT,
    PRIMARY KEY (user_id, character_id)
);

-- ----------------------------------------------------------------------------
-- 動作確認
-- ----------------------------------------------------------------------------
-- (a) 新カラムが入ったか
--   \d users
--
-- (b) 同じキャラを 2 回装備しようとすると弾かれることを確認
--   INSERT INTO equipped_characters VALUES (1, 1);
--   INSERT INTO equipped_characters VALUES (1, 1);   -- ← PK 違反
--
-- (c) 装備中のキャラを characters 側から消そうとすると RESTRICT で守られる
--   DELETE FROM characters WHERE id = 1;             -- ← FK 違反になる
