# 第11章 ステップ式実習 — アイドル風コイン自動生成

各 step は独立に動きます。step1 → step6 の順に進めると、最終的に
「装備キャラ × 経過秒で coin が貯まる、並行回収しても二重加算しない」
最小サーバが組み上がります。

| step | やること                                              |
| ---- | ----------------------------------------------------- |
| 1    | `users.last_collected_at` 追加 + `equipped_characters` |
| 2    | rate を集計する SELECT (LEFT JOIN + COALESCE)          |
| 3    | `collect()` を素朴に書く (FOR UPDATE 無し)              |
| 4    | `FOR UPDATE OF u` で並行回収を防ぐ                      |
| 5    | `/api/me` エンドポイントで collect を自動呼び出し       |
| 6    | 並行回収を 2 スレッドで再現して検証                     |

## 動作環境

```bash
psql "$DATABASE_URL" -f exercises/ch11/step1_alter_users.sql

# alice (id=1) に ★5 と ★3 のキャラを装備させる例 (キャラ ID は seed.sql 依存)
psql "$DATABASE_URL" -c "
  INSERT INTO equipped_characters (user_id, character_id) VALUES (1, 1), (1, 5)
  ON CONFLICT DO NOTHING;
"

# 最終形を起動
python exercises/ch11/step5_endpoint_with_collect.py

# 別ターミナル
curl http://127.0.0.1:8001/api/me -H 'Authorization: Bearer 1'
```

## 認証
ch10 と同じく `Authorization: Bearer <user_id>` を学習用の偽認証として使う。
