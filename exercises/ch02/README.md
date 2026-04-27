# 第2章 ステップ式実習 (playground)

本番 DB (= `gacha` データベース) を汚さないため、 **playground 用のデータベースを別途作って**
そこで遊ぶのを推奨。 Ch.2 の本編は `gacha` で進めますが、 こちらは制約違反を試したり
壊して試行錯誤するための練習場です。

Windows PowerShell で:

```powershell
# 0. play データベースを作る (1 回だけ)
docker exec -it gacha_pg psql -U gacha -d gacha -c "CREATE DATABASE play;"

# 1. 各ステップを流す (Get-Content でファイル内容を流し込む)
Get-Content exercises\ch02\step1_users_only.sql       | docker exec -i gacha_pg psql -U gacha -d play
Get-Content exercises\ch02\step2_characters.sql       | docker exec -i gacha_pg psql -U gacha -d play
Get-Content exercises\ch02\step3_gachas_and_items.sql | docker exec -i gacha_pg psql -U gacha -d play
Get-Content exercises\ch02\step4_user_characters.sql  | docker exec -i gacha_pg psql -U gacha -d play
Get-Content exercises\ch02\step5_join_aggregate.sql   | docker exec -i gacha_pg psql -U gacha -d play

# 2. 対話的に試したいとき
docker exec -it gacha_pg psql -U gacha -d play
```

Git Bash / WSL / macOS / Linux なら従来どおりリダイレクトが使えます:

```bash
docker compose exec -T db psql -U gacha -d play < exercises/ch02/step1_users_only.sql
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
