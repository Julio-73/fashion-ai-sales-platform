import sys
from sqlalchemy import create_engine, text

def main():
    print("Starting script...", flush=True)
    try:
        print("Connecting to postgres database with 3s timeout...", flush=True)
        # Connect to 'postgres' default database with timeout
        engine = create_engine(
            'postgresql://postgres:postgres@127.0.0.1:5432/postgres',
            connect_args={'connect_timeout': 3}
        )
        print("Engine created. Connecting...", flush=True)
        with engine.connect() as conn:
            print("Connected! Executing query...", flush=True)
            res = conn.execute(text("SELECT 1"))
            print(f"Query executed successfully, result: {res.fetchone()}", flush=True)
            conn.execute(text("COMMIT"))
            print("Creating database ai_sales_agent_saas...", flush=True)
            try:
                conn.execute(text("CREATE DATABASE ai_sales_agent_saas"))
                print("Database 'ai_sales_agent_saas' created successfully.", flush=True)
            except Exception as e:
                if "already exists" in str(e):
                    print("Database 'ai_sales_agent_saas' already exists.", flush=True)
                else:
                    raise e
    except Exception as exc:
        print(f"Error: {exc}", flush=True)

if __name__ == "__main__":
    main()
