# 第10章 ステップ式実習 — ログインボーナス

各 step は<strong>独立に動く最小サーバ</strong>です。step1 → step6 の順に
コピペしながら機能を積み上げていくと、最終的に Ch.10 のゴール (二重取得を
DB の UNIQUE 制約で物理的に塞いだ daily-claim API) が手元に組み上がります。

進め方:

1. `step1_daily_bonuses_table.sql` を psql で流す (テーブルを作る)
2. `step2_naive_endpoint.py` を起動 → わざと壊して TOCTTOU を観察
3. `step3_unique_safe_endpoint.py` で UNIQUE 制約に守らせる
4. `step4_concurrent_test.py` で 2 リクエスト同時投入を実機で観察
5. `step5_timezone_handling.sql` で日本時間境界の挙動を確認
6. `step6_coin_update_in_tx.py` が最終形 (coins UPDATE まで含めて完成)

| step | やること                                            |
| ---- | --------------------------------------------------- |
| 1    | `daily_bonuses` テーブル + UNIQUE 制約を作る          |
| 2    | SELECT してから INSERT する素朴版 (TOCTTOU バグの種)  |
| 3    | INSERT 一発 + UniqueViolation キャッチで物理保証      |
| 4    | スレッド 2 本で同時投入し片方 200 / 片方 400 を確認   |
| 5    | `Asia/Tokyo` 境界を psql で実験                       |
| 6    | INSERT と coins UPDATE を同一トランザクションに収める |

## 認証について

教材を短く保つため、各 step は <strong>`Authorization: Bearer <数字>` を
そのまま user_id として扱う</strong>「学習用の偽認証」を採用しています。
本物のセッション認証は Ch.7 で学んだ通りで、本章の論点 (UNIQUE 制約) には
無関係なので簡略化しています。

## 動作環境

```bash
# Postgres を docker compose で起動済み前提 (Ch.2 と同じ docker-compose.yml)
# 接続情報は環境変数 DATABASE_URL で渡せる。デフォルトは:
#   host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha
export DATABASE_URL="host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha"

# テーブルを作る
psql "$DATABASE_URL" -f exercises/ch10/step1_daily_bonuses_table.sql

# 例: alice (user_id=1) を 1 件だけ用意 (Ch.7 まで終えていない人向け)
psql "$DATABASE_URL" -c "INSERT INTO users (id, name, pass_hash) VALUES (1, 'alice', 'fake') ON CONFLICT DO NOTHING;"

# サーバを起動 (step ごと)
python exercises/ch10/step3_unique_safe_endpoint.py

# 別ターミナルで叩く
curl -X POST http://127.0.0.1:8001/api/daily/claim -H 'Authorization: Bearer 1'
curl -X POST http://127.0.0.1:8001/api/daily/claim -H 'Authorization: Bearer 1'   # 2回目は 400
```
