-- ============================================================================
-- ch02 / step 2 — characters (= ガチャから出るキャラクター) を足す。
-- ============================================================================
-- ねらい:
--   ・マスタテーブルの典型例を体感する
--   ・CHECK 制約 (rarity が 1..5)
--   ・別テーブルが増えると、後で必要になる FK の準備が整う
-- ============================================================================

DROP TABLE IF EXISTS characters;

CREATE TABLE characters (
    id      BIGSERIAL PRIMARY KEY,
    name    TEXT      NOT NULL UNIQUE,
    rarity  SMALLINT  NOT NULL CHECK (rarity BETWEEN 1 AND 5),
    emoji   TEXT      NOT NULL DEFAULT '❓'
);

INSERT INTO characters (name, rarity, emoji) VALUES
    ('スライム', 1, '🟢'),
    ('ウルフ',   2, '🐺'),
    ('ナイト',   3, '🛡️'),
    ('ペガサス', 4, '🦄'),
    ('ドラゴン', 5, '🐉');

SELECT id, name, rarity, emoji FROM characters ORDER BY rarity DESC, id;

-- 演習:
-- (a) rarity = 9 を入れようとする -> CHECK 違反
--     INSERT INTO characters (name, rarity, emoji) VALUES ('test', 9, 'x');
--
-- (b) name 重複も UNIQUE で弾かれることを確認
--
-- (c) レア度別の件数を SELECT
--     SELECT rarity, COUNT(*) FROM characters GROUP BY rarity ORDER BY rarity;
