#!/bin/bash
# NL2SQL Development Environment Startup Script
# Usage: ./init.sh [command]
# Commands: start (default), stop, restart, build, logs

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Default command
COMMAND=${1:-start}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_info "All dependencies satisfied."
}

start_backend() {
    log_info "Starting backend service..."
    cd "$BACKEND_DIR"
    
    # Check if virtualenv exists
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtualenv and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt 2>/dev/null || true
    
    # Start FastAPI server
    log_info "Starting FastAPI server on http://localhost:8000"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

start_frontend() {
    log_info "Starting frontend service..."
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_info "Installing Node.js dependencies..."
        npm install
    fi
    
    # Start Vite dev server
    log_info "Starting Vite dev server on http://localhost:5173"
    npm run dev
}

start_docker() {
    log_info "Starting all services with Docker Compose..."
    cd "$PROJECT_ROOT"
    docker compose up -d
    log_info "Services started. Check http://localhost:8000 (API) and http://localhost:5173 (Frontend)"
}

stop_services() {
    log_info "Stopping services..."
    
    # Stop Docker Compose
    cd "$PROJECT_ROOT"
    docker compose down 2>/dev/null || true
    
    log_info "Services stopped."
}

restart_services() {
    stop_services
    start_docker
}

build_services() {
    log_info "Building Docker images..."
    cd "$PROJECT_ROOT"
    docker compose build
    log_info "Build complete."
}

show_logs() {
    cd "$PROJECT_ROOT"
    docker compose logs -f
}

show_help() {
    echo "NL2SQL Development Environment Manager"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start      Start development servers (default)"
    echo "  stop       Stop all services"
    echo "  restart    Restart all services"
    echo "  build      Build Docker images"
    echo "  logs       Show Docker logs"
    echo "  help       Show this help message"
    echo ""
    echo "Environment:"
    echo "  ANTHROPIC_API_KEY    Required for Claude API"
    echo "  DATABASE_URL         Database connection string"
}

# Main
case "$COMMAND" in
    start)
        check_dependencies
        start_docker
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    build)
        build_services
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
