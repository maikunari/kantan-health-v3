#!/bin/bash

# Healthcare Directory v2 - Development Startup Script

echo "🏥 Healthcare Directory v2 - Starting Development Environment"
echo "============================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Check if Node.js is available
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js and npm are required but not found"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Check required ports
echo "📋 Checking required ports..."
if ! check_port 5000; then
    echo "   Backend API port 5000 is in use"
fi
if ! check_port 3000; then
    echo "   Frontend port 3000 is in use"
fi

# Install backend dependencies
echo ""
echo "📦 Installing backend dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Start backend in background
echo ""
echo "🚀 Starting backend API server..."
python3 app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend API server started (PID: $BACKEND_PID)"
    echo "   API available at: http://localhost:5000"
else
    echo "❌ Failed to start backend API server"
    exit 1
fi

# Start frontend
echo ""
echo "🎨 Starting frontend development server..."
cd frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ Development environment started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:5000"
echo ""
echo "📋 Default Login:"
echo "   Username: admin"
echo "   Password: Set via ADMIN_PASSWORD in config/.env"
echo ""
echo "💡 To stop all services, press Ctrl+C"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down development environment..."
    
    # Kill backend
    if ps -p $BACKEND_PID > /dev/null; then
        kill $BACKEND_PID
        echo "   ✅ Backend API server stopped"
    fi
    
    # Kill frontend
    if ps -p $FRONTEND_PID > /dev/null; then
        kill $FRONTEND_PID
        echo "   ✅ Frontend development server stopped"
    fi
    
    echo "👋 Development environment stopped"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT

# Wait for both processes
wait