from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from strawberry.asgi import GraphQL
from app.graphql.schema import schema
from app.ws.manager import manager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graphql_app = GraphQL(schema, subscription_protocols=["graphql-ws"])

app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)

@app.websocket("/ws/{table_id}")
async def websocket_endpoint(websocket: WebSocket, table_id: str):
    await manager.connect(websocket, table_id)
    
    # Send initial state from Redis if available
    try:
        from app.storage.redis_client import redis_client
        from app.graphql.schema import get_engine
        import json
        
        # Get the raw JSON string from the 'data' field of the hash
        data = await redis_client.redis.hget(f"table:{table_id}:state", "data")
        if data:
            state = json.loads(data)
            await websocket.send_json({
                "type": "update", 
                "table_id": table_id,
                "seq": 0, 
                "state": state,
                "events": []
            })
    except Exception as e:
        print(f"Error sending initial state: {e}")

    try:
        while True:
            data = await websocket.receive_json()
            print(f"[WS] Received message: {data}")
            
            # Route action to TableEngine
            if data.get("type") == "action":
                try:
                    from app.graphql.schema import get_engine
                    print(f"[WS] Routing action to engine for table {table_id}")
                    engine = get_engine(table_id)
                    await engine.enqueue(data)
                    print(f"[WS] Action enqueued successfully")
                except Exception as e:
                    print(f"[WS] Error processing action: {e}")
                    import traceback
                    traceback.print_exc()
    except WebSocketDisconnect:
        print(f"[WS] Client disconnected from table {table_id}")
        await manager.disconnect(websocket, table_id)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
