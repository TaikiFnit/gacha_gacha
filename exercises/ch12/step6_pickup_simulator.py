"""ch12 / step 6 — 期間内 / 期間外で抽選分布が変わるのを 1 万回サンプリングして観察。

ゴール:
    fetch_pool() を直接 N 回呼んで weighted_choice() し、 character_id ごとの
    出現回数を集計する。 「ピックアップキャラの実際の排出率が 6 倍になっているか」
    を実機で確認できる。

実行:
    # アクティブなピックアップを置いた状態で:
    python exercises/ch12/step6_pickup_simulator.py
    # 期間外と比較:
    psql "$DATABASE_URL" -c "DELETE FROM pickup_periods;"
    python exercises/ch12/step6_pickup_simulator.py
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step4_fetch_pool_lateral import fetch_pool, weighted_choice   # noqa: E402

import psycopg
from psycopg.rows import dict_row

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)
GACHA_ID = 1
N = 10000


def main():
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        pool = fetch_pool(conn, GACHA_ID)

    print(f"--- pool (gacha_id={GACHA_ID}) ---")
    for it in pool:
        print(f"  character_id={it['character_id']:>3}  rarity={it['rarity']}  weight={it['weight']}")

    counts: Counter = Counter()
    for _ in range(N):
        chosen = weighted_choice(pool)
        counts[chosen["character_id"]] += 1

    print(f"\n--- {N} 回引いた結果 (実測) ---")
    for cid, n in sorted(counts.items()):
        rarity = next(it["rarity"] for it in pool if it["character_id"] == cid)
        weight = next(float(it["weight"]) for it in pool if it["character_id"] == cid)
        pct_actual = 100 * n / N
        pct_theory = 100 * weight / sum(float(it["weight"]) for it in pool)
        print(f"  character_id={cid:>3}  rarity={rarity}  hits={n:>5}  "
              f"actual={pct_actual:5.2f}%  theory={pct_theory:5.2f}%")


if __name__ == "__main__":
    main()
