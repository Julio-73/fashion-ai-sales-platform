"""Debug all failing endpoints with proper paths and values"""
import asyncio, httpx, json

BASE = "http://127.0.0.1:8000/api/v1"

async def main():
    c = httpx.AsyncClient(base_url=BASE, timeout=30)
    
    r = await c.post("/auth/login", json={"email": "demo@fashionsales.ai", "password": "Demo@2024!"})
    if r.status_code != 200:
        print(f"Login failed: {r.status_code} {r.text[:200]}")
        return
    token = r.json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    empresa_id = r.json()["user"]["empresa_id"]
    print(f"Login OK, empresa={empresa_id}")
    
    # 1. Customer PATCH with correct lead_status
    print("\n--- 1. Customer update with correct lead_status ---")
    r = await c.post("/customers", json={
        "full_name": "Debug Customer Final", "email": "debug-final@test.io",
        "phone": "+51999000999", "lead_status": "new", "priority": "hot"
    })
    if r.status_code == 201:
        cid = r.json()["id"]
        r = await c.patch(f"/customers/{cid}", json={"lead_status": "interested", "lead_score": 80})
        print(f"PATCH /customers/{cid}: {r.status_code} {r.text[:200]}")
    else:
        print(f"Create customer: {r.status_code} {r.text[:200]}")
    
    # 2. Pipeline move to negotiation
    print("\n--- 2. Pipeline move to negotiation ---")
    r = await c.get("/pipeline/deals?limit=1")
    if r.status_code == 200:
        data = r.json()
        deals = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if deals and len(deals) > 0:
            did = deals[0]["id"]
            print(f"Deal: {did} current_stage={deals[0].get('stage')}")
            r = await c.post(f"/pipeline/deals/{did}/move-stage", json={"target_stage": "negotiation", "probability": 80})
            print(f"Move to negotiation: {r.status_code} {r.text[:500]}")
        else:
            # Create a deal first
            print("No deals found, creating one...")
            r = await c.post("/pipeline/deals", json={
                "customer_id": cid, "title": "Debug Final Deal",
                "estimated_value": 5000.0, "stage": "new_lead",
                "probability": 10, "channel": "whatsapp"
            })
            if r.status_code == 201:
                did = r.json()["id"]
                # Move to contacted first
                await c.post(f"/pipeline/deals/{did}/move-stage", json={"target_stage": "contacted", "probability": 25})
                await c.post(f"/pipeline/deals/{did}/move-stage", json={"target_stage": "qualified", "probability": 45})
                await c.post(f"/pipeline/deals/{did}/move-stage", json={"target_stage": "proposal", "probability": 65})
                r = await c.post(f"/pipeline/deals/{did}/move-stage", json={"target_stage": "negotiation", "probability": 80})
                print(f"Move to negotiation: {r.status_code} {r.text[:500]}")
    
    # 3. Executive dashboard WITH trailing slash
    print("\n--- 3. Executive dashboard (with trailing slash) ---")
    r = await c.get("/executive-dashboard/")
    print(f"GET /executive-dashboard/: {r.status_code}")
    if r.status_code == 200:
        keys = list(r.json().keys())
        print(f"  Keys: {keys}")
    else:
        print(f"  {r.text[:200]}")
    
    # 4. Smart Sales endpoints
    print("\n--- 4. Smart Sales ---")
    for path in ["/smart-sales/analyze", "/smart-sales/recommend", "/smart-sales/generate"]:
        r = await c.post(path, json={"empresa_id": empresa_id, "message": "Quiero un polo negro talla M"})
        print(f"POST {path}: {r.status_code} {r.text[:200]}")
    
    # 5. Reporting - check what exists
    print("\n--- 5. Reporting inventory ---")
    r = await c.get("/reporting/executive/pdf")
    print(f"GET /reporting/executive/pdf: {r.status_code} {r.text[:200]}")
    
    # 6. Admin endpoints
    print("\n--- 6. Admin endpoints ---")
    r = await c.get("/admin/dashboard")
    print(f"GET /admin/dashboard: {r.status_code} {r.text[:200]}")
    
    await c.aclose()

asyncio.run(main())
