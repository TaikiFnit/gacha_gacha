-- ============================================================================
-- ch10 / step 5 — タイムゾーン境界の挙動を psql で観察する。
-- ============================================================================
-- 「日本時間で日付が変わったら新しいボーナスをもらえる」 を実現するために、
-- step1 のテーブルでは DEFAULT (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')::date を
-- 入れている。 これがなぜ必要か、 接続のタイムゾーンを切り替えて観察する。
--
-- 実行:
--   psql "$DATABASE_URL" -f exercises/ch10/step5_timezone_handling.sql
-- ============================================================================

-- 0. クリーンアップ (再実行可能にする)
DELETE FROM daily_bonuses WHERE user_id IN (1, 2);

-- ----------------------------------------------------------------------------
-- 1. 接続のタイムゾーンを UTC にして INSERT してみる
-- ----------------------------------------------------------------------------
SET TIME ZONE 'UTC';

-- 観察ポイント: 接続が UTC でも、 DEFAULT は AT TIME ZONE 'Asia/Tokyo' で
-- 日本時間の日付になっている。
INSERT INTO daily_bonuses (user_id, amount) VALUES (1, 200)
RETURNING id, user_id, claimed_on, amount, NOW() AS server_now;

-- 確認: claimed_on は日本時間の今日になっているはず
SELECT id, user_id, claimed_on,
       NOW() AT TIME ZONE 'UTC'        AS now_utc,
       NOW() AT TIME ZONE 'Asia/Tokyo' AS now_jst
  FROM daily_bonuses
 WHERE user_id = 1;

-- ----------------------------------------------------------------------------
-- 2. もし DEFAULT を CURRENT_DATE (TZ 指定なし) にしてしまうと…
-- ----------------------------------------------------------------------------
-- アプリ言語側で date を作って渡すと、 接続の TZ に引きずられる。
-- 試しに UTC 接続のまま現在日付 (UTC) を直接書き込むとこうなる:

INSERT INTO daily_bonuses (user_id, claimed_on, amount)
     VALUES (2, CURRENT_DATE, 200)
  RETURNING user_id, claimed_on AS utc_date;

-- ↑ 日本時間 0〜9 時の間に実行すると、 claimed_on が「前日」 になるはず。
--    日本のユーザー目線で「日付変わったのにまだ昨日扱い」 = バグ。

-- 後始末
SET TIME ZONE DEFAULT;

-- ----------------------------------------------------------------------------
-- 演習
-- ----------------------------------------------------------------------------
-- (a) ALTER TABLE で DEFAULT を一度 CURRENT_DATE (TZ 無し) に書き換えて、
--     UTC 接続で INSERT したら何日が入るか試す → 戻す
--   ALTER TABLE daily_bonuses ALTER COLUMN claimed_on SET DEFAULT CURRENT_DATE;
--   ... (実験)
--   ALTER TABLE daily_bonuses ALTER COLUMN claimed_on
--       SET DEFAULT (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')::date;
--
-- (b) Asia/Tokyo の今日の終わりを SQL で計算してみる:
--     SELECT (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' + INTERVAL '1 day')::timestamptz;
