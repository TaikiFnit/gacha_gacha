-- ============================================================================
-- ch02 / step 3 — ガチャ筐体 + 排出設定 (多対多 + 重み)。
-- ============================================================================
-- ねらい:
--   ・「複数のガチャに、複数のキャラが、それぞれ違う重みで登場する」を
--     リレーショナルに表現する = 中間テーブル
--   ・FK + UNIQUE(複合) + CHECK(weight>0)
--
-- 前提: step1, step2 を流した後の前提で動く (users / characters がある)。
-- ============================================================================

DROP TABLE IF EXISTS gacha_items;
DROP TABLE IF EXISTS gachas;

CREATE TABLE gachas (
    id    BIGSERIAL PRIMARY KEY,
    name  TEXT      NOT NULL UNIQUE,
    price INTEGER   NOT NULL CHECK (price > 0)
);

CREATE TABLE gacha_items (
    id           BIGSERIAL PRIMARY KEY,
    gacha_id     BIGINT    NOT NULL REFERENCES gachas(id)     ON DELETE CASCADE,
    character_id BIGINT    NOT NULL REFERENCES characters(id) ON DELETE RESTRICT,
    weight       INTEGER   NOT NULL CHECK (weight > 0),
    UNIQUE (gacha_id, character_id)
);

INSERT INTO gachas (name, price) VALUES
    ('通常ガチャ',     100),
    ('プレミアムガチャ', 300);

-- 通常ガチャは全レア度をバランス良く
INSERT INTO gacha_items (gacha_id, character_id, weight)
SELECT g.id, c.id,
       CASE c.rarity WHEN 1 THEN 60
                     WHEN 2 THEN 30
                     WHEN 3 THEN 20
                     WHEN 4 THEN 8
                     WHEN 5 THEN 2 END
  FROM gachas g, characters c
 WHERE g.name = '通常ガチャ';

-- プレミアムは レア度 3 以上のみ、SSR 厚め
INSERT INTO gacha_items (gacha_id, character_id, weight)
SELECT g.id, c.id,
       CASE c.rarity WHEN 3 THEN 50
                     WHEN 4 THEN 20
                     WHEN 5 THEN 10 END
  FROM gachas g, characters c
 WHERE g.name = 'プレミアムガチャ' AND c.rarity >= 3;

-- 排出表 (ガチャごとの確率) を一気に見る:
SELECT g.name        AS gacha,
       c.name        AS chara,
       c.rarity,
       gi.weight,
       round(gi.weight * 100.0 / sum(gi.weight) over (partition by g.id), 2) AS pct
  FROM gacha_items gi
  JOIN gachas      g ON g.id = gi.gacha_id
  JOIN characters  c ON c.id = gi.character_id
 ORDER BY g.id, gi.weight DESC;

-- 演習:
-- (a) 同じ (gacha_id, character_id) を二重に入れたらどうなる?
--     INSERT INTO gacha_items (gacha_id, character_id, weight) VALUES (1, 1, 10);
--   → UNIQUE 違反
--
-- (b) 存在しない gacha_id を入れたら?
--     INSERT INTO gacha_items (gacha_id, character_id, weight) VALUES (9999, 1, 10);
--   → FK 違反
--
-- (c) characters から「使われている」キャラを消そうとする
--     DELETE FROM characters WHERE id = 1;
--   → ON DELETE RESTRICT で守られる
--
-- (d) 通常ガチャを丸ごと消すと、gacha_items はどうなる?
--     DELETE FROM gachas WHERE name = '通常ガチャ';
--   → ON DELETE CASCADE で gacha_items の該当行も消える
