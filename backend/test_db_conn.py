import asyncio
import asyncpg

async def main():
    print("Connecting...", flush=True)
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/postgres', timeout=3)
        print("Connected!", flush=True)
        await conn.close()
    except Exception as e:
        print(f"Error: {e}", flush=True)

asyncio.run(main())
