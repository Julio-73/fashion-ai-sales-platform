"""Debug pipeline move to negotiation"""
import asyncio, httpx

BASE = "http://127.0.0.1:8000/api/v1"

async def main():
    c = httpx.AsyncClient(base_url=BASE, timeout=30)
    
    r = await c.post("/auth/login", json={"email": "demo@fashionsales.ai", "password": "Demo@2024!"})
    if r.status_code != 200:
        print(f"Login: {r.status_code}")
        return
    token = r.json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    print("Login OK")
    
    # Create a deal from scratch, move through all stages
    r = await c.post("/customers", json={
        "full_name": "Pipe Debug", "email": "pipe-debug-1@test.io",
        "phone": "+51999000001", "lead_status": "new", "priority": "hot"
    })
    if r.status_code == 201:
        cid = r.json()["id"]
        print(f"Customer: {cid}")
    else:
        # Try getting existing customer
        r = await c.get("/customers?limit=1")
        cid = r.json()[0]["id"] if isinstance(r.json(), list) else r.json()["items"][0]["id"]
        print(f"Using existing customer: {cid}")
    
    r = await c.post("/pipeline/deals", json={
        "customer_id": cid, "title": "Pipe Test Negotiation",
        "estimated_value": 5000.0, "stage": "new_lead",
        "probability": 10, "channel": "whatsapp"
    })
    print(f"Create deal: {r.status_code}")
    if r.status_code != 201:
        print(f"  {r.text[:200]}")
        await c.aclose()
        return
    did = r.json()["id"]
    print(f"Deal ID: {did}")
    
    stages = [
        ("contacted", 25),
        ("qualified", 45),
        ("proposal", 65),
        ("negotiation", 80),
    ]
    for stage, prob in stages:
        r = await c.post(f"/pipeline/deals/{did}/move-stage", json={"target_stage": stage, "probability": prob})
        print(f"Move to {stage}: {r.status_code} {r.text[:200]}")
        if r.status_code == 500:
            # Check server logs
            break
    
    await c.aclose()

asyncio.run(main())
