#!/bin/bash
# Deployment script for Deep Thinking MCP Server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Python is available (for local deployment)
    if ! command -v python3 &> /dev/null; then
        log_warning "Python 3 is not available. Docker deployment only."
    fi
    
    log_success "Requirements check passed"
}

create_directories() {
    log_info "Creating required directories..."
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$PROJECT_ROOT/config"
    mkdir -p "$PROJECT_ROOT/templates"
    
    log_success "Directories created"
}

backup_existing_data() {
    if [ -f "$DATA_DIR/deep_thinking.db" ]; then
        log_info "Backing up existing database..."
        
        backup_file="$BACKUP_DIR/deep_thinking_$(date +%Y%m%d_%H%M%S).db"
        cp "$DATA_DIR/deep_thinking.db" "$backup_file"
        
        log_success "Database backed up to $backup_file"
    fi
}

deploy_docker() {
    log_info "Deploying with Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    # Build and start services
    docker-compose build
    docker-compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check service status
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker deployment completed successfully"
        log_info "Services status:"
        docker-compose ps
    else
        log_error "Docker deployment failed"
        docker-compose logs
        exit 1
    fi
}

deploy_local() {
    log_info "Deploying locally with Python..."
    
    cd "$PROJECT_ROOT"
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    log_info "Installing dependencies..."
    if command -v uv &> /dev/null; then
        uv sync
    else
        pip install -e .
    fi
    
    # Initialize database and configuration
    log_info "Initializing system..."
    python scripts/start_mcp_server.py --validate-only
    
    log_success "Local deployment completed successfully"
    log_info "To start the server, run: python scripts/start_mcp_server.py"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -m, --mode MODE     Deployment mode: docker, local, or both (default: docker)"
    echo "  -b, --backup        Create backup before deployment"
    echo "  -c, --clean         Clean existing deployment before starting"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Deploy with Docker"
    echo "  $0 -m local         # Deploy locally"
    echo "  $0 -m both -b       # Deploy both ways with backup"
    echo "  $0 -c               # Clean deploy with Docker"
}

clean_deployment() {
    log_info "Cleaning existing deployment..."
    
    # Stop and remove Docker containers
    if command -v docker-compose &> /dev/null; then
        cd "$PROJECT_ROOT"
        docker-compose down -v 2>/dev/null || true
        docker-compose rm -f 2>/dev/null || true
    fi
    
    # Clean Python cache
    find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Main deployment logic
main() {
    local mode="docker"
    local backup=false
    local clean=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--mode)
                mode="$2"
                shift 2
                ;;
            -b|--backup)
                backup=true
                shift
                ;;
            -c|--clean)
                clean=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate mode
    if [[ ! "$mode" =~ ^(docker|local|both)$ ]]; then
        log_error "Invalid mode: $mode. Must be docker, local, or both."
        exit 1
    fi
    
    log_info "Starting deployment with mode: $mode"
    
    # Check requirements
    check_requirements
    
    # Create directories
    create_directories
    
    # Clean if requested
    if [ "$clean" = true ]; then
        clean_deployment
    fi
    
    # Backup if requested
    if [ "$backup" = true ]; then
        backup_existing_data
    fi
    
    # Deploy based on mode
    case $mode in
        docker)
            deploy_docker
            ;;
        local)
            deploy_local
            ;;
        both)
            deploy_local
            deploy_docker
            ;;
    esac
    
    log_success "Deployment completed successfully!"
    
    # Show next steps
    echo ""
    log_info "Next steps:"
    if [[ "$mode" == "docker" || "$mode" == "both" ]]; then
        echo "  - Check Docker services: docker-compose ps"
        echo "  - View logs: docker-compose logs -f"
        echo "  - Stop services: docker-compose down"
    fi
    if [[ "$mode" == "local" || "$mode" == "both" ]]; then
        echo "  - Start local server: python scripts/start_mcp_server.py"
        echo "  - View logs: tail -f logs/mcp_server.log"
    fi
    echo "  - Configure MCP client to use the server"
}

# Run main function
main "$@"