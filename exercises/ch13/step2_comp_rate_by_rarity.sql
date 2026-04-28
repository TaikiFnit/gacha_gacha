-- ============================================================================
-- ch13 / step 2 — レア度別コンプ率ランキング (★5 を全 X 体中 何体持っているか)。
-- ============================================================================
-- 母数 (マスタ) と分子 (所持) を別 SELECT で出して JOIN するのが定石。
-- ============================================================================

WITH total AS (
    SELECT COUNT(*) AS n FROM characters WHERE rarity = 5
),
owned AS (
    SELECT u.id, u.name,
           COUNT(DISTINCT c.id) AS got    -- ← 重複所持を 1 体扱いにする
      FROM users u
      LEFT JOIN user_characters uc ON uc.user_id = u.id
      LEFT JOIN characters     c   ON c.id = uc.character_id AND c.rarity = 5
     GROUP BY u.id
)
SELECT o.id, o.name, o.got, t.n,
       ROUND(o.got::numeric / NULLIF(t.n, 0) * 100, 1) AS comp_pct
  FROM owned o, total t
 ORDER BY comp_pct DESC NULLS LAST, o.id
 LIMIT 50;

-- ----------------------------------------------------------------------------
-- 落とし穴
-- ----------------------------------------------------------------------------
-- (a) DISTINCT を忘れると、 同じキャラを 5 体持っているユーザーが「5 体コンプ」 扱い
-- (b) NULLIF(t.n, 0) を忘れると、 母数 0 でゼロ除算エラー
-- (c) NULLS LAST を付けないと、 NULL (= 母数 0 のとき) が先頭に来る
