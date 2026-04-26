-- ============================================================================
-- ch02 / step 5 — Box (所持キャラ一覧) を JOIN + 集計で組み立てる。
-- ============================================================================
-- ねらい:
--   ・JOIN: 履歴とマスタを繋ぐ
--   ・GROUP BY + COUNT: 同じキャラの所持数を出す
--   ・LEFT JOIN: 「未所持を含めた全キャラ一覧」も出せる
--   ・ウィンドウ関数 SUM(...) OVER (): 排出確率を行ごとに引きずる
-- ============================================================================

-- ----------------------------------------------------------------------------
-- (1) Box: alice が所持しているキャラと、その個数
-- ----------------------------------------------------------------------------
SELECT c.id, c.name, c.rarity, c.emoji,
       COUNT(*) AS count
  FROM user_characters uc
  JOIN characters       c ON c.id = uc.character_id
  JOIN users            u ON u.id = uc.user_id
 WHERE u.name = 'alice'
 GROUP BY c.id
 ORDER BY c.rarity DESC, c.id;

-- ----------------------------------------------------------------------------
-- (2) コンプ表: 全キャラと、alice が持ってる個数 (LEFT JOIN)
-- ----------------------------------------------------------------------------
SELECT c.id, c.name, c.rarity,
       COUNT(uc.id) AS owned_count       -- ← uc.id で数える (NULL は数えられない)
  FROM characters c
  LEFT JOIN user_characters uc
         ON uc.character_id = c.id
        AND uc.user_id = (SELECT id FROM users WHERE name = 'alice')
 GROUP BY c.id
 ORDER BY c.rarity DESC, c.id;

-- ----------------------------------------------------------------------------
-- (3) レア度別コンプ率
-- ----------------------------------------------------------------------------
WITH owned AS (
    SELECT DISTINCT c.id, c.rarity
      FROM characters c
      JOIN user_characters uc ON uc.character_id = c.id
      JOIN users u            ON u.id = uc.user_id
     WHERE u.name = 'alice'
)
SELECT c.rarity,
       COUNT(*)            AS total_chars,
       COUNT(o.id)         AS owned_chars,
       round(COUNT(o.id) * 100.0 / COUNT(*), 1) AS pct
  FROM characters c
  LEFT JOIN owned o ON o.id = c.id
 GROUP BY c.rarity
 ORDER BY c.rarity DESC;

-- ----------------------------------------------------------------------------
-- (4) 通常ガチャの確率テーブル (ウィンドウ関数で1行ごとに分母を持つ)
-- ----------------------------------------------------------------------------
SELECT c.name, c.rarity, c.emoji,
       gi.weight,
       round(gi.weight * 100.0 / sum(gi.weight) over (), 2) AS pct
  FROM gacha_items gi
  JOIN characters c ON c.id = gi.character_id
 WHERE gi.gacha_id = (SELECT id FROM gachas WHERE name='通常ガチャ')
 ORDER BY pct DESC;

-- 演習:
-- (a) 「未所持のSSR (rarity=5) のみ」を返すクエリを書いてみよう
-- (b) 「全ユーザーの所持数ランキング (1人1行, 多い順)」を出してみよう
-- (c) (4) の結果を、累積確率 (running total) も追加して出してみよう
--     ヒント: SUM(weight) OVER (ORDER BY weight DESC ROWS UNBOUNDED PRECEDING)
