# 第16章 ステップ式実習 — フロントの本気化

| step | やること                                              |
| ---- | ----------------------------------------------------- |
| 1    | API 通信層を `api.js` に集約 (フレームワーク非依存)     |
| 2    | 状態 store を 100 行で書く (Zustand 等を使わずに)       |
| 3    | WebSocket ブロードキャストサーバ (Python)              |
| 4    | WS クライアント側ミニ HTML (タイムライン表示)         |
| 5    | ガチャ演出アニメ (CSS + 段階再生)                       |
| 6    | API 互換性 smoke テスト (フロント刷新時の安全網)        |

## 動作環境

```bash
# WS サーバを起動 (要 pip install websockets)
python exercises/ch16/step3_websocket_server.py

# 別シェルで HTML を配信
python -m http.server 5500 --directory exercises/ch16

# ブラウザで:
#   http://localhost:5500/step4_ws_client.html
#   http://localhost:5500/step5_pull_with_effect.html
```

> 本物の `web/` は触らない。 ここは「方針論を実機で確認する」 ためのサンドボックス。
