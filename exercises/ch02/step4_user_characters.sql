-- ============================================================================
-- ch02 / step 4 — ユーザー所持品 (= ガチャ結果の履歴) を入れる。
-- ============================================================================
-- ねらい:
--   ・「同じキャラを何度引いてもOK」を履歴行で表現する
--   ・ガチャを引く一連の処理 (coins -100, user_characters に1行) を
--     トランザクションで束ねる
--   ・FOR UPDATE で行ロックする意味を体験する
-- ============================================================================

DROP TABLE IF EXISTS user_characters;

CREATE TABLE user_characters (
    id           BIGSERIAL   PRIMARY KEY,
    user_id      BIGINT      NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
    character_id BIGINT      NOT NULL REFERENCES characters(id) ON DELETE RESTRICT,
    obtained_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_characters_user ON user_characters(user_id);

-- ----------------------------------------------------------------------------
-- alice が通常ガチャを 1 回引いてスライムが当たったぞ! を SQLで再現
-- ----------------------------------------------------------------------------
BEGIN;

-- coins と price をロックして読む (二重消費を防ぐ)
SELECT coins FROM users WHERE name = 'alice' FOR UPDATE;

-- 価格分減らす
UPDATE users
   SET coins = coins - 100
 WHERE name = 'alice'
RETURNING coins;   -- ← 残高を返してもらう

-- 履歴に追加
INSERT INTO user_characters (user_id, character_id)
SELECT u.id, c.id
  FROM users u, characters c
 WHERE u.name = 'alice' AND c.name = 'スライム'
RETURNING id, obtained_at;

COMMIT;

-- 確認
SELECT u.name AS user, c.name AS chara, uc.obtained_at
  FROM user_characters uc
  JOIN users      u ON u.id = uc.user_id
  JOIN characters c ON c.id = uc.character_id
 ORDER BY uc.id;

-- 演習:
-- (a) BEGIN -> SELECT FOR UPDATE のあと、別のpsqlセッションを開いて
--     同じ alice の coins を SELECT してみると何が起きる?
--     (試したら必ず ROLLBACK か COMMIT で閉じること)
--
-- (b) coins を引かずに INSERT だけしてみる -> どこにも怒られない?
--     → だから「ロジックを TRANSACTION で束ねる」のが大事という話につながる
--
-- (c) 同じキャラを5回引いた状態を再現するには?
--     INSERT INTO user_characters (user_id, character_id)
--     SELECT u.id, c.id FROM users u, characters c, generate_series(1,5)
--      WHERE u.name='alice' AND c.name='スライム';
