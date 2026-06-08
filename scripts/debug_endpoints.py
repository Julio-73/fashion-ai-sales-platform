import httpx, asyncio

async def main():
    c = httpx.AsyncClient(base_url='http://127.0.0.1:8000/api/v1', timeout=30)
    r = await c.post('/auth/login', json={'email':'demo@fashionsales.ai','password':'Demo@2024!'})
    if r.status_code == 429:
        print("Rate limited, waiting...")
        await asyncio.sleep(65)
        r = await c.post('/auth/login', json={'email':'demo@fashionsales.ai','password':'Demo@2024!'})
    print(f"Login: {r.status_code}")
    if r.status_code != 200:
        print(f"  {r.text[:200]}")
        return
    tok = r.json()['access_token']
    c.headers['Authorization'] = f'Bearer {tok}'

    r2 = await c.post('/customers', json={'full_name':'Debug Client','email':'debug@test.io','phone':'+51999000001','lead_status':'new','priority':'hot'})
    cid = r2.json()['id']
    print(f"Created customer: {r2.status_code} id={cid}")

    r3 = await c.patch(f'/customers/{cid}', json={'lead_status':'qualified','lead_score':80})
    print(f"PATCH customer: {r3.status_code} {r3.text[:200]}")

    r4 = await c.get('/executive-dashboard')
    print(f"Exec dashboard: {r4.status_code}")
    if r4.status_code == 200:
        d = r4.json()
        print(f"  keys: {list(d.keys())}")

    r5 = await c.get('/reporting/metrics?period=month')
    print(f"Reporting metrics: {r5.status_code} {r5.text[:200]}")

    # Check the 500 on pipeline move to negotiation
    r6 = await c.post('/pipeline/deals', json={
        'customer_id': cid, 'title': 'Debug Deal', 'estimated_value': 1000.0,
        'stage': 'proposal', 'probability': 65, 'channel': 'test'
    })
    did = r6.json()['id']
    print(f"Created deal: {r6.status_code} id={did}")
    r7 = await c.post(f'/pipeline/deals/{did}/move-stage', json={
        'target_stage': 'negotiation', 'probability': 80
    })
    print(f"Move to negotiation: {r7.status_code} {r7.text[:300]}")
    await c.aclose()

asyncio.run(main())
