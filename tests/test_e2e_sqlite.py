"""End-to-end test for server/app.py using SQLite as the storage.

Why this exists:
    The production stack is PostgreSQL + psycopg. Running PG in this sandbox
    is infeasible (no apt, no docker). To still get behavioural confidence
    we monkey-patch `server.db` with `tests.sqlite_adapter` so the same
    handler code runs against an in-memory SQLite. This validates:
      - HTTP routing / status codes
      - JSON request / response shapes
      - Bearer Token authentication (Authorization: Bearer <token>)
      - Password hash + verify
      - Gacha pull flow including coin debit and box append
      - Box aggregation (GROUP BY + COUNT)

What this DOES NOT validate:
    - PostgreSQL-only features (FOR UPDATE locking, concurrent semantics)
    - Type coercion specific to psycopg
    For full PG validation, run `bash tests/smoke_curl.sh` against the docker
    compose stack.

Run:
    python tests/test_e2e_sqlite.py
"""

from __future__ import annotations

import http.client
import json
import pathlib
import sys
import threading
import time
import urllib.parse


# --- bootstrap: put project root on sys.path -------------------------------
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# --- monkey-patch server.db before server.app imports it -------------------
from tests import sqlite_adapter, translate_schema           # noqa: E402
import server.db as _real_db                                 # noqa: E402

# Initialise the test DB with schema + seed
sqlite_adapter.init_shared_db(
    translate_schema.get_translated_schema(),
    translate_schema.get_translated_seed(),
)

_real_db.get_conn = sqlite_adapter.get_conn       # type: ignore[assignment]
_real_db.healthcheck = sqlite_adapter.healthcheck # type: ignore[assignment]

# Now import server.app (it picks up the patched db)
import server.app as app_mod                                 # noqa: E402

# Some server modules ALSO `from .db import get_conn`. Patch those too.
import server.auth as auth_mod                               # noqa: E402  # noqa: F401
# auth_mod uses `psycopg.Connection` for type hints only; no patching needed.

# server.app imported `get_conn` at module load -> rebind it.
app_mod.get_conn = sqlite_adapter.get_conn       # type: ignore[assignment]


# --------------------------------------------------------------------------
# Test harness
# --------------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 18723  # arbitrary high port unlikely to clash


_results: dict[str, str] = {}
_failed = False


def expect(label: str, cond: bool, detail: str = "") -> None:
    global _failed
    if cond:
        _results[label] = "PASS"
        print(f"  PASS  {label}")
    else:
        _failed = True
        _results[label] = "FAIL " + detail
        print(f"  FAIL  {label}  {detail}")


# Persistent client. Bearer Token を保持して Authorization ヘッダで送る。
class Client:
    def __init__(self, host: str, port: int):
        self.host, self.port = host, port
        self.token: str | None = None

    def request(self, method: str, path: str, body=None
                ) -> tuple[int, dict, dict]:
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(data))
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        conn = http.client.HTTPConnection(self.host, self.port, timeout=5)
        conn.request(method, path, body=data, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"_raw": raw.decode(errors="replace")}
        # capture token from response body
        if isinstance(payload, dict) and isinstance(payload.get("token"), str):
            self.token = payload["token"]
        out_headers = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        return resp.status, payload, out_headers

    def clear_cookie(self) -> None:    # 互換のため名前は残す
        self.token = None


