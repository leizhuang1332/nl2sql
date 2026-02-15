#!/bin/bash

# =============================================================================
# init.sh - Project Initialization Script
# =============================================================================
# Run this script at the start of every session to ensure the environment
# is properly set up.
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
PROJECT_DIR=$(pwd)

echo -e "${YELLOW}Initializing NL2SQL project...${NC}"

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env.example if it doesn't exist
if [ ! -f ".env.example" ]; then
    echo "Creating .env.example..."
    cat > .env.example << 'EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o

# Database Configuration
DATABASE_URI=sqlite:///example.db

# Security Configuration
READ_ONLY=true
MAX_RETRIES=3
TIMEOUT=30
EOF
    echo -e "${GREEN}✓ .env.example created${NC}"
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env created (please edit with your API key)${NC}"
fi

# Create tests directory if it doesn't exist
if [ ! -d "tests" ]; then
    echo "Creating tests directory..."
    mkdir -p tests
    touch tests/__init__.py
fi

echo -e "${GREEN}✓ Initialization complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OpenAI API key"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Run 'python -m pytest' to run tests"
echo ""
echo "Ready to continue development."
