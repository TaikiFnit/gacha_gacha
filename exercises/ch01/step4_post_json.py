"""ch01 / step 4 — POST で JSON を受け取り、加工して返す。

ゴール:
    本物のWeb APIで頻出する「ボディからJSONを読む」を覚える。
    Content-Length / rfile / json.loads / json.dumps の往復を完全に書ける状態を目指す。

実装する API:
    POST /api/echo
        body: {"name": "alice", "age": 7}
        resp: {"received": {...}, "size": 23}
    POST /api/sum
        body: {"a": 1, "b": 2}
        resp: {"answer": 3}
    どちらも JSON 不正なら 400, 必須キー欠損なら 400, それ以外は 200。

実行:
    python exercises/ch01/step4_post_json.py
    curl -X POST http://127.0.0.1:8001/api/echo \\
         -H "Content-Type: application/json" \\
         -d '{"name":"alice","age":7}'
    curl -X POST http://127.0.0.1:8001/api/sum \\
         -H "Content-Type: application/json" \\
         -d '{"a":1,"b":2}'

宿題:
    1. /api/sum で a, b の片方が文字列だったら 400 を返すよう厳しくしよう
    2. /api/echo の応答に "method": "POST" を追加してみよう
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


class App(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        try:
            body = self._read_json()
        except ValueError as e:
            return self._json(400, {"error": f"invalid json: {e}"})

        if path == "/api/echo":
            return self._json(200, {"received": body,
                                    "size": len(json.dumps(body).encode())})
        if path == "/api/sum":
            try:
                a, b = body["a"], body["b"]
            except KeyError:
                return self._json(400, {"error": "a と b が必要"})
            return self._json(200, {"answer": a + b})

        return self._json(404, {"error": "Not Found"})

    # ---- helpers --------------------------------------------------------
    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _json(self, status: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    addr = ("127.0.0.1", 8001)
    print(f"listening on http://{addr[0]}:{addr[1]}")
    HTTPServer(addr, App).serve_forever()


if __name__ == "__main__":
    main()
