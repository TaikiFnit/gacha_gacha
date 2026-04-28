-- ============================================================================
-- ch12 / step 5 — GIST インデックス有り / 無しで EXPLAIN ANALYZE を比較。
-- ============================================================================
-- pickup_periods が大きく育ったとき、 GIST が無いと範囲条件 (NOW() <@ period)
-- が Seq Scan になり遅い。 体感で違いを見るために 1 万行流し込み、 比較する。
-- ============================================================================

-- 1. 既存データを退避
DROP TABLE IF EXISTS pickup_periods_bench;
CREATE TABLE pickup_periods_bench (LIKE pickup_periods INCLUDING ALL);

-- 2. ランダムに 1 万件流し込む
INSERT INTO pickup_periods_bench (gacha_id, period, weights, note)
SELECT 1,
       tstzrange(
         NOW() - (random() * INTERVAL '365 days'),
         NOW() - (random() * INTERVAL '365 days') + INTERVAL '1 day',
         '[)'
       ),
       jsonb_build_object((1 + (random()*9)::int)::text, 2 + (random()*5)::int),
       'bench'
  FROM generate_series(1, 10000);

-- 必ず 1 件は「今アクティブ」 を入れる
INSERT INTO pickup_periods_bench (gacha_id, period, weights, note)
VALUES (1,
        tstzrange(NOW() - INTERVAL '1 hour', NOW() + INTERVAL '23 hours', '[)'),
        '{"1": 6}', 'active');

-- 3. インデックス無しで EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM pickup_periods_bench
 WHERE gacha_id = 1 AND NOW() <@ period;
-- ↑ Seq Scan + Filter になっているはず。 行数が多いほど遅い。

-- 4. GIST インデックスを張る
CREATE INDEX idx_pickup_bench_gist
    ON pickup_periods_bench USING GIST (gacha_id, period);

-- 5. もう一度 EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM pickup_periods_bench
 WHERE gacha_id = 1 AND NOW() <@ period;
-- ↑ Bitmap Index Scan + Recheck に変わり、 行数に対する依存度が下がる

-- 6. 後始末
-- DROP TABLE pickup_periods_bench;
