# Real-Time Distributed Poker App

## Quick Start

### 1. Start Infrastructure
```bash
cd poker-backend/docker
docker-compose up --build -d
```

### 2. Seed Database
```bash
cd poker-backend
python -m app.scripts.seed_db
```

### 3. Start Backend (Local)
```bash
cd poker-backend
uvicorn app.main:app --reload --host 0.0.0.0
```

### 4. Start Frontend
```bash
cd frontend
npm run dev
```

### 5. Manual Testing

1. Open `http://localhost:5173` in your browser
2. **Player 1**:
   - Username: `Alice`
   - Table ID: `Table1`
   - Click "Join Table"
3. **Player 2** (open in incognito/new tab):
   - Username: `Bob`
   - Table ID: `Table1`
   - Click "Join Table"

**Expected Behavior:**
- Game starts automatically when 2+ players join
- Players see each other in real-time
- Turn indicator (yellow highlight) shows whose turn it is
- Action buttons (Fold, Check, Call, Raise) work when it's your turn

**Debugging:**
- Open browser console (F12) to see WebSocket logs
- Check backend terminal for action processing logs
- Verify Docker containers are running: `docker ps`

## Architecture

- **Backend**: FastAPI + WebSocket + GraphQL
- **Frontend**: Svelte + Vite + TailwindCSS
- **State**: Redis (hot), Postgres (persistent)
- **Events**: NATS JetStream
- **Concurrency**: Per-table async queue + Redis locks

## Features Implemented

- ✅ Real-time multiplayer
- ✅ WebSocket bidirectional communication
- ✅ Poker FSM (Preflop, Flop, Turn, River, Showdown)
- ✅ Betting rounds with All-In support
- ✅ Anti-cheat (Seed Commitment via HMAC)
- ✅ Persistent game audit logs
- ✅ User accounts
- ✅ Animated UI

## Database Schema

### `users`
- `id` (text): User ID
- `username` (text): Display name
- `chips` (bigint): Current balance
- `created_at` (timestamp)

### `game_audit`
- `id` (serial): Auto-increment
- `table_id` (text): Table identifier
- `hand_id` (text): Unique hand ID
- `server_seed` (text): RNG seed (revealed at showdown)
- `server_secret` (text): Server secret
- `commitment` (text): HMAC commitment
- `events` (jsonb): All game events

### `tables`
- `id` (text): Table ID
- `config` (jsonb): Table configuration
- `created_at` (timestamp)
