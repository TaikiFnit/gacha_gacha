# 第13章 ステップ式実習 — ランキング / SNS 機能

| step | やること                                              |
| ---- | ----------------------------------------------------- |
| 1    | 所持数ランキング SQL (LEFT JOIN + GROUP BY + RANK)      |
| 2    | レア度別コンプ率 SQL (CTE + COUNT DISTINCT + NULLIF)    |
| 3    | `friendships` テーブル + 自己ループ禁止 / ステート     |
| 4    | `users.public_box BOOLEAN` を追加                       |
| 5    | 認可チェック付き `GET /api/users/:id/box` 最小サーバ    |
| 6    | keyset pagination で「次の 50 位」 を高速に             |

```bash
psql "$DATABASE_URL" -f exercises/ch13/step1_owned_ranking.sql
psql "$DATABASE_URL" -f exercises/ch13/step2_comp_rate_by_rarity.sql
psql "$DATABASE_URL" -f exercises/ch13/step3_friendships_table.sql
psql "$DATABASE_URL" -f exercises/ch13/step4_public_box_column.sql

python exercises/ch13/step5_view_box_with_authz.py
curl http://127.0.0.1:8001/api/users/1/box -H 'Authorization: Bearer 1'  # 自分は見える
curl http://127.0.0.1:8001/api/users/2/box -H 'Authorization: Bearer 1'  # 公開設定次第
```
