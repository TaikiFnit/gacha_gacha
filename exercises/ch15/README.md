# 第15章 ステップ式実習 — 監視・ログ・運用

| step | やること                                          |
| ---- | ------------------------------------------------- |
| 1    | JSON 構造化ロガーを作る (フォーマッタ)             |
| 2    | アクセスログをミドルウェア的に全リクエスト出す      |
| 3    | Postgres の `auto_explain` で遅いクエリ検出         |
| 4    | `/api/metrics` を Prometheus 互換テキストで返す    |
| 5    | `/api/ready` で DB まで含めた readiness probe       |
| 6    | 1〜5 を統合した「観測しやすい」 最小サーバ          |

```bash
python exercises/ch15/step6_full_observable_server.py

curl http://127.0.0.1:8001/api/health
curl http://127.0.0.1:8001/api/ready
curl http://127.0.0.1:8001/api/metrics
```
