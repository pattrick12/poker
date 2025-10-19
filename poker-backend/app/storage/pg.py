import os
import asyncpg
import logging

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/poker")

class PostgresClient:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(DATABASE_URL)
                await self.init_db()
            except Exception as e:
                logging.error(f"Failed to connect to DB: {e}")

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def init_db(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    chips BIGINT DEFAULT 1000,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS game_audit (
                    id SERIAL PRIMARY KEY,
                    table_id TEXT NOT NULL,
                    hand_id TEXT NOT NULL,
                    server_seed TEXT,
                    server_secret TEXT,
                    commitment TEXT,
                    events JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

    async def get_or_create_user(self, username: str):
        async with self.pool.acquire() as conn:
            # Simple ID gen
            user_id = f"p-{username}"
            row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
            if not row:
                await conn.execute(
                    "INSERT INTO users (id, username, chips) VALUES ($1, $2, $3)",
                    user_id, username, 1000
                )
                return {"id": user_id, "username": username, "chips": 1000}
            return dict(row)

    async def log_hand(self, table_id, hand_id, seed, secret, commitment, events):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO game_audit (table_id, hand_id, server_seed, server_secret, commitment, events)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                table_id, hand_id, str(seed), secret, commitment, events
            )

pg_client = PostgresClient()