def start_server() -> threading.Thread:
    from http.server import ThreadingHTTPServer
    server = ThreadingHTTPServer((HOST, PORT), app_mod.GachaHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    # wait a tick
    for _ in range(20):
        try:
            c = http.client.HTTPConnection(HOST, PORT, timeout=1)
            c.request("OPTIONS", "/api/me")
            c.getresponse().read()
            c.close()
            break
        except Exception:
            time.sleep(0.05)
    return t


# --------------------------------------------------------------------------
# Scenarios
# --------------------------------------------------------------------------
def scenario_register_login_flow(c: Client) -> None:
    print("\n[1] register / login / me / logout")

    # /api/me without cookie -> 401
    s, body, _ = c.request("GET", "/api/me")
    expect("GET /api/me before login -> 401", s == 401, f"got {s}")

    # register
    s, body, _ = c.request("POST", "/api/register",
                           {"name": "alice", "password": "secret123",
                            "display_name": "Alice"})
    expect("POST /api/register -> 200", s == 200, f"got {s} {body}")
    expect("register payload has user.id", "user" in body and "id" in body["user"])
    expect("register starts with 1000 coins",
           body.get("user", {}).get("coins") == 1000,
           f"got {body.get('user',{}).get('coins')}")

    # /api/me after register -> 200
    s, body, _ = c.request("GET", "/api/me")
    expect("GET /api/me after register -> 200", s == 200, f"got {s}")
    expect("/api/me returns alice",
           body.get("user", {}).get("name") == "alice")

    # logout
    s, body, _ = c.request("POST", "/api/logout")
    expect("POST /api/logout -> 200", s == 200, f"got {s}")

    # cookie was just cleared by Set-Cookie max-age=0; session token in
    # client.cookie is the empty/expired one. /api/me should now be 401.
    s, body, _ = c.request("GET", "/api/me")
    expect("GET /api/me after logout -> 401", s == 401, f"got {s}")

    # login fresh
    c.clear_cookie()
    s, body, _ = c.request("POST", "/api/login",
                           {"name": "alice", "password": "secret123"})
    expect("POST /api/login -> 200", s == 200, f"got {s} {body}")

    # wrong password
    other = Client(HOST, PORT)
    s, body, _ = other.request("POST", "/api/login",
                                {"name": "alice", "password": "WRONG"})
    expect("login with wrong password -> 401", s == 401, f"got {s}")


def scenario_register_validation(c: Client) -> None:
    print("\n[2] register input validation")
    s, _, _ = c.request("POST", "/api/register",
                        {"name": "ab", "password": "longenough"})
    expect("name too short -> 400", s == 400, f"got {s}")
    s, _, _ = c.request("POST", "/api/register",
                        {"name": "okuser", "password": "short"})
    expect("password too short -> 400", s == 400, f"got {s}")
    s, body, _ = c.request("POST", "/api/register",
                           {"name": "alice", "password": "secret123"})
    expect("duplicate name -> 400 (not 500)", s == 400, f"got {s}")
    expect("duplicate name returns user-facing error",
           "name" in body.get("error", "") or "使われて" in body.get("error", ""),
           f"got {body!r}")


def scenario_gacha(c: Client) -> None:
    print("\n[3] gacha list & pull")
    s, body, _ = c.request("GET", "/api/gacha/list")
    expect("GET /api/gacha/list -> 200", s == 200, f"got {s}")
    expect("gacha list has 2 entries",
           len(body.get("gachas", [])) == 2,
           f"got {body}")
    expect("normal gacha pool_size = 12",
           body["gachas"][0]["pool_size"] == 12)

    # need to be logged in - alice already logged in via scenario 1
    s, body, _ = c.request("GET", "/api/me")
    coins_before = body["user"]["coins"]

    s, body, _ = c.request("POST", "/api/gacha/pull", {"gacha_id": 1})
    expect("pull -> 200", s == 200, f"got {s} {body}")
    expect("pull returns a character with rarity 1..5",
           1 <= body.get("character", {}).get("rarity", 0) <= 5)
    expect("pull deducts 100 coins",
           body.get("coins") == coins_before - 100,
           f"before={coins_before} after={body.get('coins')}")

    # invalid gacha id
    s, body, _ = c.request("POST", "/api/gacha/pull", {"gacha_id": 999})
    expect("pull non-existent gacha -> 404", s == 404, f"got {s}")

    # alice has 1000 - 100 (first pull above) = 900. 100/pull -> max 9 more.
    EXTRA_PULLS = 8
    for _ in range(EXTRA_PULLS):
        s, _, _ = c.request("POST", "/api/gacha/pull", {"gacha_id": 1})
        assert s == 200, f"unexpected pull status {s}"

    # box should reflect the pulls
    s, body, _ = c.request("GET", "/api/box")
    expect("GET /api/box -> 200", s == 200, f"got {s}")
    expect(f"box.total_pulls == {1 + EXTRA_PULLS}",
           body.get("total_pulls") == 1 + EXTRA_PULLS,
           f"got {body.get('total_pulls')}")
    expect("box.items is non-empty", len(body.get("items", [])) >= 1)
    # rarity sort: highest rarity first
    rarities = [it["rarity"] for it in body["items"]]
    expect("box items sorted by rarity DESC",
           rarities == sorted(rarities, reverse=True),
           f"got {rarities}")
    # tie-breaking: same-rarity items are sorted by id ASC
    from collections import defaultdict
    ids_per_rarity = defaultdict(list)
    for it in body["items"]:
        ids_per_rarity[it["rarity"]].append(it["id"])
    all_tie_ok = all(ids == sorted(ids) for ids in ids_per_rarity.values())
    expect("same-rarity items are tie-broken by id ASC",
           all_tie_ok,
           f"got {dict(ids_per_rarity)}")


def scenario_insufficient_coins() -> None:
    print("\n[4] insufficient coins guard")
    c = Client(HOST, PORT)
    # register a fresh user with 1000 coins
    s, body, _ = c.request("POST", "/api/register",
                           {"name": "broke", "password": "secret123"})
    assert s == 200, body
    # premium gacha costs 300; 4 pulls = 1200 > 1000
    statuses = []
    for _ in range(5):
        s, _, _ = c.request("POST", "/api/gacha/pull", {"gacha_id": 2})
        statuses.append(s)
    expect("first 3 premium pulls succeed",
           statuses[:3] == [200, 200, 200],
           f"got {statuses[:3]}")
    expect("4th premium pull fails with 400 (insufficient coins)",
           statuses[3] == 400,
           f"got {statuses[3]}")


def scenario_404() -> None:
    print("\n[5] unknown route")
    c = Client(HOST, PORT)
    s, body, _ = c.request("GET", "/api/nope")
    expect("GET /api/nope -> 404", s == 404, f"got {s}")


def main() -> int:
    print("starting test server on", f"http://{HOST}:{PORT}")
    start_server()
    print("server up.")

    c = Client(HOST, PORT)
    scenario_register_login_flow(c)
    scenario_register_validation(c)
    scenario_gacha(c)
    scenario_insufficient_coins()
    scenario_404()

    print("\n========== summary ==========")
    passed = sum(1 for v in _results.values() if v == "PASS")
    failed = len(_results) - passed
    print(f"  {passed} passed, {failed} failed, {len(_results)} total")
    return 0 if not _failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
