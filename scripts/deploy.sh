#!/bin/bash
set -e

# Gopnik Deployment Script
# Automates deployment of Gopnik services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.${DEPLOYMENT_ENV}.yml"

# Default values
DEFAULT_SERVICES="gopnik-api gopnik-web nginx-lb redis postgres"
SERVICES="${SERVICES:-$DEFAULT_SERVICES}"
BUILD_IMAGES="${BUILD_IMAGES:-true}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check if required environment variables are set
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        required_vars=(
            "GOPNIK_SECRET_KEY"
            "POSTGRES_PASSWORD"
            "GRAFANA_PASSWORD"
        )
        
        for var in "${required_vars[@]}"; do
            if [ -z "${!var}" ]; then
                log_error "Required environment variable not set: $var"
                exit 1
            fi
        done
    fi
    
    log_success "Prerequisites check passed"
}

create_directories() {
    log_info "Creating required directories..."
    
    directories=(
        "logs"
        "temp"
        "audit"
        "config"
        "secrets"
        "backups"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$PROJECT_ROOT/$dir"
        log_info "Created directory: $dir"
    done
    
    log_success "Directories created"
}

generate_secrets() {
    log_info "Generating secrets..."
    
    secrets_dir="$PROJECT_ROOT/secrets"
    
    # Generate secret key if not exists
    if [ ! -f "$secrets_dir/secret_key.txt" ]; then
        openssl rand -hex 32 > "$secrets_dir/secret_key.txt"
        log_info "Generated secret key"
    fi
    
    # Generate SSL certificates if not exists
    if [ ! -f "$secrets_dir/ssl_cert.pem" ] || [ ! -f "$secrets_dir/ssl_key.pem" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout "$secrets_dir/ssl_key.pem" \
            -out "$secrets_dir/ssl_cert.pem" -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=gopnik.local"
        log_info "Generated SSL certificates"
    fi
    
    # Generate database password if not exists
    if [ ! -f "$secrets_dir/postgres_password.txt" ]; then
        openssl rand -base64 32 > "$secrets_dir/postgres_password.txt"
        log_info "Generated database password"
    fi
    
    # Generate Grafana password if not exists
    if [ ! -f "$secrets_dir/grafana_password.txt" ]; then
        openssl rand -base64 16 > "$secrets_dir/grafana_password.txt"
        log_info "Generated Grafana password"
    fi
    
    # Set proper permissions
    chmod 600 "$secrets_dir"/*
    
    log_success "Secrets generated"
}

backup_data() {
    if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
        log_info "Creating backup before deployment..."
        
        backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        
        # Backup audit logs
        if [ -d "$PROJECT_ROOT/audit" ]; then
            cp -r "$PROJECT_ROOT/audit" "$backup_dir/"
            log_info "Backed up audit logs"
        fi
        
        # Backup configuration
        if [ -d "$PROJECT_ROOT/config" ]; then
            cp -r "$PROJECT_ROOT/config" "$backup_dir/"
            log_info "Backed up configuration"
        fi
        
        # Backup database (if running)
        if docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
            docker-compose -f "$COMPOSE_FILE" exec -T postgres \
                pg_dump -U gopnik gopnik > "$backup_dir/database.sql"
            log_info "Backed up database"
        fi
        
        log_success "Backup created: $backup_dir"
    fi
}

build_images() {
    if [ "$BUILD_IMAGES" = "true" ]; then
        log_info "Building Docker images..."
        
        docker-compose -f "$COMPOSE_FILE" build --no-cache
        
        log_success "Docker images built"
    fi
}

run_migrations() {
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        log_info "Running database migrations..."
        
        # Wait for database to be ready
        log_info "Waiting for database to be ready..."
        timeout=60
        while [ $timeout -gt 0 ]; do
            if docker-compose -f "$COMPOSE_FILE" exec -T postgres \
                pg_isready -U gopnik -d gopnik &> /dev/null; then
                break
            fi
            sleep 2
            timeout=$((timeout - 2))
        done
        
        if [ $timeout -le 0 ]; then
            log_error "Database not ready after 60 seconds"
            exit 1
        fi
        
        # Run migrations
        docker-compose -f "$COMPOSE_FILE" exec -T gopnik-api \
            gopnik migrate --config /app/config/gopnik.yaml
        
        log_success "Database migrations completed"
    fi
}

deploy_services() {
    log_info "Deploying services: $SERVICES"
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d $SERVICES
    
    log_success "Services deployed"
}

health_check() {
    log_info "Performing health checks..."
    
    services_to_check=("gopnik-api" "gopnik-web")
    
    for service in "${services_to_check[@]}"; do
        if echo "$SERVICES" | grep -q "$service"; then
            log_info "Checking health of $service..."
            
            timeout=$HEALTH_CHECK_TIMEOUT
            while [ $timeout -gt 0 ]; do
                if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "healthy"; then
                    log_success "$service is healthy"
                    break
                fi
                
                if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "unhealthy"; then
                    log_error "$service is unhealthy"
                    docker-compose -f "$COMPOSE_FILE" logs "$service"
                    exit 1
                fi
                
                sleep 5
                timeout=$((timeout - 5))
            done
            
            if [ $timeout -le 0 ]; then
                log_error "$service health check timed out"
                docker-compose -f "$COMPOSE_FILE" logs "$service"
                exit 1
            fi
        fi
    done
    
    log_success "All health checks passed"
}

show_status() {
    log_info "Deployment status:"
    echo
    docker-compose -f "$COMPOSE_FILE" ps
    echo
    
    log_info "Service URLs:"
    if echo "$SERVICES" | grep -q "gopnik-api"; then
        echo "  API Server: http://localhost:8000/docs"
    fi
    if echo "$SERVICES" | grep -q "gopnik-web"; then
        echo "  Web Interface: http://localhost:8080"
    fi
    if echo "$SERVICES" | grep -q "grafana"; then
        echo "  Grafana: http://localhost:3000"
    fi
    if echo "$SERVICES" | grep -q "prometheus"; then
        echo "  Prometheus: http://localhost:9090"
    fi
    echo
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old gopnik images (keep last 3)
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.ID}}" | \
        grep "gopnik" | sort -k2 -r | tail -n +4 | awk '{print $3}' | \
        xargs -r docker rmi
    
    log_success "Old images cleaned up"
}

rollback() {
    log_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore from backup if available
    latest_backup=$(ls -t "$PROJECT_ROOT/backups" | head -n1)
    if [ -n "$latest_backup" ]; then
        log_info "Restoring from backup: $latest_backup"
        
        # Restore audit logs
        if [ -d "$PROJECT_ROOT/backups/$latest_backup/audit" ]; then
            rm -rf "$PROJECT_ROOT/audit"
            cp -r "$PROJECT_ROOT/backups/$latest_backup/audit" "$PROJECT_ROOT/"
        fi
        
        # Restore configuration
        if [ -d "$PROJECT_ROOT/backups/$latest_backup/config" ]; then
            cp -r "$PROJECT_ROOT/backups/$latest_backup/config"/* "$PROJECT_ROOT/config/"
        fi
        
        # Restore database
        if [ -f "$PROJECT_ROOT/backups/$latest_backup/database.sql" ]; then
            docker-compose -f "$COMPOSE_FILE" up -d postgres
            sleep 10
            docker-compose -f "$COMPOSE_FILE" exec -T postgres \
                psql -U gopnik -d gopnik < "$PROJECT_ROOT/backups/$latest_backup/database.sql"
        fi
    fi
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    log_info "Starting Gopnik deployment..."
    log_info "Environment: $DEPLOYMENT_ENV"
    log_info "Services: $SERVICES"
    log_info "Compose file: $COMPOSE_FILE"
    echo
    
    # Set trap for cleanup on error
    trap 'log_error "Deployment failed"; rollback; exit 1' ERR
    
    check_prerequisites
    create_directories
    generate_secrets
    backup_data
    build_images
    deploy_services
    run_migrations
    health_check
    cleanup_old_images
    show_status
    
    log_success "Deployment completed successfully!"
}

# Command line argument handling
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    "backup")
        backup_data
        ;;
    "cleanup")
        cleanup_old_images
        ;;
    "help"|"--help"|"-h")
        echo "Gopnik Deployment Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  deploy    Deploy Gopnik services (default)"
        echo "  rollback  Rollback to previous deployment"
        echo "  status    Show deployment status"
        echo "  health    Run health checks"
        echo "  backup    Create backup"
        echo "  cleanup   Clean up old Docker images"
        echo "  help      Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  DEPLOYMENT_ENV           Deployment environment (default: production)"
        echo "  SERVICES                 Services to deploy (default: all)"
        echo "  BUILD_IMAGES             Build Docker images (default: true)"
        echo "  RUN_MIGRATIONS           Run database migrations (default: true)"
        echo "  BACKUP_BEFORE_DEPLOY     Create backup before deploy (default: true)"
        echo "  HEALTH_CHECK_TIMEOUT     Health check timeout in seconds (default: 300)"
        echo ""
        echo "Examples:"
        echo "  # Deploy all services"
        echo "  $0 deploy"
        echo ""
        echo "  # Deploy only API service"
        echo "  SERVICES=\"gopnik-api\" $0 deploy"
        echo ""
        echo "  # Deploy to development environment"
        echo "  DEPLOYMENT_ENV=development $0 deploy"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac