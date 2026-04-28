-- ============================================================================
-- ch12 / step 1 — pickup_periods テーブル + GIST インデックスを作る。
-- ============================================================================

DROP TABLE IF EXISTS pickup_periods;

CREATE TABLE pickup_periods (
    id        BIGSERIAL PRIMARY KEY,
    gacha_id  BIGINT    NOT NULL REFERENCES gachas(id) ON DELETE CASCADE,
    period    TSTZRANGE NOT NULL,
    weights   JSONB     NOT NULL,
    note      TEXT
);

CREATE INDEX idx_pickup_active
    ON pickup_periods USING GIST (gacha_id, period);

-- ----------------------------------------------------------------------------
-- 動作確認
-- ----------------------------------------------------------------------------
-- (a) 範囲型の表記:
--   '[)' → 開始は含む、 終了は含まない (半開区間)
--   '[]' → 両端含む / '()' → 両端含まない / '(]' → 開始除外、 終了含む
--
-- (b) 「現在 NOW() に重なる行」 を取り出す問い合わせ:
--   SELECT id, period, weights FROM pickup_periods
--    WHERE gacha_id = 1 AND NOW() <@ period;
--
-- (c) GIST インデックスは「順序が無いデータ」 (範囲型, 幾何, 全文検索) で有効。
--   B-Tree では範囲型のクエリは基本的に効かない。
