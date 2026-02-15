#!/bin/bash

# NL2SQL Development Server Script
# Usage: ./init.sh [start|stop|restart|status]

set -e

PROJECT_NAME="nl2sql"
VENV_NAME="venv"
PID_FILE=".server.pid"
LOG_FILE="server.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_NAME" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_NAME"
        log_info "Virtual environment created"
    fi
}

# Install dependencies
install_deps() {
    check_venv
    log_info "Installing dependencies..."
    source "$VENV_NAME/bin/activate"
    pip install --upgrade pip
    
    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    log_info "Dependencies installed"
}

# Start the development server
start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_warn "Server is already running (PID: $PID)"
            return
        else
            rm "$PID_FILE"
        fi
    fi
    
    check_venv
    
    log_info "Starting development server..."
    source "$VENV_NAME/bin/activate"
    
    # Start FastAPI with uvicorn
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    log_info "Server started (PID: $(cat $PID_FILE))"
    log_info "Log file: $LOG_FILE"
    log_info "API docs: http://localhost:8000/docs"
}

# Stop the development server
stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_info "Stopping server (PID: $PID)..."
            kill "$PID"
            rm "$PID_FILE"
            log_info "Server stopped"
        else
            log_warn "Server was not running"
            rm "$PID_FILE"
        fi
    else
        log_warn "No PID file found"
        # Try to kill any uvicorn process
        pkill -f "uvicorn main:app" 2>/dev/null || true
    fi
}

# Restart the server
restart() {
    stop
    sleep 1
    start
}

# Check server status
status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_info "Server is running (PID: $PID)"
        else
            log_warn "Server is not running (stale PID file)"
        fi
    else
        log_warn "Server is not running"
    fi
}

# Health check
health() {
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_info "Health check: PASSED"
        return 0
    else
        log_error "Health check: FAILED"
        return 1
    fi
}

# Main
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    health)
        health
        ;;
    install)
        install_deps
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|health|install}"
        exit 1
        ;;
esac
