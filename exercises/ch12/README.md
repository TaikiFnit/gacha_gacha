# 第12章 ステップ式実習 — ピックアップガチャ

「期間限定で特定キャラの確率が上がる」 を、 マスタ (`gacha_items.weight`) を
書き換えずに後付けで重ねる設計。

| step | やること                                                |
| ---- | ------------------------------------------------------- |
| 1    | `pickup_periods` テーブル + GIST インデックス             |
| 2    | アクティブな期間を `NOW() <@ period` で取り出す SELECT    |
| 3    | JSONB の weight を取り出し、 倍率として適用する SELECT     |
| 4    | `fetch_pool()` を改造したガチャ抽選サーバ最小一式        |
| 5    | EXPLAIN ANALYZE で GIST インデックス効果を比較           |
| 6    | 期間内 / 期間外で抽選分布が変わるのを 1 万回サンプリング  |

## 動作環境

```bash
psql "$DATABASE_URL" -f exercises/ch12/step1_pickup_periods_table.sql

# 例: 今日のうちだけドラゴン (character_id=1) を 6 倍にするピックアップ
psql "$DATABASE_URL" -c "
  INSERT INTO pickup_periods (gacha_id, period, weights, note) VALUES
    (1,
     tstzrange(NOW() - INTERVAL '1 hour', NOW() + INTERVAL '23 hours', '[)'),
     '{\"1\": 6}',
     'テスト用ピックアップ');
"

# 抽選サーバ
python exercises/ch12/step4_fetch_pool_lateral.py
curl -X POST http://127.0.0.1:8001/api/gacha/pull \
     -H 'Authorization: Bearer 1' -H 'Content-Type: application/json' \
     -d '{"gacha_id": 1}'
```
