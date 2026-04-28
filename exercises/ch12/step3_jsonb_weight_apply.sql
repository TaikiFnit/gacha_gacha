-- ============================================================================
-- ch12 / step 3 — JSONB weight を取り出して、 倍率として gacha_items に乗せる。
-- ============================================================================
-- LEFT JOIN LATERAL を使って「アクティブ期間にこのキャラがピックアップされていれば
-- その倍率、 されていなければ 1」 を gi.weight に掛け算する。
-- ============================================================================

-- 確認用クエリ (gacha_id = 1 を例に)
SELECT gi.character_id,
       gi.weight                                AS base_weight,
       COALESCE(p.mult, 1)                      AS mult,
       gi.weight * COALESCE(p.mult, 1)          AS effective_weight
  FROM gacha_items gi
  LEFT JOIN LATERAL (
        SELECT (pp.weights ->> gi.character_id::text)::numeric AS mult
          FROM pickup_periods pp
         WHERE pp.gacha_id = gi.gacha_id
           AND NOW() <@ pp.period
           AND pp.weights ? gi.character_id::text
         LIMIT 1
       ) p ON TRUE
 WHERE gi.gacha_id = 1
 ORDER BY gi.character_id;

-- ----------------------------------------------------------------------------
-- 読み方
-- ----------------------------------------------------------------------------
-- (a) JSONB 演算子:
--   weights ? 'key'        ← key が存在するか (boolean)
--   weights -> 'key'       ← JSON 値として取り出し
--   weights ->> 'key'      ← テキストとして取り出し (型は text)
--   ::numeric              ← 数値型にキャスト
--
-- (b) LATERAL は「外側の行ごとに、 内側のサブクエリを再評価」 する書き方。
--   pickup_periods に複数のヒットがあっても LIMIT 1 で 1 件に絞る。
--   サービス方針として「重ねて掛ける」 のが正しいなら集約 (SUM や AVG) を使う。
--
-- (c) COALESCE(p.mult, 1) ← ピックアップに無いキャラは 1 倍 = 普段の weight のまま。
