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
#
# 認証は Bearer Token。 register/login のレスポンス JSON 内 token を、
# 以降の認証付きリクエストで Authorization: Bearer <token> として送る。
# ----------------------------------------------------------------------------
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}
USER_NAME=${USER:-smoke_user_$$}
PASSWORD=${PASSWORD:-smokepass123}

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: このスクリプトは jq を必須とします (token 抽出に使用)" >&2
  echo "       brew install jq / apt install jq などで入れてください" >&2
  exit 1
fi

# ----- 認証なしで叩く -----
call() {
  local method=$1 path=$2 body=${3:-}
  local args=( -sS -X "$method"
               -H "Content-Type: application/json"
               -w '\nHTTP_STATUS:%{http_code}\n'
               "$BASE_URL$path" )
  [ -n "$body" ] && args+=( -d "$body" )
  curl "${args[@]}"
}

# ----- Bearer Token を付けて叩く -----
call_auth() {
  local method=$1 path=$2 body=${3:-}
  local args=( -sS -X "$method"
               -H "Content-Type: application/json"
               -H "Authorization: Bearer $TOKEN"
               -w '\nHTTP_STATUS:%{http_code}\n'
               "$BASE_URL$path" )
  [ -n "$body" ] && args+=( -d "$body" )
  curl "${args[@]}"
}

# レスポンス本文 (HTTP_STATUS 行を除く) を取り出すヘルパ
strip_status() { sed -n '/^HTTP_STATUS:/!p'; }

echo "== 1. register =="
REG_RAW=$(call POST /api/register \
  "{\"name\":\"$USER_NAME\",\"password\":\"$PASSWORD\",\"display_name\":\"Smoker\"}")
echo "$REG_RAW" | jq

TOKEN=$(echo "$REG_RAW" | strip_status | jq -r '.token // empty')
if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "ERROR: register のレスポンスに token が入っていません" >&2
  exit 1
fi
echo "  -> token: ${TOKEN:0:8}…"

echo
echo "== 2. me =="
call_auth GET /api/me | jq

echo
echo "== 3. gacha list (認証不要) =="
call GET /api/gacha/list | jq

echo
echo "== 4. pull x 3 =="
for i in 1 2 3; do
  echo "-- pull $i --"
  call_auth POST /api/gacha/pull '{"gacha_id":1}' | jq
done

echo
echo "== 5. box =="
call_auth GET /api/box | jq

echo
echo "== 6. logout =="
call_auth POST /api/logout | jq

echo
echo "== 7. me after logout (expect 401) =="
call_auth GET /api/me | jq

echo
echo "smoke test finished. user=$USER_NAME"
