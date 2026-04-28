-- ============================================================================
-- ch13 / step 1 — 所持キャラ数ランキング (上位 50)。
-- ============================================================================

-- シンプル版
SELECT u.id, u.name, COUNT(uc.character_id) AS owned
  FROM users u
  LEFT JOIN user_characters uc ON uc.user_id = u.id
 GROUP BY u.id
 ORDER BY owned DESC, u.id ASC
 LIMIT 50;

-- 順位付き版 (RANK / DENSE_RANK / ROW_NUMBER の違いを観察)
SELECT u.id, u.name,
       COUNT(uc.character_id)                                       AS owned,
       RANK()       OVER (ORDER BY COUNT(uc.character_id) DESC)     AS rank,
       DENSE_RANK() OVER (ORDER BY COUNT(uc.character_id) DESC)     AS dense_rank,
       ROW_NUMBER() OVER (ORDER BY COUNT(uc.character_id) DESC, u.id) AS row_no
  FROM users u
  LEFT JOIN user_characters uc ON uc.user_id = u.id
 GROUP BY u.id
 ORDER BY rank, u.id
 LIMIT 50;

-- ----------------------------------------------------------------------------
-- 違い:
--   RANK       同点は同順位、 次は飛び番   (1, 2, 2, 4)
--   DENSE_RANK 同点は同順位、 次は連番     (1, 2, 2, 3)
--   ROW_NUMBER 完全な通し番号             (1, 2, 3, 4)
