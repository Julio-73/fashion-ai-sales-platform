"""FASE 1 — End to End Audit V3 (using seeded credentials)"""
import asyncio, json, time, httpx, sys
from uuid import uuid4
BASE = "http://127.0.0.1:8000/api/v1"
PASS, FAIL = 0, 0
errors = []

class State:
    access_token = ""
    refresh_token = ""
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
        errors.append(f"{name}: {str(e)[:200]}")
        print(f"  FAIL [{time.time()-t0:.2f}s] {name}: {str(e)[:200]}")

async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as c:
        # Login with seeded regular user
        async def login():
            r = await c.post("/auth/login", json={
                "email": "demo@fashionsales.ai", "password": "Demo@2024!"
            })
            if r.status_code == 429:
                print("  Rate limited on login, waiting 60s...")
                await asyncio.sleep(62)
                r = await c.post("/auth/login", json={
                    "email": "demo@fashionsales.ai", "password": "Demo@2024!"
                })
            assert r.status_code == 200, f"Login: {r.status_code} {r.text[:200]}"
            d = r.json()
            s.access_token = d["access_token"]
            s.refresh_token = d["refresh_token"]
            s.empresa_id = d["user"]["empresa_id"]
            c.headers["Authorization"] = f"Bearer {s.access_token}"
        await step("1.1 Login as demo user", login)

        async def create_customer():
            r = await c.post("/customers", json={
                "full_name": "E2E Cliente Final",
                "email": f"client-{uuid4().hex[:8]}@test.io",
                "phone": "+51999000001",
                "lead_status": "new", "priority": "hot"
            })
            assert r.status_code == 201, f"{r.status_code} {r.text[:200]}"
            s.customer_id = r.json()["id"]
        await step("1.2 Create customer (lead)", create_customer)

        async def update_customer():
            r = await c.patch(f"/customers/{s.customer_id}", json={
                "lead_status": "qualified", "lead_score": 80, "notes": "E2E qualified"
            })
            assert r.status_code == 200 and r.json()["lead_status"] == "qualified"
        await step("1.3 Update customer -> qualified", update_customer)

        async def create_deal():
            r = await c.post("/pipeline/deals", json={
                "customer_id": s.customer_id, "title": "Deal E2E",
                "estimated_value": 5000.0, "stage": "new_lead",
                "probability": 10, "channel": "whatsapp"
            })
            assert r.status_code == 201, f"{r.status_code} {r.text[:200]}"
            s.deal_id = r.json()["id"]
        await step("1.4 Create pipeline deal", create_deal)

        for st, prob in [("contacted",25),("qualified",45),("proposal",65),("negotiation",80)]:
            async def move(st=st, prob=prob):
                r = await c.post(f"/pipeline/deals/{s.deal_id}/move-stage", json={
                    "target_stage": st, "probability": prob
                })
                assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
                assert r.json()["stage"] == st
            await step(f"1.5 Move deal -> {st}", move)

        async def close_won():
            r = await c.post(f"/pipeline/deals/{s.deal_id}/move-stage", json={
                "target_stage": "won", "probability": 100, "won_reason": "E2E cierre"
            })
            assert r.status_code == 200 and r.json()["stage"] == "won"
        await step("1.6 Close deal -> won", close_won)

        async def pipeline_board():
            r = await c.get("/pipeline/board")
            assert r.status_code == 200
            assert "by_stage" in r.json()
        await step("1.7 Pipeline board", pipeline_board)

        async def pipeline_dashboard():
            r = await c.get("/pipeline/dashboard")
            assert r.status_code == 200
        await step("1.8 Pipeline dashboard", pipeline_dashboard)

        async def pipeline_metrics():
            r = await c.get("/pipeline/metrics")
            assert r.status_code == 200
        await step("1.9 Pipeline metrics", pipeline_metrics)

        async def automation_rules():
            r = await c.get("/automation/rules")
            assert r.status_code == 200
        await step("1.10 List automation rules", automation_rules)

        async def automation_tasks():
            r = await c.get("/automation/tasks")
            assert r.status_code == 200
        await step("1.11 List automation tasks", automation_tasks)

        async def automation_run():
            r = await c.post("/automation/run")
            assert r.status_code == 200
        await step("1.12 Run automation engine", automation_run)

        async def create_order():
            r = await c.post("/orders", json={
                "customer_name": "E2E Client", "customer_phone": "+51999000001",
                "delivery_type": "delivery", "delivery_address": "Av. Test 123, Lima",
                "status": "confirmed",
                "items": [{"product_name": "E2E Product", "quantity": 1, "price": 5000.0}]
            })
            assert r.status_code == 201, f"{r.status_code} {r.text[:200]}"
            s.order_id = r.json()["id"]
        await step("1.13 Create order", create_order)

        async def order_list():
            r = await c.get("/orders")
            assert r.status_code == 200 and "items" in r.json()
        await step("1.14 List orders", order_list)

        async def order_metrics():
            r = await c.get("/orders/metrics")
            assert r.status_code == 200
        await step("1.15 Order metrics", order_metrics)

        async def exec_dashboard():
            r = await c.get("/executive-dashboard")
            assert r.status_code == 200
        await step("1.16 Executive dashboard", exec_dashboard)

        async def crm_metrics():
            r = await c.get("/crm/metrics")
            assert r.status_code == 200
        await step("1.17 CRM metrics", crm_metrics)

        async def reporting_metrics():
            r = await c.get("/reporting/metrics?period=month")
            assert r.status_code == 200
        await step("1.18 Reporting metrics", reporting_metrics)

        async def ai_score():
            r = await c.post(f"/pipeline/deals/{s.deal_id}/ai-score")
            assert r.status_code == 200
        await step("1.19 AI score on deal", ai_score)

        async def pipeline_alerts():
            r = await c.get("/pipeline/alerts")
            assert r.status_code == 200
        await step("1.20 Pipeline alerts", pipeline_alerts)

    print(f"\n{'='*50}")
    print(f"FASE 1 E2E AUDIT: {PASS} passed, {FAIL} failed")
    if errors:
        print("Errors:")
        for e in errors: print(f"  - {e}")
    verdict = "ALL FLOWS VALIDATED SUCCESSFULLY" if FAIL == 0 else f"{FAIL} ISSUES DETECTED"
    print(f"VEREDICT: {verdict}")
    return 0 if FAIL == 0 else 1

asyncio.run(main())
