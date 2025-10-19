import asyncio
from collections import deque
from app.storage.redis_client import redis_client
from app.events.nats_client import nats_client
from app.engine.fsm import PokerFSM
from app.engine.rng import DeterministicRNG
from app.ws.manager import manager

class TableEngine:
    def __init__(self, table_id):
        self.table_id = table_id
        self.queue = asyncio.Queue()
        self.fsm = PokerFSM(table_id)
        self.rng = DeterministicRNG(table_id) # Should be seeded per hand in reality
        self.seq = 0  # per-table event sequence

    async def enqueue(self, action):
        await self.queue.put(action)

    async def run(self):
        print(f"[TableEngine] Starting engine for table {self.table_id}")
        while True:
            action = await self.queue.get()
            print(f"[TableEngine] Processing action: {action}")
            try:
                # Acquire lightweight per-table lock in Redis for cross-process safety
                # Using the redis_client wrapper which exposes .lock
                lock = redis_client.lock(f"table-lock:{self.table_id}", timeout=5)
                async with lock:
                    # Apply action deterministically via FSM
                    events, state = await self.fsm.apply(action, rng=self.rng)
                    
                    print(f"[TableEngine] FSM returned {len(events)} events")
                    
                    # Persist hot state to Redis
                    await redis_client.hset(f"table:{self.table_id}:state", mapping=state.to_primitive())
                    
                    # Publish events to NATS (optional, don't let it crash the game)
                    for ev in events:
                        try:
                            await nats_client.publish(f"table.{self.table_id}.events", ev.to_json())
                        except Exception as nats_error:
                            # NATS is optional in development
                            print(f"[TableEngine] NATS publish failed (non-fatal): {nats_error}")
                        self.seq += 1
                    
                    # Broadcast to connected clients (via WebSocket manager)
                    # Sanitize state for public view (hide other players' cards)
                    public_state = state.state.to_dict()
                    # TODO: Mask hole cards for others in a real impl
                    
                    msg = {
                        "type": "update",
                        "table_id": self.table_id,
                        "seq": self.seq,
                        "state": public_state,
                        "events": [ev.payload for ev in events]
                    }
                    print(f"[TableEngine] Broadcasting update to clients")
                    await manager.broadcast(self.table_id, msg)
            except Exception as e:
                print(f"[TableEngine] Error in action processing: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.queue.task_done()
