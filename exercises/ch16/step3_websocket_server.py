"""ch16 / step 3 — WebSocket ブロードキャストサーバ (依存少なめ版)。

ゴール:
    接続中のクライアント全員に向けて、 任意のメッセージをブロードキャストする
    サーバ。 「他人がガチャを引いた」 みたいなイベントを後から差し込める。

    依存:
        pip install websockets

実行:
    python exercises/ch16/step3_websocket_server.py

    # ブロードキャスト送信用の小さなクライアント:
    python -c "
    import asyncio, json, websockets
    async def main():
        async with websockets.connect('ws://127.0.0.1:8765') as ws:
            await ws.send(json.dumps({'type':'pull','user':'alice','rarity':5,'broadcast':True}))
    asyncio.run(main())
    "

設計のポイント:
    本来は HTTP API サーバから「内部 HTTP で 1 イベント POST → WS が broadcast」
    が綺麗。 ここでは依存を websockets だけに留めるため、 メッセージに
    "broadcast": true が含まれていれば全員に転送、 という最小プロトコルにした。
"""
import asyncio
import json
import os
import sys

try:
    import websockets
    from websockets.asyncio.server import serve
except ImportError:
    print("pip install websockets が必要です", file=sys.stderr)
    sys.exit(1)

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8765"))

clients: set = set()


async def broadcast(text: str):
    await asyncio.gather(
        *(c.send(text) for c in clients),
        return_exceptions=True,
    )


async def handler(ws):
    clients.add(ws)
    try:
        async for msg in ws:
            try:
                payload = json.loads(msg)
            except json.JSONDecodeError:
                continue
            if payload.get("broadcast"):
                await broadcast(json.dumps(
                    {k: v for k, v in payload.items() if k != "broadcast"},
                    ensure_ascii=False,
                ))
    finally:
        clients.discard(ws)


async def main():
    print(f"ws://{HOST}:{PORT}  (clients: send {{...,'broadcast':true}} to fan-out)")
    async with serve(handler, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nbye")
