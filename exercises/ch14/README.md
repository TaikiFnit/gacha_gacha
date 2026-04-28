# 第14章 ステップ式実習 — マイグレーション

本物の `db/init.sql` は触らない。ここでは `exercises/ch14/migrations/` 配下に
独立した番号付き SQL を置き、`step3_runner.py` を使って自前で適用していく。

| step | やること                                             |
| ---- | ---------------------------------------------------- |
| 1    | `schema_migrations` テーブル設計                       |
| 2    | 「最初の 1 ファイル」 (0001_initial.sql) を切り出す      |
| 3    | 未適用のファイルを順に流すランナー (Python)            |
| 4    | 列追加 (default 付き) の 0002 を流す                    |
| 5    | backfill → DROP DEFAULT + UNIQUE の 0003 / 0004      |
| 6    | 失敗したマイグレーションの「打ち消し」 0005 パターン     |

## 動作環境

学習用に独立した DB を作って試すのが安全:

```bash
psql "$DATABASE_URL" -c "CREATE DATABASE play_migrate;"
export DATABASE_URL="host=127.0.0.1 port=5432 user=gacha password=gacha dbname=play_migrate"

# step1 だけは手で流す (schema_migrations 自体を作る)
psql "$DATABASE_URL" -f exercises/ch14/step1_schema_migrations_table.sql

# あとは全部ランナーに任せる
python exercises/ch14/step3_runner.py exercises/ch14/migrations
```
