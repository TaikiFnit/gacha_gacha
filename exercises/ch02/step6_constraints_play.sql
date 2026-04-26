-- ============================================================================
-- ch02 / step 6 — 制約に "わざと殴られる" 演習。
-- ============================================================================
-- DB の良さは「自分から間違いを教えてくれる」こと。
-- このファイルは敢えて全部失敗するクエリ集。
-- それぞれエラーメッセージをよく読んで、何が守られているのか言語化しよう。
-- (1 行ずつ psql に貼り付けて確認するのがおすすめ。)
-- ============================================================================

-- 1. NOT NULL: 必須カラムを欠落させる
INSERT INTO users (name) VALUES ('no_pass');
-- → ERROR:  null value in column "pass_hash" of relation "users" violates not-null constraint

-- 2. UNIQUE: name の重複
INSERT INTO users (name, pass_hash) VALUES ('alice', 'h');
-- → ERROR:  duplicate key value violates unique constraint "users_name_key"

-- 3. CHECK: rarity 範囲外
INSERT INTO characters (name, rarity, emoji) VALUES ('boss', 9, '😈');
-- → ERROR:  new row for relation "characters" violates check constraint "characters_rarity_check"

-- 4. CHECK: weight が 0
INSERT INTO gacha_items (gacha_id, character_id, weight) VALUES (1, 1, 0);
-- → ERROR:  ... violates check constraint "gacha_items_weight_check"

-- 5. FK (参照先がない)
INSERT INTO gacha_items (gacha_id, character_id, weight) VALUES (9999, 1, 1);
-- → ERROR:  insert or update on table "gacha_items" violates foreign key constraint ...

-- 6. ON DELETE RESTRICT: 参照されてるキャラを消そうとする
DELETE FROM characters WHERE id = 1;
-- → ERROR:  update or delete on table "characters" violates foreign key constraint
--           "user_characters_character_id_fkey" on table "user_characters"

-- 7. (Postgres特有) 型ミスマッチ: TEXT を期待するカラムに数値リテラルを直接
--   psql は気を利かせて変換してしまうので、これはあまり踏まない。

-- 8. トランザクションの ROLLBACK で「途中まで」が無かったことになる
BEGIN;
  INSERT INTO users (name, pass_hash) VALUES ('eve', 'h');
  -- ここでわざと失敗
  INSERT INTO users (name, pass_hash) VALUES ('eve', 'h');  -- UNIQUE違反
ROLLBACK;
-- 上の eve も入っていない:
SELECT * FROM users WHERE name = 'eve';   -- 0 rows
