"""第12章 / 練習: pickup 期間内 / 期間外で抽選分布を比較する。

実行:
    # 期間中のピックアップ行を入れた状態:
    python scripts/ch12_pickup_simulator.py
    # 期間外:
    psql "$DATABASE_URL" -c "DELETE FROM pickup_periods;"
    python scripts/ch12_pickup_simulator.py
"""
import os
import sys
from collections import Counter

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "exercises", "ch12"),
)
from step4_fetch_pool_lateral import fetch_pool, weighted_choice   # noqa: E402

import psycopg
from psycopg.rows import dict_row

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)
GACHA_ID = int(os.environ.get("GACHA_ID", "1"))
N = int(os.environ.get("N", "10000"))


def main():
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        pool = fetch_pool(conn, GACHA_ID)

    if not pool:
        print(f"empty pool for gacha_id={GACHA_ID}", file=sys.stderr)
        sys.exit(1)

    counts: Counter = Counter()
    for _ in range(N):
        counts[weighted_choice(pool)["character_id"]] += 1

    total_w = sum(float(it["weight"]) for it in pool)
    print(f"gacha_id={GACHA_ID}  N={N}")
    for it in pool:
        cid = it["character_id"]
        actual = 100 * counts[cid] / N
        theory = 100 * float(it["weight"]) / total_w
        print(f"  cid={cid:>3}  rarity={it['rarity']}  "
              f"actual={actual:5.2f}%  theory={theory:5.2f}%")


if __name__ == "__main__":
    main()
