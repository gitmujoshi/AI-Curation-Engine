#!/bin/bash

# Perimeter Gateway - Quick Start Script
# This script helps you get started with Perimeter in minutes

set -e

echo "🔒 Perimeter AI Security Gateway - Quick Start"
echo "=============================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites met"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before starting services"
    echo ""
    read -p "Press Enter to continue after updating .env..."
fi

# Start services
echo "🚀 Starting Perimeter services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Perimeter Gateway is healthy!"
else
    echo "⚠️  Gateway may still be starting up. Check logs with: docker-compose logs -f"
fi

echo ""
echo "=============================================="
echo "🎉 Perimeter is running!"
echo ""
echo "📍 Service URLs:"
echo "   Gateway:    http://localhost:8000"
echo "   Docs:       http://localhost:8000/docs"
echo "   Health:     http://localhost:8000/health"
echo "   Metrics:    http://localhost:8000/metrics"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "🔑 API Key for testing: pmtr_live_test_key_12345"
echo ""
echo "📚 Next steps:"
echo "   1. Test the API: curl http://localhost:8000/health"
echo "   2. View docs: open http://localhost:8000/docs"
echo "   3. Run examples: python examples/python/basic_usage.py"
echo ""
echo "🛑 To stop: docker-compose down"
echo "=============================================="
