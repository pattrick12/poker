import strawberry
from typing import List, Optional
from datetime import datetime
import asyncio
from app.engine.table_engine import TableEngine

# Global engine registry (In-memory for single node, use Redis/NATS routing for distributed)
engines = {}

def get_engine(table_id):
    if table_id not in engines:
        engines[table_id] = TableEngine(table_id)
        asyncio.create_task(engines[table_id].run())
    return engines[table_id]

@strawberry.type
class Player:
    id: strawberry.ID
    username: str
    chips: int

@strawberry.type
class Card:
    rank: str
    suit: str

@strawberry.type
class TableState:
    table_id: strawberry.ID
    pot: int
    phase: str
    # Simplified for GraphQL return, real state is complex
    
@strawberry.type
class Query:
    @strawberry.field
    async def table(self, table_id: strawberry.ID) -> Optional[TableState]:
        return None

@strawberry.input
class JoinTableInput:
    table_id: strawberry.ID
    username: str
    buyin: int

@strawberry.input
class ActionInput:
    table_id: strawberry.ID
    player_id: strawberry.ID
    action: str
    amount: Optional[int] = None

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def join_table(self, input: JoinTableInput) -> bool:
        engine = get_engine(input.table_id)
        await engine.enqueue({
            "action": "join",
            "player_id": f"p-{input.username}", # Simple ID gen
            "username": input.username,
            "buyin": input.buyin
        })
        return True

    @strawberry.mutation
    async def perform_action(self, input: ActionInput) -> bool:
        engine = get_engine(input.table_id)
        await engine.enqueue({
            "action": input.action,
            "player_id": input.player_id,
            "amount": input.amount
        })
        return True

@strawberry.type
class TableUpdate:
    table_id: strawberry.ID
    payload: str

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def table_updates(self, table_id: strawberry.ID) -> TableUpdate:
        while True:
            await asyncio.sleep(1)
            yield TableUpdate(table_id=table_id, payload="ping")

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
