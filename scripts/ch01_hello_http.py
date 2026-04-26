"""第1章 / 練習1: フレームワークなしの Hello サーバー。

実行:
    python scripts/ch01_hello_http.py

別ターミナル:
    curl -v http://127.0.0.1:8001/
    curl -v http://127.0.0.1:8001/anything
    curl -v http://127.0.0.1:8001/?name=alice

ポイント:
    - do_GET: GET メソッド全般を処理する。サブクラスでオーバーライドする。
    - send_response → send_header → end_headers → wfile.write の順を必ず守る。
    - body は bytes。文字列は .encode() を通して送る。
"""
from http.server import BaseHTTPRequestHandler, HTTPServer


class Hello(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = f"hello, http\nyou requested: {self.path}\n".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # アクセスログを少し読みやすく
    def log_message(self, fmt, *args):
        print(f"[{self.command}] {self.path}")


def main() -> None:
    addr = ("127.0.0.1", 8001)
    server = HTTPServer(addr, Hello)
    print(f"listening on http://{addr[0]}:{addr[1]}  (Ctrl+C で終了)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
