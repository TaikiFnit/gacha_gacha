# 第2章 ステップ式実習

本番DBを汚さないため、**playground用のDBを作って**そこで遊ぶのを推奨。

```bash
# ホスト側から:
docker compose exec -T db psql -U gacha -d gacha -c "CREATE DATABASE play;"

# 各ステップを流す
docker compose exec -T db psql -U gacha -d play < exercises/ch02/step1_users_only.sql
docker compose exec -T db psql -U gacha -d play < exercises/ch02/step2_characters.sql
docker compose exec -T db psql -U gacha -d play < exercises/ch02/step3_gachas_and_items.sql
docker compose exec -T db psql -U gacha -d play < exercises/ch02/step4_user_characters.sql
docker compose exec -T db psql -U gacha -d play < exercises/ch02/step5_join_aggregate.sql

# 対話的に試したいときは
docker compose exec db psql -U gacha -d play
```

| step | やること                          |
| ---- | --------------------------------- |
| 1    | users だけ作る + 制約に触れる     |
| 2    | characters マスタを足す           |
| 3    | gachas + 多対多の中間テーブル     |
| 4    | user_characters + トランザクション |
| 5    | JOIN / GROUP BY / ウィンドウ関数  |
| 6    | わざと制約違反させる演習          |

step5 まで仕上がると、`server/app.py` の `GET /api/box` が
発行している SQL がすんなり読める状態になります。
