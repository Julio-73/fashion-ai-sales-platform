"""FASE 1 — End to End Audit: Lead -> CRM -> Pipeline -> Automation -> Orders -> Reporting -> Dashboard"""
import asyncio
import json
import time
import httpx
from uuid import uuid4

BASE = "http://127.0.0.1:8000/api/v1"
results = {"passed": [], "failed": []}
email = f"e2e-test-{uuid4().hex[:8]}@test.io"
company = f"E2E-Test-{uuid4().hex[:6]}"

async def step(name: str, func):
    try:
        t0 = time.time()
        await func()
        elapsed = time.time() - t0
        results["passed"].append((name, elapsed))
        print(f"  PASS [{elapsed:.2f}s] {name}")
    except Exception as e:
        results["failed"].append((name, str(e)))
        print(f"  FAIL [{time.time()-t0:.2f}s] {name}: {e}")

async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as c:
        # 1. Register new company + user
        async def register():
            r = await c.post("/auth/register", json={
                "company_name": company, "company_slug": company.lower(),
                "email": email, "password": "Test1234!"
            })
            assert r.status_code == 201, f"Register: {r.status_code} {r.text}"
            data = r.json()
            assert "access_token" in data, "No access_token in register response"
            c.headers["Authorization"] = f"Bearer {data['access_token']}"
            globals()["refresh_token"] = data.get("refresh_token", "")
            globals()["empresa_id"] = data["user"]["empresa_id"]
            globals()["user_id"] = data["user"]["user_id"]
        await step("1.1 Register tenant+user", register)

        # 2. Create a customer (Lead)
        async def create_customer():
            r = await c.post("/customers", json={
                "full_name": "E2E Test Client", "email": f"client-{uuid4().hex[:8]}@test.io",
                "phone": "+51999000001", "lead_status": "new", "priority": "hot"
            })
            assert r.status_code == 201, f"Create customer: {r.status_code} {r.text}"
            globals()["customer_id"] = r.json()["id"]
        await step("1.2 Create customer (Lead)", create_customer)

        # 3. Move lead to CRM
        async def update_customer():
            r = await c.put(f"/customers/{customer_id}", json={
                "lead_status": "qualified", "priority": "hot",
                "lead_score": 80, "notes": "E2E qualified lead"
            })
            assert r.status_code == 200, f"Update customer: {r.status_code}"
            assert r.json()["lead_status"] == "qualified"
        await step("1.3 Update customer in CRM", update_customer)

        # 4. Create pipeline deal
        async def create_deal():
            r = await c.post("/pipeline/items", json={
                "customer_id": customer_id, "title": "E2E Test Deal",
                "estimated_value": 5000.00, "stage": "new_lead",
                "probability": 10, "channel": "whatsapp"
            })
            assert r.status_code == 201, f"Create deal: {r.status_code} {r.text}"
            globals()["deal_id"] = r.json()["id"]
        await step("1.4 Create pipeline deal", create_deal)

        # 5. Move through pipeline stages
        async def move_contacted():
            r = await c.patch(f"/pipeline/items/{deal_id}/move", json={
                "target_stage": "contacted", "probability": 25
            })
            assert r.status_code == 200
            assert r.json()["stage"] == "contacted"
        await step("1.5 Move deal: new_lead -> contacted", move_contacted)

        async def move_qualified():
            r = await c.patch(f"/pipeline/items/{deal_id}/move", json={
                "target_stage": "qualified", "probability": 45
            })
            assert r.status_code == 200 and r.json()["stage"] == "qualified"
        await step("1.6 Move deal: contacted -> qualified", move_qualified)

        async def move_proposal():
            r = await c.patch(f"/pipeline/items/{deal_id}/move", json={
                "target_stage": "proposal", "probability": 65
            })
            assert r.status_code == 200 and r.json()["stage"] == "proposal"
        await step("1.7 Move deal: qualified -> proposal", move_proposal)

        async def move_negotiation():
            r = await c.patch(f"/pipeline/items/{deal_id}/move", json={
                "target_stage": "negotiation", "probability": 80
            })
            assert r.status_code == 200 and r.json()["stage"] == "negotiation"
        await step("1.8 Move deal: proposal -> negotiation", move_negotiation)

        async def move_won():
            r = await c.patch(f"/pipeline/items/{deal_id}/move", json={
                "target_stage": "won", "probability": 100,
                "won_reason": "E2E test successful closure"
            })
            assert r.status_code == 200 and r.json()["stage"] == "won"
        await step("1.9 Close deal: negotiation -> won", move_won)

        # 6. Check automations
        async def list_automations():
            r = await c.get("/automation/rules")
            assert r.status_code == 200
            rules = r.json()
            assert isinstance(rules, list) or "rules" in r.json()
        await step("1.10 List automation rules", list_automations)

        # 7. Create order
        async def create_order():
            r = await c.post("/orders", json={
                "customer_name": "E2E Test Client",
                "customer_phone": "+51999000001",
                "delivery_type": "delivery",
                "delivery_address": "Av. Test 123, Lima",
                "status": "confirmed",
                "items": [{"product_name": "E2E Test Product", "quantity": 1, "price": 5000.00}]
            })
            assert r.status_code == 201, f"Create order: {r.status_code} {r.text}"
            globals()["order_id"] = r.json()["id"]
        await step("1.11 Create order", create_order)

        # 8. Generate report
        async def list_orders():
            r = await c.get("/orders?limit=5")
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, dict) and "items" in data
        await step("1.12 List orders (reporting data)", list_orders)

        async def reporting_metrics():
            r = await c.get("/reporting/metrics?period=month")
            assert r.status_code == 200
        await step("1.13 Reporting metrics", reporting_metrics)

        # 9. Executive dashboard
        async def exec_dashboard():
            r = await c.get("/executive-dashboard")
            assert r.status_code == 200
            data = r.json()
            assert "kpi_strip" in data or "metrics" in data
        await step("1.14 Executive dashboard", exec_dashboard)

        # 10. Pipeline board
        async def pipeline_board():
            r = await c.get("/pipeline/board")
            assert r.status_code == 200
            data = r.json()
            assert "items" in data or "by_stage" in data
        await step("1.15 Pipeline board", pipeline_board)

        # 11. Pipeline dashboard
        async def pipeline_dashboard():
            r = await c.get("/pipeline/dashboard")
            assert r.status_code == 200
        await step("1.16 Pipeline dashboard", pipeline_dashboard)

        # 12. CRM metrics
        async def crm_metrics():
            r = await c.get("/crm/metrics")
            assert r.status_code == 200
        await step("1.17 CRM metrics", crm_metrics)

        # Summary
        print(f"\n=== FASE 1 E2E AUDIT RESULTS ===")
        print(f"Passed: {len(results['passed'])}/{len(results['passed'])+len(results['failed'])}")
        print(f"Failed: {len(results['failed'])}")
        for name, elapsed in results["passed"]:
            print(f"  [PASS] {name} ({elapsed:.2f}s)")
        for name, err in results["failed"]:
            print(f"  [FAIL] {name}: {err}")
        if not results["failed"]:
            print("\n => FULL E2E FLOW VALIDATED SUCCESSFULLY")
        else:
            print(f"\n => {len(results['failed'])} failures detected")

asyncio.run(main())
