#!/bin/bash

# Healthcare Directory v2 - Startup Script
echo "🏥 Starting Healthcare Directory v2..."

# Function to cleanup background processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM EXIT

# Start Flask backend
echo "🔧 Starting Flask backend on port 5001..."
python3 app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start React frontend
echo "⚛️  Starting React frontend on port 3001..."
cd frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ Healthcare Directory v2 is starting up!"
echo ""
echo "🌐 Frontend: http://localhost:3001"
echo "🔌 Backend:  http://localhost:5001" 
echo "👤 Login:    admin / developer"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID