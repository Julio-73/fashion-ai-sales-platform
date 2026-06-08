import asyncio, asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/ai_sales_agent_saas')
    print("=== usuarios ===")
    rows = await conn.fetch('SELECT id, email, created_at FROM usuarios')
    for r in rows:
        print(f"  {r['id']}: {r['email']} ({r['created_at']})")
    print("=== admin_users ===")
    rows = await conn.fetch('SELECT id, email, rol FROM admin_users')
    for r in rows:
        print(f"  {r['id']}: {r['email']} role={r['rol']}")
    print("=== empresas ===")
    rows = await conn.fetch('SELECT id, nombre, slug FROM empresas')
    for r in rows:
        print(f"  {r['id']}: {r['nombre']} ({r['slug']})")
    print("=== empresa_usuarios ===")
    rows = await conn.fetch('SELECT empresa_id, usuario_id, rol FROM empresa_usuarios')
    for r in rows:
        print(f"  emp={r['empresa_id']} user={r['usuario_id']} role={r['rol']}")
    await conn.close()

asyncio.run(main())
