import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/ai_sales_agent_saas')
    rows = await conn.fetch("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    print(f"Tables: {len(rows)}")
    for r in rows:
        cnt = await conn.fetchval(f'SELECT COUNT(*) FROM "{r["tablename"]}"')
        print(f"  {r['tablename']}: {cnt} rows")
    await conn.close()

asyncio.run(main())
