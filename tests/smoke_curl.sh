#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# Smoke test against a *real* running gacha_gacha API.
#
# 必要なもの:
#   - docker compose up -d   (Postgres を起動)
#   - python -m server.app   (API サーバーを :8000 で起動)
#   - jq                     (任意 / きれいに表示用)
#
# 使い方:
#   bash tests/smoke_curl.sh
#
# 既定では http://localhost:8000 / ユーザー名 smoke_user に対して動作。
# -e BASE_URL=http://... / -e USER=foo で上書き可。
# ----------------------------------------------------------------------------
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}
USER_NAME=${USER:-smoke_user_$$}
PASSWORD=${PASSWORD:-smokepass123}
COOKIES=$(mktemp)
trap 'rm -f "$COOKIES"' EXIT

JQ=$(command -v jq || true)
fmt() { if [ -n "$JQ" ]; then $JQ; else cat; fi; }

call() {
  local method=$1 path=$2 body=${3:-}
  local args=( -sS -X "$method" -b "$COOKIES" -c "$COOKIES"
               -H "Content-Type: application/json"
               -w '\nHTTP_STATUS:%{http_code}\n'
               "$BASE_URL$path" )
  [ -n "$body" ] && args+=( -d "$body" )
  curl "${args[@]}"
}

echo "== 1. register =="
call POST /api/register "{\"name\":\"$USER_NAME\",\"password\":\"$PASSWORD\",\"display_name\":\"Smoker\"}" | fmt

echo
echo "== 2. me =="
call GET /api/me | fmt

echo
echo "== 3. gacha list =="
call GET /api/gacha/list | fmt

echo
echo "== 4. pull x 3 =="
for i in 1 2 3; do
  echo "-- pull $i --"
  call POST /api/gacha/pull '{"gacha_id":1}' | fmt
done

echo
echo "== 5. box =="
call GET /api/box | fmt

echo
echo "== 6. logout =="
call POST /api/logout | fmt

echo
echo "== 7. me after logout (expect 401) =="
call GET /api/me | fmt

echo
echo "smoke test finished. user=$USER_NAME"
