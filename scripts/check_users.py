import asyncio, asyncpg
async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/ai_sales_agent_saas')
    users = await conn.fetch("SELECT id, email, empresa_id FROM usuarios ORDER BY created_at")
    memberships = await conn.fetch("SELECT empresa_id, usuario_id, rol FROM empresa_usuarios")
    print("=== USERS ===")
    for u in users:
        print(f"  {u['id']}: {u['email']} (empresa: {u['empresa_id']})")
    print("=== MEMBERSHIPS ===")
    for m in memberships:
        print(f"  user={m['usuario_id']} empresa={m['empresa_id']} role={m['rol']}")
    admins = await conn.fetch("SELECT id, email, rol FROM admin_users")
    print("=== ADMIN USERS ===")
    for a in admins:
        print(f"  {a['id']}: {a['email']} role={a['rol']}")
    await conn.close()
asyncio.run(main())
