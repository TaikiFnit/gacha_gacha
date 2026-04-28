-- ============================================================================
-- ch11 / step 2 — 「装備の rarity 合計 = rate」 を集計する SELECT。
-- ============================================================================
-- 装備 0 体のユーザーも 0 として 1 行返したいので LEFT JOIN + COALESCE。
-- INNER JOIN だと装備 0 のユーザーが行ごと消えてバグになる。
-- ============================================================================

-- 全ユーザーの rate
SELECT u.id, u.name, u.last_collected_at,
       COALESCE(SUM(c.rarity), 0) AS rate
  FROM users u
  LEFT JOIN equipped_characters ec ON ec.user_id = u.id
  LEFT JOIN characters         c  ON c.id        = ec.character_id
 GROUP BY u.id
 ORDER BY u.id;

-- 単一ユーザーだけ取り出す形 (collect() で使う)
-- ↓ ここに WHERE u.id = :user_id を足すだけで Python から呼べる
SELECT u.id, u.last_collected_at,
       COALESCE(SUM(c.rarity), 0) AS rate
  FROM users u
  LEFT JOIN equipped_characters ec ON ec.user_id = u.id
  LEFT JOIN characters         c  ON c.id        = ec.character_id
 WHERE u.id = 1
 GROUP BY u.id;

-- ----------------------------------------------------------------------------
-- 演習
-- ----------------------------------------------------------------------------
-- (a) LEFT JOIN を INNER JOIN に書き換えると、 装備 0 体のユーザーが消えるのを観察
-- (b) ★5 だけを 2 倍カウントしたいときどうする?
--     ヒント: SUM(CASE WHEN c.rarity = 5 THEN 2 ELSE 1 END * c.rarity)
