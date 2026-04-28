-- ============================================================================
-- ch12 / step 2 — 「今この瞬間アクティブなピックアップ」 を取り出す。
-- ============================================================================
-- まず期間判定だけ。 weight の適用は step3 でやる。
-- ============================================================================

-- 例として 3 期間を入れる (実行時の NOW() に対して、 過去 / 現在 / 未来)
INSERT INTO pickup_periods (gacha_id, period, weights, note) VALUES
  (1,
   tstzrange(NOW() - INTERVAL '7 days', NOW() - INTERVAL '1 day', '[)'),
   '{"1": 3}', '先週のピックアップ (もう終了)'),
  (1,
   tstzrange(NOW() - INTERVAL '1 hour', NOW() + INTERVAL '23 hours', '[)'),
   '{"1": 6}', '今走っているピックアップ'),
  (1,
   tstzrange(NOW() + INTERVAL '7 days', NOW() + INTERVAL '14 days', '[)'),
   '{"2": 4}', '来週のピックアップ (まだ始まってない)');

-- アクティブな行だけを取り出す
SELECT id, lower(period) AS started_at, upper(period) AS ends_at,
       weights, note
  FROM pickup_periods
 WHERE gacha_id = 1
   AND NOW() <@ period;
-- ↑ 「今走っているピックアップ」 の 1 行だけ返るはず

-- ----------------------------------------------------------------------------
-- 演習
-- ----------------------------------------------------------------------------
-- (a) 範囲演算子いろいろ:
--   tstzrange(...) && tstzrange(...)   ← 重なるか
--   tstzrange(...) @> NOW()            ← NOW() を含むか (上と同じ意味)
--   NOW() <@ period                    ← NOW() が period に含まれるか
--
-- (b) 後始末
--   DELETE FROM pickup_periods;
