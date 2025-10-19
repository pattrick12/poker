# How to Test the Poker App - Step by Step

## Current Issue
Your backend shows only ONE player (`p-hello`) has joined. You need TWO players in SEPARATE browser windows.

## Step-by-Step Instructions

### 1. Open First Browser Window
1. Go to `http://localhost:5173`
2. You should see the purple "Poker Royale" lobby
3. **Don't enter anything yet**

### 2. Open Second Browser Window
1. **Option A**: Open a new **Incognito/Private** window (`Cmd+Shift+N` or `Ctrl+Shift+N`)
2. **Option B**: Use a **different browser** (e.g., if using Chrome, open Firefox)
3. Go to `http://localhost:5173` in this second window

### 3. Join as Player 1 (First Window)
1. In the **first window**:
   - Username: `Alice`
   - Table ID: `Table1`
   - Click **"Join Table"**
2. You should see the poker table appear
3. You'll see "Waiting for players..." or one player listed

### 4. Join as Player 2 (Second Window)  
1. In the **second window** (incognito/different browser):
   - Username: `Bob`
   - Table ID: `Table1` (SAME as Player 1)
   - Click **"Join Table"**
2. Game should start automatically!

###  5. What to Expect
In your **backend terminal**, you should see:
```
[TableEngine] Processing action: {'action': 'join', 'player_id': 'p-Alice', ...}
[TableEngine] Processing action: {'action': 'join', 'player_id': 'p-Bob', ...}
[TableEngine] FSM returned 3 events
```

In **both browser windows**, you should see:
- Both players listed
- Community cards in the center
- A yellow highlight showing whose turn it is
- Action buttons (Fold, Check, Call, Raise)

### 6. Playing
- Switch between the two browser windows
- Click action buttons in the window where your player is highlighted in yellow
- Watch the game progress through Preflop → Flop → Turn → River → Showdown

## Troubleshooting

**If nothing happens:**
- Check backend terminal - do you see TWO WebSocket connections?
- Check browser console (F12) - do you see "Connected to table Table1" in both?

**If you see "FSM returned 0 events":**
- You're clicking when it's not your turn
- Only click in the window with the yellow highlight

**If backend shows no messages:**
- The WebSocket isn't connected
- Try refreshing the browser and joining again
