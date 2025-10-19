import os
import nats
from nats.js import JetStreamContext

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

class NatsClient:
    def __init__(self):
        self.nc = None
        self.js: JetStreamContext = None

    async def connect(self):
        self.nc = await nats.connect(NATS_URL)
        self.js = self.nc.jetstream()

    async def publish(self, subject, payload):
        if not self.js:
            await self.connect()
        # payload should be bytes
        if isinstance(payload, str):
            payload = payload.encode()
        await self.js.publish(subject, payload)

    async def close(self):
        if self.nc:
            await self.nc.close()

nats_client = NatsClient()
