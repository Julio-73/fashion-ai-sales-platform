#!/usr/bin/env bash
# =============================================================================
# AI Sales Agent SaaS — Enterprise Smoke Test
# =============================================================================
# Simulates a real customer onboarding from tenant creation to report generation.
#
# Usage: ./smoke_test.sh [base_url]
#   base_url: defaults to http://127.0.0.1:8000
# =============================================================================

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

pass() { PASS=$((PASS+1)); echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { FAIL=$((FAIL+1)); echo -e "${RED}[FAIL]${NC} $1"; }

assert_status() {
  local desc="$1" method="$2" url="$3" expected="$4" body="$5" token="$6"
  local headers=()
  if [ -n "$token" ]; then headers=(-H "Authorization: Bearer $token"); fi
  local code
  if [ -n "$body" ]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "${headers[@]}" -H "Content-Type: application/json" -d "$body" "$url" 2>/dev/null || echo "000")
  else
    code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "${headers[@]}" "$url" 2>/dev/null || echo "000")
  fi
  if [ "$code" = "$expected" ]; then
    pass "$desc ($code)"
  else
    fail "$desc — expected $expected, got $code"
  fi
}

echo ""
echo "================================================"
echo "  Enterprise Smoke Test"
echo "  Target: $BASE_URL"
echo "================================================"
echo ""

# ── 1. Health ────────────────────────────────────────
assert_status "GET /health" GET "$BASE_URL/api/v1/health" 200 "" ""

# ── 2. System Status ─────────────────────────────────
assert_status "GET /system/status" GET "$BASE_URL/api/v1/system/status" 200 "" ""

# ── 3. Register tenant ───────────────────────────────
REGISTER_BODY='{"company_name":"SmokeTestCorp","company_slug":"smoke-test-corp","email":"admin@smoketest.com","password":"Sm0keTest2024!"}'
assert_status "POST /auth/register" POST "$BASE_URL/api/v1/auth/register" 201 "$REGISTER_BODY" ""

# ── 4. Login ─────────────────────────────────────────
LOGIN_BODY='{"email":"admin@smoketest.com","password":"Sm0keTest2024!"}'
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" -H "Content-Type: application/json" -d "$LOGIN_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
if [ -n "$TOKEN" ]; then
  pass "POST /auth/login (token received)"
else
  fail "POST /auth/login — no token"
fi

# ── 5. Me ────────────────────────────────────────────
assert_status "GET /auth/me" GET "$BASE_URL/api/v1/auth/me" 200 "" "$TOKEN"

# ── 6. Create customer ──────────────────────────────
CUSTOMER_BODY='{"full_name":"Maria Garcia","email":"maria@email.com","phone":"+51999888777","lead_status":"new","source":"whatsapp","tags":["vip","summer-campaign"]}'
assert_status "POST /customers" POST "$BASE_URL/api/v1/customers" 201 "$CUSTOMER_BODY" "$TOKEN"

# ── 7. List customers ────────────────────────────────
assert_status "GET /customers" GET "$BASE_URL/api/v1/customers" 200 "" "$TOKEN"

# ── 8. Create product ────────────────────────────────
PRODUCT_BODY='{"name":"Polo Premium Black","description":"Premium cotton polo","category":"Polos","base_price":49.99,"status":"active"}'
assert_status "POST /products" POST "$BASE_URL/api/v1/products" 201 "$PRODUCT_BODY" "$TOKEN"

# ── 9. List products ─────────────────────────────────
assert_status "GET /products" GET "$BASE_URL/api/v1/products" 200 "" "$TOKEN"

# ── 10. Create pipeline deal ─────────────────────────
PIPELINE_BODY='{"title":"Venta Polo Premium","estimated_value":49.99,"stage":"new_lead","probability":20}'
assert_status "POST /pipeline/deals" POST "$BASE_URL/api/v1/pipeline/deals" 201 "$PIPELINE_BODY" "$TOKEN"

# ── 11. Move deal through stages ─────────────────────
for stage in contacted qualified proposal negotiation won; do
  MOVE_BODY="{\"target_stage\":\"$stage\"}"
  assert_status "Move deal → $stage" POST "$BASE_URL/api/v1/pipeline/deals/{deal_id}/move-stage" 200 "$MOVE_BODY" "$TOKEN"
done

# ── 12. Pipeline board ────────────────────────────────
assert_status "GET /pipeline/board" GET "$BASE_URL/api/v1/pipeline/board" 200 "" "$TOKEN"

# ── 13. Pipeline metrics ──────────────────────────────
assert_status "GET /pipeline/metrics" GET "$BASE_URL/api/v1/pipeline/metrics" 200 "" "$TOKEN"

# ── 14. Pipeline funnel ──────────────────────────────
assert_status "GET /pipeline/funnel" GET "$BASE_URL/api/v1/pipeline/funnel" 200 "" "$TOKEN"

# ── 15. Pipeline dashboard ───────────────────────────
assert_status "GET /pipeline/dashboard" GET "$BASE_URL/api/v1/pipeline/dashboard" 200 "" "$TOKEN"

