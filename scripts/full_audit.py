"""PILOT READINESS ENTERPRISE V1 — Full Audit Suite"""
import asyncio, httpx, json, time, sys
from uuid import uuid4

BASE = "http://127.0.0.1:8000/api/v1"
PASS, FAIL = 0, 0
errors = []
results_log = []

def log_result(phase, name, status, detail=""):
    global PASS, FAIL
    if status == "PASS":
        PASS += 1
    else:
        FAIL += 1
        errors.append(f"[{phase}] {name}: {detail}")
    results_log.append((phase, name, status, detail))
    print(f"  [{status}] {name}")

class Client:
    def __init__(self):
        self.c = httpx.AsyncClient(base_url=BASE, timeout=30)
        self.token = ""
        self.empresa_id = ""
    
    async def login(self, email, password):
        for attempt in range(5):
            r = await self.c.post("/auth/login", json={"email": email, "password": password})
            if r.status_code == 429:
                print(f"  Rate limited, waiting 65s (attempt {attempt+1})...")
                await asyncio.sleep(65)
                continue
            if r.status_code == 200:
                d = r.json()
                self.token = d["access_token"]
                self.empresa_id = d["user"]["empresa_id"]
                self.c.headers["Authorization"] = f"Bearer {self.token}"
                return True
            print(f"  Login failed: {r.status_code} {r.text[:100]}")
            return False
        return False

    async def close(self):
        await self.c.aclose()

