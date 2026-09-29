#!/bin/bash
# M2 冒烟：房源全链路 — 上传/发布/列表筛选/详情/房东主页/状态流转/举报/管理员
# 用法：bash scripts/smoke2.sh [base_url]。需服务已启动且数据库已 seed（有广州城市 + admin 账号）
set -e
BASE="${1:-http://127.0.0.1:8000}"

check() { # name expected actual
  if echo "$3" | grep -q "$2"; then echo "PASS: $1"; else echo "FAIL: $1 — got: $3"; exit 1; fi
}

# ---- 房东账号 ----
NAME="m2_$RANDOM"
BODY=$(printf '{"username":"%s","password":"%s"}' "$NAME" "pass123456")
curl -s -X POST $BASE/api/auth/register -H 'Content-Type: application/json' -d "$BODY" > /dev/null
TOKEN=$(curl -s -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d "$BODY" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
AUTH="Authorization: Bearer $TOKEN"

# ---- 测试图（2400x1600 大图，验证压缩）----
.venv/bin/python -c "
from PIL import Image
Image.new('RGB', (2400, 1600), (200, 120, 60)).save('/tmp/m2_test.jpg', quality=95)"

# ---- 上传 ----
UP=$(curl -s -X POST $BASE/api/my/upload/photos -H "$AUTH" -F "files=@/tmp/m2_test.jpg" -F "files=@/tmp/m2_test.jpg")
check upload-photos '"photos"' "$UP"
check upload-thumb '_thumb' "$(echo "$UP" | python3 -c "import sys,json;print(json.load(sys.stdin)['photos'][0])")"

# ---- 发布 ----
VILLAGE="冒烟村$RANDOM"
LISTING=$(.venv/bin/python -c "
import json, sys
photos = json.loads('''$UP''')['photos']
payload = {
    'city': '广州', 'village': '$VILLAGE', 'address': '测试巷1号3楼',
    'rent': 1200, 'deposit_type': '押一付一', 'layout': '单间',
    'area': 18.5, 'floor': 3, 'floor_total': 7, 'has_elevator': False,
    'facing': '南', 'private_bathroom': True,
    'water_price': 4.5, 'electric_price': 1.5,
    'available_date': '2026-10-01',
    'metro_line': '3号线', 'metro_station': '客村站', 'walk_minutes': 8,
    'photos': photos, 'phone': '13800138000', 'title': None,
}
print(json.dumps(payload, ensure_ascii=False))")
CREATED=$(curl -s -X POST $BASE/api/my/listings -H "$AUTH" -H 'Content-Type: application/json' -d "$LISTING")
check create "$VILLAGE" "$CREATED"
check auto-title "·单间·1200元" "$CREATED"
LID=$(echo "$CREATED" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
LANDLORD_ID=$(echo "$CREATED" | python3 -c "import sys,json;print(json.load(sys.stdin)['landlord_id'])")

# ---- 校验失败用例：坏城市 ----
check bad-city '暂不支持城市' "$(curl -s -X POST $BASE/api/my/listings -H "$AUTH" -H 'Content-Type: application/json' -d "$(echo "$LISTING" | .venv/bin/python -c "import sys,json;d=json.load(sys.stdin);d['city']='火星';print(json.dumps(d,ensure_ascii=False))")")"

# ---- 列表/筛选/详情 ----
check list-by-village "\"total\":1" "$(curl -s -G $BASE/api/listings --data-urlencode "city=广州" --data-urlencode "village=$VILLAGE")"
check list-by-metro "\"total\":1" "$(curl -s -G $BASE/api/listings --data-urlencode "city=广州" --data-urlencode "metro_station=客村站" --data-urlencode "village=$VILLAGE")"
check list-rent-filter "\"total\":1" "$(curl -s -G $BASE/api/listings --data-urlencode "city=广州" --data-urlencode "rent_min=1000" --data-urlencode "rent_max=1500" --data-urlencode "village=$VILLAGE")"
check filter-options "$VILLAGE" "$(curl -s -G $BASE/api/filter-options --data-urlencode "city=广州")"
check detail-phone '13800138000' "$(curl -s $BASE/api/listings/$LID)"

# ---- 房东主页 ----
LANDLORD=$(curl -s -G $BASE/api/landlords/$LANDLORD_ID/listings --data-urlencode "city=广州")
check landlord-username "$NAME" "$LANDLORD"
check landlord-count "\"total\":1" "$LANDLORD"

# ---- 举报 ----
REPORT_BODY=$(printf '{"listing_id":%s,"reason":"fake"}' "$LID")
check report '"ok":true' "$(curl -s -X POST $BASE/api/reports -H 'Content-Type: application/json' -d "$REPORT_BODY")"

# ---- 状态流转 ----
check mark-rented '"ok":true' "$(curl -s -X PATCH $BASE/api/my/listings/$LID/status -H "$AUTH" -H 'Content-Type: application/json' -d '{"action":"rented"}')"
check detail-404-after-rented '房源不存在' "$(curl -s $BASE/api/listings/$LID)"
check rented-no-reactivate '复制重新发布' "$(curl -s -X PATCH $BASE/api/my/listings/$LID/status -H "$AUTH" -H 'Content-Type: application/json' -d '{"action":"active"}')"
check report-inactive-404 '房源不存在' "$(curl -s -X POST $BASE/api/reports -H 'Content-Type: application/json' -d "$REPORT_BODY")"

# ---- 第二条房源：下架/恢复 + 管理员强制下架 ----
CREATED2=$(curl -s -X POST $BASE/api/my/listings -H "$AUTH" -H 'Content-Type: application/json' -d "$LISTING")
LID2=$(echo "$CREATED2" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
check offline '"ok":true' "$(curl -s -X PATCH $BASE/api/my/listings/$LID2/status -H "$AUTH" -H 'Content-Type: application/json' -d '{"action":"offline"}')"
check re-online '"ok":true' "$(curl -s -X PATCH $BASE/api/my/listings/$LID2/status -H "$AUTH" -H 'Content-Type: application/json' -d '{"action":"active"}')"

ADMIN_TOKEN=$(curl -s -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin123456"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
ADMIN_AUTH="Authorization: Bearer $ADMIN_TOKEN"
PENDING=$(curl -s "$BASE/api/admin/reports?status=pending" -H "$ADMIN_AUTH")
check admin-reports-pending "\"listing_id\":$LID" "$PENDING"
REPORT_ID=$(echo "$PENDING" | .venv/bin/python -c "
import sys, json
items = json.load(sys.stdin)['items']
print(next(r['id'] for r in items if r['listing_id'] == $LID))")
check admin-report-done '"ok":true' "$(curl -s -X PATCH $BASE/api/admin/reports/$REPORT_ID -H "$ADMIN_AUTH" -H 'Content-Type: application/json' -d '{"status":"done"}')"
check admin-force-offline '"ok":true' "$(curl -s -X PATCH $BASE/api/admin/listings/$LID2/status -H "$ADMIN_AUTH" -H 'Content-Type: application/json' -d '{"action":"offline"}')"
check admin-no-auth '无权限' "$(curl -s -X PATCH "$BASE/api/admin/listings/$LID2/status" -H "$AUTH" -H 'Content-Type: application/json' -d '{"action":"offline"}')"

echo "ALL PASS"
