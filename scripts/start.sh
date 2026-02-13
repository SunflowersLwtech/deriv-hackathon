#!/bin/bash
set -e

echo "==========================================="
echo "  TradeIQ — One-Click Startup"
echo "==========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "  .env file not found!"
    echo "  Copy .env.example to .env and fill in your keys."
    echo "  cp .env.example .env"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "  Docker not found. Please install Docker Desktop."
    exit 1
fi

echo ""
echo "  Step 1: Building containers..."
docker compose build

echo ""
echo "  Step 2: Starting services..."
docker compose up -d

echo ""
echo "  Step 3: Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/healthz/ > /dev/null 2>&1; then
        echo "  Backend is ready!"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "  Step 4: Seeding demo data..."
curl -s -X POST http://localhost:8000/api/demo/seed/ 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  (seed may have already been run)"

echo ""
echo "==========================================="
echo "  TradeIQ is running!"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API:      http://localhost:8000/api/"
echo ""
echo "  Demo:     http://localhost:3000/demo"
echo "==========================================="
