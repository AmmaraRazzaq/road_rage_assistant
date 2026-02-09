#!/bin/bash
# Quick Docker deployment script for Road Rage Detection App

echo "=========================================="
echo "Road Rage Detection - Docker Deployment"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo ""
    read -p "Enter your GEMINI_API_KEY: " api_key
    echo "GEMINI_API_KEY=$api_key" > .env
    echo "✅ Created .env file"
fi

echo ""
echo "🔨 Building Docker image..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "🚀 Starting container..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start container!"
    exit 1
fi

echo ""
echo "✅ Deployment successful!"
echo ""
echo "📍 Access your app at: http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  - View logs:     docker-compose logs -f"
echo "  - Stop app:      docker-compose down"
echo "  - Restart app:   docker-compose restart"
echo "  - View status:   docker-compose ps"
echo ""
