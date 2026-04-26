"""DB-free unit tests for server.auth and server.gacha.

Run:
    python tests/test_unit.py
"""

from __future__ import annotations

import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import auth, gacha            # noqa: E402

_failed = False


def expect(label: str, cond: bool, detail: str = "") -> None:
    global _failed
    mark = "PASS" if cond else "FAIL"
    if not cond:
        _failed = True
    print(f"  {mark}  {label}  {detail if not cond else ''}")


# --------------------------------------------------------------------------
def test_password_roundtrip() -> None:
    print("\n[auth] hash + verify roundtrip")
    pw = "correct horse battery staple"
    h = auth.hash_password(pw)
    expect("verify with correct password", auth.verify_password(pw, h))
    expect("verify with wrong password rejects",
           not auth.verify_password("not the password", h))
    expect("hash format starts with pbkdf2_sha256$",
           h.startswith("pbkdf2_sha256$"))


def test_password_salt_is_unique() -> None:
    print("\n[auth] same password -> different stored hashes (salt)")
    h1 = auth.hash_password("abc12345")
    h2 = auth.hash_password("abc12345")
    expect("two stored hashes differ", h1 != h2)


def test_session_token_is_unique() -> None:
    print("\n[auth] session tokens are unique")
    tokens = {auth.new_session_token() for _ in range(2000)}
    expect("2000 fresh tokens are all distinct", len(tokens) == 2000)


# --------------------------------------------------------------------------
def test_gacha_draw_distribution() -> None:
    """Pull a fixed pool 200,000 times and check empirical weights are within
    a generous tolerance of the configured weights."""
    print("\n[gacha] empirical distribution converges to weights")
    pool = [
        gacha.GachaItem(1, "A", 1, "🟢", 50),
        gacha.GachaItem(2, "B", 2, "🦇", 30),
        gacha.GachaItem(3, "C", 3, "🛡️", 15),
        gacha.GachaItem(4, "D", 5, "🐉",  5),
    ]
    total_w = sum(p.weight for p in pool)
    expected = {p.character_id: p.weight / total_w for p in pool}

    rng = random.Random(42)
    n = 200_000
    counts: dict[int, int] = {p.character_id: 0 for p in pool}
    for _ in range(n):
        won = gacha.draw(pool, rng=rng)
        counts[won.character_id] += 1

    for cid, exp in expected.items():
        emp = counts[cid] / n
        # 5 percentage-point tolerance — generous for n=200k
        expect(f"char {cid} empirical {emp:.4f} vs expected {exp:.4f}",
               abs(emp - exp) < 0.01,
               f"diff={abs(emp-exp):.4f}")


def test_gacha_empty_pool_raises() -> None:
    print("\n[gacha] empty pool raises")
    try:
        gacha.draw([])
    except ValueError:
        expect("empty pool raises ValueError", True)
        return
    expect("empty pool raises ValueError", False, "no exception raised")


# --------------------------------------------------------------------------
def main() -> int:
    test_password_roundtrip()
    test_password_salt_is_unique()
    test_session_token_is_unique()
    test_gacha_draw_distribution()
    test_gacha_empty_pool_raises()
    print("\n========== unit summary ==========")
    print("  status:", "FAILED" if _failed else "PASSED")
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
