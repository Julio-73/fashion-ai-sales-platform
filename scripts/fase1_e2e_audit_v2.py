"""FASE 1 — End to End Audit V2"""
import asyncio, json, time, httpx, sys
from uuid import uuid4
BASE = "http://127.0.0.1:8000/api/v1"
PASS, FAIL = 0, 0
errors = []

class State:
    access_token = ""
    empresa_id = ""
    customer_id = ""
    deal_id = ""
    order_id = ""

s = State()

async def step(name, func):
    global PASS, FAIL
    t0 = time.time()
    try:
        await func()
        PASS += 1
        print(f"  PASS [{time.time()-t0:.2f}s] {name}")
    except Exception as e:
        FAIL += 1
        errors.append(f"{name}: {e}")
        print(f"  FAIL [{time.time()-t0:.2f}s] {name}: {e}")

async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as c:
        email = f"e2e-{uuid4().hex[:8]}@test.io"
        slug = f"e2e-{uuid4().hex[:6]}"

        async def register():
            r = await c.post("/auth/register", json={
                "company_name": "E2E Corp", "company_slug": slug,
                "email": email, "password": "Test1234!x9"
            })
            assert r.status_code == 201, f"Register: {r.status_code} {r.text[:200]}"
            d = r.json()
            s.access_token = d["access_token"]
            s.empresa_id = d["user"]["empresa_id"]
            c.headers["Authorization"] = f"Bearer {s.access_token}"
        await step("1.1 Register tenant+user", register)

        async def create_customer():
            r = await c.post("/customers", json={
                "full_name": "E2E Cliente Final",
                "email": f"client-{uuid4().hex[:8]}@test.io",
                "phone": "+51999000001",
                "lead_status": "new", "priority": "hot"
            })
            assert r.status_code == 201, f"Create customer: {r.status_code} {r.text[:200]}"
            s.customer_id = r.json()["id"]
        await step("1.2 Create customer (lead)", create_customer)

        async def update_customer():
            r = await c.patch(f"/customers/{s.customer_id}", json={
                "lead_status": "qualified", "priority": "hot", "lead_score": 80
            })
            assert r.status_code == 200
            assert r.json()["lead_status"] == "qualified"
        await step("1.3 Update customer -> qualified", update_customer)

        async def create_deal():
            r = await c.post("/pipeline/deals", json={
                "customer_id": s.customer_id, "title": "Deal E2E Test",
                "estimated_value": 5000.0, "stage": "new_lead",
                "probability": 10, "channel": "whatsapp"
            })
            assert r.status_code == 201, f"Create deal: {r.status_code} {r.text[:200]}"
            s.deal_id = r.json()["id"]
        await step("1.4 Create pipeline deal", create_deal)

        stages = ["contacted", "qualified", "proposal", "negotiation"]
        for st in stages:
            async def move(st=st):
                probs = {"contacted":25, "qualified":45, "proposal":65, "negotiation":80}
                r = await c.post(f"/pipeline/deals/{s.deal_id}/move-stage", json={
                    "target_stage": st, "probability": probs[st]
                })
                assert r.status_code == 200, f"Move to {st}: {r.status_code} {r.text[:200]}"
                assert r.json()["stage"] == st
            await step(f"1.5 Move deal -> {st}", move)

        async def close_won():
            r = await c.post(f"/pipeline/deals/{s.deal_id}/move-stage", json={
                "target_stage": "won", "probability": 100,
                "won_reason": "E2E test cierre exitoso"
            })
            assert r.status_code == 200 and r.json()["stage"] == "won"
        await step("1.6 Close deal -> won", close_won)

        async def list_automation_rules():
            r = await c.get("/automation/rules")
            assert r.status_code == 200
            assert isinstance(r.json(), list)
        await step("1.7 List automation rules", list_automation_rules)

        async def create_order():
            r = await c.post("/orders", json={
                "customer_name": "E2E Test Client",
                "customer_phone": "+51999000001",
                "delivery_type": "delivery",
                "delivery_address": "Av. Principal 123, Lima",
                "status": "confirmed",
                "items": [{"product_name": "Producto E2E", "quantity": 1, "price": 5000.0}]
            })
            assert r.status_code == 201, f"Create order: {r.status_code} {r.text[:200]}"
            s.order_id = r.json()["id"]
        await step("1.8 Create order", create_order)

        async def reporting_metrics():
            r = await c.get("/reporting/metrics?period=month")
            assert r.status_code == 200
        await step("1.9 Reporting metrics", reporting_metrics)

        async def exec_dashboard():
            r = await c.get("/executive-dashboard")
            assert r.status_code == 200
            d = r.json()
            assert "kpi_strip" in d
        await step("1.10 Executive dashboard", exec_dashboard)

        async def pipeline_board():
            r = await c.get("/pipeline/board")
            assert r.status_code == 200
            assert "by_stage" in r.json()
        await step("1.11 Pipeline board", pipeline_board)

        async def pipeline_dashboard():
            r = await c.get("/pipeline/dashboard")
            assert r.status_code == 200
        await step("1.12 Pipeline dashboard", pipeline_dashboard)

        async def pipeline_metrics():
            r = await c.get("/pipeline/metrics")
            assert r.status_code == 200
        await step("1.13 Pipeline metrics", pipeline_metrics)

        async def crm_metrics():
            r = await c.get("/crm/metrics")
            assert r.status_code == 200
        await step("1.14 CRM metrics", crm_metrics)

        async def order_list():
            r = await c.get("/orders")
            assert r.status_code == 200
            assert "items" in r.json()
        await step("1.15 Order list", order_list)

        async def reporting_export():
            r = await c.get("/reporting/top-products?limit=5")
            assert r.status_code == 200
        await step("1.16 Top products report", reporting_export)

        async def automation_metrics():
            r = await c.get("/automation/metrics")
            assert r.status_code == 200
        await step("1.17 Automation metrics", automation_metrics)

    print(f"\n{'='*50}")
    print(f"FASE 1 E2E AUDIT: {PASS} passed, {FAIL} failed")
    if errors:
        print(f"Errors: {errors}")
    print(f"VEREDICT: {'ALL FLOWS VALIDATED' if FAIL == 0 else 'ISSUES DETECTED'}")
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
