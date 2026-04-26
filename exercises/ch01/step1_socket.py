"""ch01 / step 1 — TCPソケットだけでHTTP風の返事を返す。

ゴール:
    HTTP は「テキスト」「TCP の上」「往復1セット」というのを、
    フレームワークなしで体感する。

実行:
    python exercises/ch01/step1_socket.py     (= ターミナル A)
    別ターミナル B で:
        curl -v http://127.0.0.1:9000/

何が起きるか:
    - 9000 番ポートでTCP接続を待つ
    - 1 件接続が来たら、最大 4096 バイト読み取って中身を表示
    - "HTTP/1.1 200 OK ..." という形のテキストを返して切断

確認ポイント:
    1. curl の出力に > GET / HTTP/1.1, > Host: ... のような送信ヘッダが見える
    2. ターミナル A 側に、curl が送ってきたリクエスト全文 (= ただのテキスト) が出る
    3. < HTTP/1.1 200 OK が curl 側に表示される
"""

import socket


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 同じポートですぐ再起動できるようにする小ワザ
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 9000))
    sock.listen()
    print("listening on http://127.0.0.1:9000  (Ctrl+C で終了)")

    try:
        while True:
            conn, addr = sock.accept()
            data = conn.recv(4096)
            print("---- received ----")
            print(data.decode(errors="replace"))
            print("---- end -----")

            body = b"hello, raw tcp\n"
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain; charset=utf-8\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                b"\r\n"
                + body
            )
            conn.sendall(response)
            conn.close()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
