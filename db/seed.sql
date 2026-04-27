-- ===========================================================================
-- 初期データ
-- ・キャラクター 12 体 (レア度 1〜5)
-- ・ガチャ筐体 2 個 (通常ガチャ / レアガチャ)
-- ・各ガチャの排出設定
--
-- ON CONFLICT DO NOTHING を付けてあるので、 何度実行しても二重投入されない。
--
-- ⚠️ id を手で振っている理由:
--   gacha_items が character_id / gacha_id を数値で直接参照しているため、
--   seed の段階で id が確定している必要がある。 BIGSERIAL に任せると、
--   再実行や追加投入で id がズレて gacha_items の参照が壊れ得る。
--   下の SELECT setval(...) は、 手で振った最大 id まで sequence を進める。
--
-- 🔁 DB を完全にリセットしたい場合:
--   docker compose down -v   # ボリュームごと消す
--   docker compose up -d     # schema.sql + seed.sql が再投入される
--
--   または既存 DB に対して:
--     TRUNCATE characters, gachas, gacha_items, user_characters,
--              users, sessions RESTART IDENTITY CASCADE;
--     \i db/seed.sql
-- ===========================================================================

INSERT INTO characters (id, name, rarity, emoji) VALUES
    ( 1, 'スライム',       1, '🟢'),
    ( 2, 'コウモリ',       1, '🦇'),
    ( 3, 'ゴブリン',       1, '👺'),
    ( 4, 'ウルフ',         2, '🐺'),
    ( 5, 'マーメイド',     2, '🧜'),
    ( 6, 'ナイト',         3, '🛡️'),
    ( 7, 'ウィザード',     3, '🧙'),
    ( 8, 'ペガサス',       4, '🦄'),
    ( 9, 'ドラゴンの卵',   4, '🥚'),
    (10, 'ドラゴン',       5, '🐉'),
    (11, '不死鳥',         5, '🔥'),
    (12, '伝説の勇者',     5, '⚔️')
ON CONFLICT (id) DO NOTHING;

-- characters の id は手で振ったので sequence を進める
SELECT setval(pg_get_serial_sequence('characters', 'id'),
              (SELECT MAX(id) FROM characters));

INSERT INTO gachas (id, name, price) VALUES
    (1, '通常ガチャ',      100),
    (2, 'プレミアムガチャ', 300)
ON CONFLICT (id) DO NOTHING;

SELECT setval(pg_get_serial_sequence('gachas', 'id'),
              (SELECT MAX(id) FROM gachas));

-- ---------------------------------------------------------------------------
-- 通常ガチャ: コモン多め、SSR はちょこっと
--   weight 合計 = 100 + 100 + 100 + 60 + 60 + 30 + 30 + 10 + 10 + 2 + 2 + 1 = 505
--   → スライム = 100/505 ≒ 19.8%, 伝説の勇者 = 1/505 ≒ 0.2%
-- ---------------------------------------------------------------------------
INSERT INTO gacha_items (gacha_id, character_id, weight) VALUES
    (1,  1, 100), (1,  2, 100), (1,  3, 100),
    (1,  4,  60), (1,  5,  60),
    (1,  6,  30), (1,  7,  30),
    (1,  8,  10), (1,  9,  10),
    (1, 10,   2), (1, 11,   2), (1, 12,   1)
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- プレミアムガチャ: レア度3以上のみ。SSRは出やすめ。
-- ---------------------------------------------------------------------------
INSERT INTO gacha_items (gacha_id, character_id, weight) VALUES
    (2,  6,  50), (2,  7,  50),
    (2,  8,  25), (2,  9,  25),
    (2, 10,   8), (2, 11,   8), (2, 12,   4)
ON CONFLICT DO NOTHING;
