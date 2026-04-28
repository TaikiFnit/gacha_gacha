"""ch11 / step 4 — FOR UPDATE OF u で並行回収を防ぐ。

ゴール:
    step3 の collect_naive() は 2 スレッドが同時に呼ぶと、 両方が同じ
    last_collected_at を読んで二重加算してしまう。 SELECT に
    FOR UPDATE OF u を足して、 「自分の users 行に行ロック」 をかけることで
    一方が COMMIT するまでもう一方が SELECT で待たされるようにする。

    OF u ← ロック対象を明示しないと、 JOIN している characters マスタまで
    ロックされて他ユーザーまで巻き込まれる。

実行:
    python exercises/ch11/step4_collect_for_update.py 1
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


def collect(conn, user_id: int) -> int:
    """前回回収から今までの分を加算する。 行ロックで並行安全。"""
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
             FOR UPDATE OF u
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
        with conn.cursor() as cur:
            cur.execute("SELECT coins FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            before = row["coins"] if row else 0
        gained = collect(conn, user_id)
        with conn.cursor() as cur:
            cur.execute("SELECT coins FROM users WHERE id = %s", (user_id,))
            after = cur.fetchone()["coins"]
        print(f"user_id={user_id}: {before} -> {after}  (+{gained})")


if __name__ == "__main__":
    main()
