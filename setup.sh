#!/bin/bash

# Bible Video Generator Setup Script
# This script sets up the development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📚 AI Bible Story Video Generator Setup${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js is not installed. Installing via Docker...${NC}"
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python 3 is not installed. Installing via Docker...${NC}"
fi

echo -e "${YELLOW}🔧 Setting up environment files...${NC}"

# Create backend .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}📝 Creating backend .env file...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}⚠️  Please edit backend/.env and add your API keys:${NC}"
    echo -e "   - OPENAI_API_KEY"
    echo -e "   - REPLICATE_API_TOKEN"
    echo -e "   - ELEVENLABS_API_KEY"
    echo -e "   - AWS credentials (optional for local development)"
fi

# Create frontend .env file if it doesn't exist
if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}📝 Creating frontend .env file...${NC}"
    cp frontend/.env.example frontend/.env
fi

echo -e "${YELLOW}🐳 Building Docker containers...${NC}"

# Build and start services
docker-compose build

echo -e "${YELLOW}🚀 Starting services...${NC}"

# Start all services
docker-compose up -d

echo -e "${GREEN}✅ Setup completed successfully!${NC}"
echo -e "${GREEN}🎉 Your Bible Video Generator is now running!${NC}"
echo ""
echo -e "${BLUE}📍 Access points:${NC}"
echo -e "   🌐 Frontend: http://localhost:3000"
echo -e "   🔧 Backend API: http://localhost:5000"
echo -e "   📊 Redis: localhost:6379"
echo ""
echo -e "${BLUE}🛠️  Development commands:${NC}"
echo -e "   📋 View logs: docker-compose logs -f"
echo -e "   🔄 Restart: docker-compose restart"
echo -e "   ⏹️  Stop: docker-compose down"
echo -e "   🧹 Clean up: docker-compose down -v"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo -e "   • Make sure to configure your API keys in backend/.env"
echo -e "   • The first video generation may take longer as Docker pulls AI model images"
echo -e "   • Check docker-compose logs if you encounter any issues"
echo ""
echo -e "${GREEN}🎬 Ready to generate your first Bible story video!${NC}"