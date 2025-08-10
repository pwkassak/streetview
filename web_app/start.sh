#!/bin/bash

echo "Starting StreetView Route Planner Web App..."
echo "=========================================="

# Function to kill background processes on exit
cleanup() {
    echo "\nShutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Start backend
echo "Starting backend server..."
cd backend
conda activate streetview310
python app.py &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend server..."
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "=========================================="
echo "Application is running!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Press Ctrl+C to stop both servers"
echo "=========================================="

# Keep script running
wait