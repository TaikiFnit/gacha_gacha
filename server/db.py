"""DB 接続ヘルパー。

学習用なので、ORM や ConnectionPool 抜きの**最小構成**にしてある。
本番では psycopg_pool.ConnectionPool を使うのが定番だが、
"接続を 1 本張って SQL を投げて受け取る" という核を見せたいので、
ここでは「1 リクエスト = 1 connection」にしている。

`with get_conn() as conn:` で使うと、ブロックを抜けるときに
コミットまたはロールバックしてくれる (psycopg の仕様)。
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


def _conn_params() -> dict:
    """環境変数から接続パラメータの dict を組み立てる。

    .env 等で設定された値を優先し、 無ければ docker-compose のデフォルトを使う。
    psycopg には connection string ではなく <strong>kwargs</strong> として渡す。
    こうしておくと、 接続失敗時に psycopg が例外メッセージへ DSN 全体を載せる
    挙動でも、 password がそのまま stderr に出てしまう事故を避けやすい。
    """
    return dict(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "gacha"),
        user=os.getenv("PGUSER", "gacha"),
        password=os.getenv("PGPASSWORD", "gacha"),
    )


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    """1 リクエスト分の DB 接続を提供する。

    使用例:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                row = cur.fetchone()
    """
    # row_factory=dict_row を指定すると、結果が tuple ではなく dict で返る。
    # クライアントへ JSON で返したい今回の用途と相性が良い。
    conn = psycopg.connect(**_conn_params(), row_factory=dict_row, autocommit=False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def healthcheck() -> bool:
    """DB に届くか確認する。サーバー起動時の早期失敗用。"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception as e:
        print(f"[db] healthcheck failed: {e}")
        return False
