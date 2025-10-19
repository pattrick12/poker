import asyncio
from app.storage.pg import pg_client

async def seed():
    print("Connecting to DB...")
    await pg_client.connect()
    
    print("Seeding Users...")
    users = ["Alice", "Bob", "Charlie", "Dave"]
    for name in users:
        user = await pg_client.get_or_create_user(name)
        print(f"Created/Found User: {user}")

    print("Seeding Tables...")
    # In our current schema, tables are created on the fly in Redis/Memory, 
    # but we can add them to Postgres if we had a 'tables' table.
    # The prompt asked for 'tables' table in Postgres schema section 10, 
    # but our pg.py init_db only created 'users' and 'game_audit'.
    # Let's add 'tables' table now.
    
    async with pg_client.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tables (
                id TEXT PRIMARY KEY,
                config JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Insert a default table
        await conn.execute("""
            INSERT INTO tables (id, config) VALUES ($1, $2)
            ON CONFLICT (id) DO NOTHING
        """, "Table1", '{"min_bet": 20}')
        print("Created Table: Table1")

    await pg_client.close()
    print("Seeding Complete.")

if __name__ == "__main__":
    asyncio.run(seed())
