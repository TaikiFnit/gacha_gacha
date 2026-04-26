"""ch01 / step 3 — パスごとに違う応答を返す (= "ルーティング"の素朴版)。

ゴール:
    self.path で分岐するという素朴な実装を体験する。
    クエリ文字列 (?msg=...) のパースも urllib.parse でやってみる。

実装する API:
    GET /              -> "hello, http\\n"
    GET /api/health    -> JSON {"status": "ok"}
    GET /api/echo?msg=X -> JSON {"you_said": "X"}
    その他              -> 404 + JSON {"error": "Not Found"}

実行:
    python exercises/ch01/step3_routing.py
    curl http://127.0.0.1:8001/
    curl http://127.0.0.1:8001/api/health
    curl 'http://127.0.0.1:8001/api/echo?msg=hi%20there'
    curl -i http://127.0.0.1:8001/nope    # -i でステータス行も表示

宿題:
    1. /api/echo に msg が無いとき、現在は空文字を返す。400 を返すように変えてみよう
    2. /api/time を増やして、現在時刻 (datetime.utcnow().isoformat()) を返してみよう
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


class App(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        path = url.path
        query = parse_qs(url.query)

        if path == "/":
            self._text(200, "hello, http\n")
        elif path == "/api/health":
            self._json(200, {"status": "ok"})
        elif path == "/api/echo":
            msg = query.get("msg", [""])[0]
            self._json(200, {"you_said": msg})
        else:
            self._json(404, {"error": "Not Found", "path": path})

    # -- helpers ----------------------------------------------------------
    def _text(self, status: int, s: str) -> None:
        body = s.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
