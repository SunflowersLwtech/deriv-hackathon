#!/bin/bash
set -e

echo "==========================================="
echo "  TradeIQ — Local Development Mode"
echo "==========================================="

# Check .env
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || true
    echo "  Created .env from template. Please fill in your API keys."
    exit 1
fi

# Start Redis via Docker (if available)
echo "  Starting Redis..."
docker compose up -d redis 2>/dev/null || echo "  Redis via Docker not available, using env REDIS_URL"

# Backend
echo ""
echo "  Starting Backend..."
cd backend
pip install -r requirements.txt --quiet 2>/dev/null || true
python manage.py migrate --noinput 2>/dev/null || true
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
cd ..

# Frontend
echo ""
echo "  Starting Frontend..."
cd frontend
npm install --silent 2>/dev/null || true
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "==========================================="
echo "  Development servers running!"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "==========================================="

# Wait and cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
