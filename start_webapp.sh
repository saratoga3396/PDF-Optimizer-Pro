#!/bin/bash
cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found."
    exit 1
fi

echo "Starting PDF Web Tool Server..."
# Run python in background
python app.py &
SERVER_PID=$!

# Wait for server to start (simple sleep or check)
echo "Waiting for server..."
sleep 2

echo "Opening browser..."
open http://localhost:5555

# Keep script running to maintain server
wait $SERVER_PID
