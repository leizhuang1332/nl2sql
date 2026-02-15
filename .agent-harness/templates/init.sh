#!/bin/bash
# {{PROJECT_NAME}} Development Environment Startup Script

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

COMMAND=${1:-start}

log_info() { echo "[INFO] $1"; }
log_error() { echo "[ERROR] $1"; exit 1; }

check_dependencies() {
    log_info "Checking dependencies..."
    command -v docker &> /dev/null || log_error "Docker required"
    docker compose version &> /dev/null || log_error "Docker Compose required"
}

start_services() {
    check_dependencies
    cd "$PROJECT_ROOT"
    docker compose up -d
    log_info "Services started"
}

stop_services() {
    cd "$PROJECT_ROOT"
    docker compose down 2>/dev/null || true
    log_info "Services stopped"
}

case "$COMMAND" in
    start) start_services ;;
    stop) stop_services ;;
    restart) stop_services; start_services ;;
    *) echo "Usage: $0 {start|stop|restart}" ;;
esac
