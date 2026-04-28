"""ch11 / step 3 — collect() を素朴に書く (FOR UPDATE 無し版、 後で壊す)。

ゴール:
    「最後の回収から今までの経過秒 × rate」 を計算して coins に加算する関数。
    まずは普通の SELECT/UPDATE で書いて動かす。 step6 で 2 スレッド同時に呼んで
    coin が二重加算されるバグを観察し、 step4 の FOR UPDATE 版で直す。

実行:
    python exercises/ch11/step3_collect_naive.py 1
    # → +N coin (= elapsed * rate)
"""
import os
import sys
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)


def collect_naive(conn, user_id: int) -> int:
    """前回回収から今までの分を加算する。 FOR UPDATE 無し = 並行で壊れる。"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.last_collected_at,
                   COALESCE(SUM(c.rarity), 0) AS rate
              FROM users u
              LEFT JOIN equipped_characters ec ON ec.user_id = u.id
              LEFT JOIN characters         c  ON c.id        = ec.character_id
             WHERE u.id = %s
             GROUP BY u.id
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row is None:
            return 0
        elapsed = (datetime.now(timezone.utc) - row["last_collected_at"]).total_seconds()
        gained = int(elapsed * row["rate"])
        if gained > 0:
            cur.execute(
                "UPDATE users "
                "   SET coins = coins + %s, last_collected_at = NOW() "
                " WHERE id = %s",
                (gained, user_id),
            )
        return gained


def main():
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        before = _coins(conn, user_id)
        gained = collect_naive(conn, user_id)
        after = _coins(conn, user_id)
        print(f"user_id={user_id}: {before} -> {after}  (+{gained})")


def _coins(conn, user_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT coins FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return row["coins"] if row else 0


if __name__ == "__main__":
    main()
