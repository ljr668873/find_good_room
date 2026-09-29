#!/bin/bash
# M1 冒烟：健康检查 + 注册/登录/me 全链路。用法：bash scripts/smoke.sh [base_url]
# 注意：JSON 用单引号拼接构造。macOS bash 3.2 在函数实参嵌套 $() 中会对
# "{\"a\",\"b\"}" 模式做 brace expansion 导致 body 被截断，勿改回转义双引号写法。
set -e
BASE="${1:-http://127.0.0.1:8000}"

check() { # name expected actual
  if echo "$3" | grep -q "$2"; then echo "PASS: $1"; else echo "FAIL: $1 — got: $3"; exit 1; fi
}

json_body() { # username password — 输出 JSON 字符串
  printf '{"username":"%s","password":"%s"}' "$1" "$2"
}

check health '"status":"ok"' "$(curl -s $BASE/api/health)"

NAME="smoke_$RANDOM"
BODY=$(json_body "$NAME" "pass123456")
check register "$NAME" "$(curl -s -X POST $BASE/api/auth/register -H 'Content-Type: application/json' -d "$BODY")"
check dup-register '用户名已存在' "$(curl -s -X POST $BASE/api/auth/register -H 'Content-Type: application/json' -d "$BODY")"

TOKEN=$(curl -s -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
check login-me "$NAME" "$(curl -s $BASE/api/auth/me -H "Authorization: Bearer $TOKEN")"
check no-token '未登录' "$(curl -s $BASE/api/auth/me)"
check bad-pass '用户名或密码错误' "$(curl -s -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d "$(json_body "$NAME" wrongpass)")"

echo "ALL PASS"
