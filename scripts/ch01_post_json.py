"""第1章 / 練習2: POST で JSON を受け取り、JSON で返す。

実行:
    python scripts/ch01_post_json.py

別ターミナル:
    curl -X POST http://127.0.0.1:8002/ \\
         -H "Content-Type: application/json" \\
         -d '{"name":"alice","level":3}'

応答:
    {"received": {"name": "alice", "level": 3}, "len": 26}

意図:
    本システムの server/app.py のエコー版にあたる、最小実装。
    Content-Length / rfile / json.loads / send_header の段取りを覚える。
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Echo(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return
        self._send(200, {"received": payload, "len": len(raw)})

    # GET も用意しておくと、ブラウザで開いたときに 405 でなく案内が出てわかりやすい
    def do_GET(self):  # noqa: N802
        self._send(405, {"error": "send POST with JSON body"})

    def _send(self, status: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{self.command}] {self.path} -> {fmt % args}")


def main() -> None:
    addr = ("127.0.0.1", 8002)
    server = HTTPServer(addr, Echo)
    print(f"listening on http://{addr[0]}:{addr[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