# ── 16. Pipeline AI score ─────────────────────────────
assert_status "GET /pipeline/deals/{deal_id}/ai-score" GET "$BASE_URL/api/v1/pipeline/deals/{deal_id}/ai-score" 200 "" "$TOKEN"

# ── 17. Pipeline recommendations ─────────────────────
assert_status "GET /pipeline/recommendations" GET "$BASE_URL/api/v1/pipeline/recommendations" 200 "" "$TOKEN"

# ── 18. Create order ─────────────────────────────────
ORDER_BODY='{"customer_name":"Maria Garcia","delivery_type":"delivery","delivery_address":"Av. Principal 123","items":[{"product_name":"Polo Premium Black","size":"M","color":"Black","quantity":2,"price":49.99}]}'
assert_status "POST /orders" POST "$BASE_URL/api/v1/orders" 201 "$ORDER_BODY" "$TOKEN"

# ── 19. List orders ──────────────────────────────────
assert_status "GET /orders" GET "$BASE_URL/api/v1/orders" 200 "" "$TOKEN"

# ── 20. Order metrics ────────────────────────────────
assert_status "GET /orders/metrics" GET "$BASE_URL/api/v1/orders/metrics" 200 "" "$TOKEN"

# ── 21. Inventory ────────────────────────────────────
assert_status "GET /inventory" GET "$BASE_URL/api/v1/inventory" 200 "" "$TOKEN"
assert_status "GET /inventory/metrics" GET "$BASE_URL/api/v1/inventory/metrics" 200 "" "$TOKEN"

# ── 22. CRM ──────────────────────────────────────────
assert_status "GET /crm/metrics" GET "$BASE_URL/api/v1/crm/metrics" 200 "" "$TOKEN"

# ── 23. Sales ────────────────────────────────────────
assert_status "GET /sales/insights" GET "$BASE_URL/api/v1/sales/insights" 200 "" "$TOKEN"
assert_status "GET /sales/activity" GET "$BASE_URL/api/v1/sales/activity" 200 "" "$TOKEN"
assert_status "GET /sales/recommendations" GET "$BASE_URL/api/v1/sales/recommendations" 200 "" "$TOKEN"
assert_status "GET /sales/top-leads" GET "$BASE_URL/api/v1/sales/top-leads" 200 "" "$TOKEN"

# ── 24. Executive Dashboard ──────────────────────────
assert_status "GET /executive-dashboard" GET "$BASE_URL/api/v1/executive-dashboard/" 200 "" "$TOKEN"

# ── 25. Automation ───────────────────────────────────
assert_status "GET /automation/metrics" GET "$BASE_URL/api/v1/automation/metrics" 200 "" "$TOKEN"
assert_status "GET /automation/rules" GET "$BASE_URL/api/v1/automation/rules" 200 "" "$TOKEN"

# ── 26. Reporting (PDF) ──────────────────────────────
assert_status "GET /reporting/sales/pdf" GET "$BASE_URL/api/v1/reporting/sales/pdf" 200 "" "$TOKEN"
assert_status "GET /reporting/pipeline/pdf" GET "$BASE_URL/api/v1/reporting/pipeline/pdf" 200 "" "$TOKEN"

# ── 27. Reporting (Excel) ────────────────────────────
assert_status "GET /reporting/sales/excel" GET "$BASE_URL/api/v1/reporting/sales/excel" 200 "" "$TOKEN"
assert_status "GET /reporting/pipeline/excel" GET "$BASE_URL/api/v1/reporting/pipeline/excel" 200 "" "$TOKEN"

# ── 28. Admin auth ───────────────────────────────────
ADMIN_BODY='{"email":"admin@smoketest.com","password":"Sm0keTest2024!"}'
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/admin/auth/login" -H "Content-Type: application/json" -d "$ADMIN_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
if [ -n "$ADMIN_TOKEN" ]; then
  pass "POST /admin/auth/login (token received)"
else
  fail "POST /admin/auth/login — no token"
fi

# ── 29. Admin endpoints ──────────────────────────────
assert_status "GET /admin/dashboard" GET "$BASE_URL/api/v1/admin/dashboard" 200 "" "$ADMIN_TOKEN"
assert_status "GET /admin/tenants" GET "$BASE_URL/api/v1/admin/tenants" 200 "" "$ADMIN_TOKEN"
assert_status "GET /admin/audit" GET "$BASE_URL/api/v1/admin/audit" 200 "" "$ADMIN_TOKEN"

# ── 30. Conversations ────────────────────────────────
assert_status "GET /conversations" GET "$BASE_URL/api/v1/conversations" 200 "" "$TOKEN"

# ── 31. WhatsApp ─────────────────────────────────────
assert_status "GET /whatsapp/metrics" GET "$BASE_URL/api/v1/whatsapp/metrics" 200 "" "$TOKEN"

# ── Results ──────────────────────────────────────────
echo ""
echo "================================================"
echo -e "  Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "================================================"
exit $FAIL