async def phase1_e2e(c: Client):
    """FASE 1 — End to End Audit"""
    print("\n=== FASE 1: E2E AUDIT ===")
    cid, did = None, None
    
    r = await c.c.post("/customers", json={
        "full_name": "Audit Cliente Final", "email": f"audit-{uuid4().hex[:8]}@test.io",
        "phone": "+51999000001", "lead_status": "new", "priority": "hot"
    })
    if r.status_code == 201:
        cid = r.json()["id"]
        log_result("F1", "Create customer", "PASS")
    else:
        log_result("F1", "Create customer", "FAIL", f"{r.status_code} {r.text[:100]}")
    
    if cid:
        r = await c.c.patch(f"/customers/{cid}", json={"lead_status": "qualified", "lead_score": 80})
        if r.status_code == 200 and r.json()["lead_status"] == "qualified":
            log_result("F1", "Update customer -> qualified", "PASS")
        else:
            log_result("F1", "Update customer", "FAIL", f"{r.status_code} {r.text[:100]}")
    
    if cid:
        r = await c.c.post("/pipeline/deals", json={
            "customer_id": cid, "title": "Audit Deal E2E", "estimated_value": 5000.0,
            "stage": "new_lead", "probability": 10, "channel": "whatsapp"
        })
        if r.status_code == 201:
            did = r.json()["id"]
            log_result("F1", "Create pipeline deal", "PASS")
        else:
            log_result("F1", "Create pipeline deal", "FAIL", f"{r.status_code} {r.text[:100]}")
    
    if did:
        moves = [("contacted",25), ("qualified",45), ("proposal",65), ("negotiation",80)]
        for st, prob in moves:
            r = await c.c.post(f"/pipeline/deals/{did}/move-stage", json={"target_stage": st, "probability": prob})
            if r.status_code == 200 and r.json()["stage"] == st:
                log_result("F1", f"Move -> {st}", "PASS")
            else:
                log_result("F1", f"Move -> {st}", "FAIL", f"{r.status_code} {r.text[:100]}")
        
        r = await c.c.post(f"/pipeline/deals/{did}/move-stage", json={"target_stage": "won", "probability": 100, "won_reason": "Audit OK"})
        log_result("F1", "Close deal -> won", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")
    
    # Read-only endpoints
    endpoints = [
        ("Pipeline board", "GET", "/pipeline/board"),
        ("Pipeline dashboard", "GET", "/pipeline/dashboard"),
        ("Pipeline metrics", "GET", "/pipeline/metrics"),
        ("Pipeline funnel", "GET", "/pipeline/funnel"),
        ("Pipeline alerts", "GET", "/pipeline/alerts"),
        ("Pipeline recommendations", "GET", "/pipeline/recommendations"),
        ("Automation rules", "GET", "/automation/rules"),
        ("Automation tasks", "GET", "/automation/tasks"),
        ("Automation metrics", "GET", "/automation/metrics"),
        ("CRM metrics", "GET", "/crm/metrics"),
        ("Customer list", "GET", "/customers?limit=5"),
        ("Order list", "GET", "/orders?limit=5"),
        ("Order metrics", "GET", "/orders/metrics"),
    ]
    for name, method, path in endpoints:
        r = await c.c.get(path)
        log_result("F1", name, "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")

    # Order creation
    r = await c.c.post("/orders", json={
        "customer_name": "Audit Client", "customer_phone": "+51999000001",
        "delivery_type": "delivery", "delivery_address": "Av. Audit 123",
        "status": "confirmed",
        "items": [{"product_name": "Audit Product", "quantity": 1, "price": 5000.0}]
    })
    log_result("F1", "Create order", "PASS" if r.status_code == 201 else "FAIL", f"{r.status_code} {r.text[:100]}")

    # Executive dashboard & reporting
    r = await c.c.get("/executive-dashboard")
    log_result("F1", "Executive dashboard", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")
    
    r = await c.c.get("/reporting/metrics?period=month")
    log_result("F1", "Reporting metrics", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code} {r.text[:100]}")

    r = await c.c.get("/reporting/top-products?limit=5")
    log_result("F1", "Top products report", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")

    # Automation engine run
    r = await c.c.post("/automation/run")
    log_result("F1", "Run automation engine", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")

async def phase2_roles(c: Client):
    """FASE 2 — Role & Permission Audit"""
    print("\n=== FASE 2: ROLE & PERMISSION AUDIT ===")
    
    r = await c.c.get("/customers?limit=5")
    log_result("F2", "demo@fashionsales.ai (admin role) GET /customers", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")
    
    r = await c.c.post("/customers", json={"full_name":"Perm Test","email":"perm@test.io","phone":"+51999000002","lead_status":"new","priority":"normal"})
    log_result("F2", "demo@fashionsales.ai POST /customers (write)", "PASS" if r.status_code == 201 else "FAIL", f"{r.status_code}")
    
    r = await c.c.get("/pipeline/board")
    log_result("F2", "Access pipeline board", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")
    
    r = await c.c.get("/admin/users")
    log_result("F2", "Non-admin access to /admin/users (should be 401/403)", "PASS" if r.status_code in (401, 403) else "ISSUE", f"{r.status_code} (should be denied)")

async def phase3_loadtest(c: Client):
    """FASE 3 — Load Test (simplified)"""
    print("\n=== FASE 3: LOAD TEST (sequential, measure latencies) ===")
    endpoints = [
        ("Auth refresh", "POST", "/auth/refresh", {"refresh_token": ""}),
        ("Pipeline board", "GET", "/pipeline/board", None),
        ("Pipeline dashboard", "GET", "/pipeline/dashboard", None),
        ("Pipeline metrics", "GET", "/pipeline/metrics", None),
        ("CRM metrics", "GET", "/crm/metrics", None),
        ("Executive dashboard", "GET", "/executive-dashboard", None),
        ("Reporting metrics", "GET", "/reporting/metrics?period=month", None),
        ("Automation metrics", "GET", "/automation/metrics", None),
        ("Customer list", "GET", "/customers?limit=25", None),
        ("Order list", "GET", "/orders?limit=25", None),
    ]
    for name, method, path, body in endpoints:
        times = []
        for _ in range(5):
            t0 = time.time()
            if method == "GET":
                r = await c.c.get(path)
            else:
                r = await c.c.post(path, json=body or {})
            elapsed = time.time() - t0
            times.append(elapsed)
        avg = sum(times) / len(times)
        max_t = max(times)
        status = "PASS" if r.status_code == 200 and avg < 1.0 else ("SLOW" if avg < 3.0 else "FAIL")
        log_result("F3", f"{name} (avg={avg:.3f}s max={max_t:.3f}s)", status, f"status={r.status_code}")

async def phase4_db_stress(c: Client):
    """FASE 4 — Database Stress (with 25 customers already)"""
    print("\n=== FASE 4: DATABASE STRESS TEST ===")
    r = await c.c.get("/customers?limit=100")
    log_result("F4", "List 100 customers", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")
    
    r = await c.c.get("/pipeline/board")
    log_result("F4", "Pipeline board with data", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")
    
    r = await c.c.get("/pipeline/dashboard")
    log_result("F4", "Pipeline dashboard with data", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")
    
    r = await c.c.get("/orders?limit=100")
    log_result("F4", "List 100 orders", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")

async def phase8_smart_sales(c: Client):
    """FASE 8 — Smart Sales Validation"""
    print("\n=== FASE 8: SMART SALES VALIDATION ===")
    
    r = await c.c.post("/smart-sales/analyze", json={
        "empresa_id": c.empresa_id, "message": "Quiero un polo negro talla M"
    })
    log_result("F8", "POST /smart-sales/analyze", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code} {r.text[:100]}")
    if r.status_code == 200:
        print(f"    Entities: {r.json()}")
    
    r = await c.c.post("/smart-sales/recommend", json={
        "empresa_id": c.empresa_id, "current_product_type": "polo"
    })
    log_result("F8", "POST /smart-sales/recommend", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code} {r.text[:100]}")
    if r.status_code == 200:
        print(f"    Recommendations: {len(r.json().get('recommendations', []))}")
    
    r = await c.c.post("/smart-sales/generate", json={
        "empresa_id": c.empresa_id, "message": "Hola, busco un vestido elegante para una fiesta"
    })
    log_result("F8", "POST /smart-sales/generate", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code} {r.text[:100]}")
    if r.status_code == 200:
        resp = r.json().get("response", "")
        print(f"    Response length: {len(resp)} chars")

async def main():
    c = Client()
    print("Logging in as demo@fashionsales.ai...")
    ok = await c.login("demo@fashionsales.ai", "Demo@2024!")
    if not ok:
        print("FATAL: Cannot login. Aborting.")
        sys.exit(1)
    print(f"  empresa_id: {c.empresa_id}")
    
    await phase1_e2e(c)
    await phase2_roles(c)
    await phase3_loadtest(c)
    await phase4_db_stress(c)
    await phase8_smart_sales(c)
    await c.close()
    
    print(f"\n{'='*60}")
    print(f"FULL AUDIT RESULTS: {PASS} PASSED, {FAIL} FAILED")
    if errors:
        print(f"\nFAILURES:")
        for e in errors:
            print(f"  - {e}")
    print(f"\n{'='*60}")
    
    # Production Score
    total = PASS + FAIL
    if total == 0:
        score = 0
    else:
        score = int((PASS / total) * 100)
    
    print(f"\n=== FASE 9: PRODUCTION SCORE ===")
    print(f"  Total tests: {total}")
    print(f"  Passed: {PASS}")
    print(f"  Failed: {FAIL}")
    print(f"  Score: {score}/100")
    
    if FAIL == 0:
        print("  Verdict: ENTERPRISE READY")
    elif score >= 80:
        print("  Verdict: PRODUCTION READY")
    elif score >= 50:
        print("  Verdict: DEMO READY")
    else:
        print("  Verdict: NOT READY")
    
    sys.exit(0 if FAIL == 0 else 1)

asyncio.run(main())
