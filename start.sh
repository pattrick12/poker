#!/bin/bash

# Quick Start Script for Poker App
echo "🎰 Starting Poker App..."

# Check if backend is running
if ! lsof -i:8000 > /dev/null 2>&1; then
    echo "❌ Backend not running on port 8000"
    echo "Please run: cd poker-backend && uvicorn app.main:app --reload"
    exit 1
fi

# Check if frontend is running  
if ! lsof -i:5173 > /dev/null 2>&1; then
    echo "❌ Frontend not running on port 5173"
    echo "Please run: cd frontend && npm run dev"
    exit 1
fi

echo "✅ Backend running on http://localhost:8000"
echo "✅ Frontend running on http://localhost:5173"
echo ""
echo "🎮 How to play:"
echo "1. Open http://localhost:5173"
echo "2. Enter username (e.g., Alice) and table ID (e.g., Table1)"
echo "3. Click 'Join Table'"
echo "4. Open INCOGNITO window (Cmd+Shift+N)"
echo "5. Join same table with different username (e.g., Bob)"
echo "6. Game starts automatically!"
echo ""
echo "📊 Test WebSocket: open test-ws.html in browser"
