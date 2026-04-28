"""ch11 / step 6 — 並行回収を 2 スレッドで再現して、 二重加算が起きるか観察。

ゴール:
    step3 (FOR UPDATE 無し) と step4 (FOR UPDATE OF u 付き) を切り替えて、
    coin の加算量が変わるのを実機で観察する。

手順:
    1. last_collected_at を意図的に過去にずらす:
       psql "$DATABASE_URL" \
         -c "UPDATE users SET last_collected_at = NOW() - INTERVAL '60 seconds' WHERE id = 1;"

    2. 比較する関数を切り替える (このファイルの IMPL 変数)
       - "naive"      → step3 の collect_naive
       - "for_update" → step4 の collect

    3. 実行:
       python exercises/ch11/step6_concurrent_collect_test.py

期待結果:
    naive:      2 スレッドが同じ rate × elapsed を同時に観測 → +120 coin (60秒 × 1秒) が <strong>2 倍</strong>に近い量加算
    for_update: 片方が COMMIT する間もう一方は待つ → ほぼ +60 coin 相当 1 回分のみ

注意:
    naive の二重加算は<strong>必ず</strong>再現するわけではない (タイミング次第)。
    last_collected_at をかなり古めに振ると顕在化しやすい。
"""
import os
import sys
import threading

import psycopg
from psycopg.rows import dict_row

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)

# どちらの実装を使うか切り替える
IMPL = os.environ.get("CH11_IMPL", "for_update")   # "naive" or "for_update"

USER_ID = 1
N = 2   # 同時実行数


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _connect():
    return psycopg.connect(DSN, row_factory=dict_row)


if IMPL == "naive":
    from step3_collect_naive import collect_naive as _collect   # noqa: E402
elif IMPL == "for_update":
    from step4_collect_for_update import collect as _collect    # noqa: E402
else:
    print(f"unknown CH11_IMPL={IMPL!r}", file=sys.stderr)
    sys.exit(2)


def _coins(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT coins FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()["coins"]


def fire():
    with _connect() as conn:
        _collect(conn, USER_ID)


def main():
    with _connect() as conn:
        before = _coins(conn, USER_ID)

    threads = [threading.Thread(target=fire) for _ in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    with _connect() as conn:
        after = _coins(conn, USER_ID)

    print(f"impl={IMPL}  threads={N}  coins {before} -> {after}  (delta={after - before})")


if __name__ == "__main__":
    main()
