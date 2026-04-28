-- ============================================================================
-- ch10 / step 1 — daily_bonuses テーブルを作る。
-- ============================================================================
-- 1 ユーザーが 1 日 1 行しか持てないことを (user_id, claimed_on) の UNIQUE で
-- DB に物理保証させる。これが Ch.10 の心臓部。
--
-- 使い方:
--   psql "$DATABASE_URL" -f exercises/ch10/step1_daily_bonuses_table.sql
-- ============================================================================

DROP TABLE IF EXISTS daily_bonuses;

CREATE TABLE daily_bonuses (
    id          BIGSERIAL    PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    claimed_on  DATE         NOT NULL DEFAULT (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')::date,
    amount      INTEGER      NOT NULL,
    UNIQUE (user_id, claimed_on)
);

-- ----------------------------------------------------------------------------
-- 動作確認
-- ----------------------------------------------------------------------------
-- (a) 同じ日に 2 行入れようとしてみる (失敗するはず)
--   INSERT INTO daily_bonuses (user_id, amount) VALUES (1, 200);
--   INSERT INTO daily_bonuses (user_id, amount) VALUES (1, 200);  -- ← UNIQUE 違反
--
-- (b) DEFAULT の AT TIME ZONE が効いていることを観察:
--   SELECT id, claimed_on, amount, NOW(), CURRENT_DATE
--     FROM daily_bonuses;
--
-- (c) 別ユーザーの同日は問題なく入る:
--   INSERT INTO daily_bonuses (user_id, amount) VALUES (2, 200);
