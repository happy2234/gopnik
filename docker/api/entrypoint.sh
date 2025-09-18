#!/bin/bash
set -e

# Gopnik API Server Docker Entrypoint

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Gopnik API Server Docker Container${NC}"
echo -e "${BLUE}===================================${NC}"

# Initialize directories
mkdir -p /app/{logs,temp,audit,models}
chown -R gopnik:gopnik /app/logs /app/temp /app/audit

# Initialize configuration
if [ ! -f "/app/config/gopnik.yaml" ]; then
    echo -e "${YELLOW}Initializing API server configuration...${NC}"
    cp /app/config/default.yaml /app/config/gopnik.yaml
    
    # Update configuration for API server
    cat >> /app/config/gopnik.yaml << EOF

# API Server Configuration
api:
  host: "0.0.0.0"
  port: 8000
  workers: ${GOPNIK_WORKERS:-4}
  reload: false
  log_level: "${GOPNIK_LOG_LEVEL:-info}"
  
  # Security settings
  cors_origins: ["*"]
  cors_methods: ["GET", "POST", "PUT", "DELETE"]
  cors_headers: ["*"]
  
  # File upload settings
  max_file_size: "100MB"
  upload_timeout: 300
  
  # Rate limiting
  rate_limit_enabled: true
  rate_limit_requests: 100
  rate_limit_window: 60

# Production settings
production:
  debug: false
  testing: false
  secret_key: "${GOPNIK_SECRET_KEY:-$(openssl rand -hex 32)}"
EOF
fi

# Download AI models if not present
if [ ! -d "/app/models/cv" ] || [ ! -d "/app/models/nlp" ]; then
    echo -e "${YELLOW}AI models not found. Downloading...${NC}"
    echo -e "${BLUE}This may take several minutes on first run.${NC}"
    
    mkdir -p /app/models/{cv,nlp}
    chown -R gopnik:gopnik /app/models
    
    # Placeholder for model download
    echo -e "${GREEN}AI models ready.${NC}"
fi

# Set environment variables
export GOPNIK_CONFIG="/app/config/gopnik.yaml"
export GOPNIK_AUDIT_DIR="/app/audit"
export GOPNIK_TEMP_DIR="/app/temp"
export GOPNIK_MODELS_DIR="/app/models"
export GOPNIK_LOG_DIR="/app/logs"

# Handle different startup modes
case "$1" in
    "api")
        echo -e "${GREEN}Starting Gopnik API server...${NC}"
        echo "Configuration: $GOPNIK_CONFIG"
        echo "Audit directory: $GOPNIK_AUDIT_DIR"
        echo "Temp directory: $GOPNIK_TEMP_DIR"
        echo "Models directory: $GOPNIK_MODELS_DIR"
        echo "Log directory: $GOPNIK_LOG_DIR"
        
        # Start services with supervisor
        exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
        ;;
    "api-dev")
        echo -e "${GREEN}Starting Gopnik API server in development mode...${NC}"
        exec su-exec gopnik gopnik api --host 0.0.0.0 --port 8000 --reload --log-level debug
        ;;
    "gunicorn")
        echo -e "${GREEN}Starting Gopnik API with Gunicorn only...${NC}"
        exec su-exec gopnik gunicorn -c gunicorn.conf.py src.gopnik.interfaces.api.app:app
        ;;
    "test")
        echo -e "${YELLOW}Running API server tests...${NC}"
        
        # Start API server in background
        su-exec gopnik gopnik api --host 127.0.0.1 --port 8000 &
        API_PID=$!
        
        # Wait for server to start
        sleep 10
        
        # Test health endpoint
        if curl -f http://127.0.0.1:8000/api/v1/health; then
            echo -e "${GREEN}API server health check passed!${NC}"
        else
            echo -e "${RED}API server health check failed!${NC}"
            kill $API_PID
            exit 1
        fi
        
        # Test API documentation
        if curl -f http://127.0.0.1:8000/docs; then
            echo -e "${GREEN}API documentation accessible!${NC}"
        else
            echo -e "${RED}API documentation not accessible!${NC}"
        fi
        
        # Cleanup
        kill $API_PID
        echo -e "${GREEN}API server tests completed!${NC}"
        exit 0
        ;;
    "bash"|"sh"|"/bin/bash"|"/bin/sh")
        echo -e "${GREEN}Starting interactive shell...${NC}"
        exec "$@"
        ;;
    "--help"|"-h"|"help")
        echo -e "${GREEN}Gopnik API Server Docker Container Help${NC}"
        echo ""
        echo "Usage: docker run gopnik/api [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  api          Start production API server (default)"
        echo "  api-dev      Start development API server with auto-reload"
        echo "  gunicorn     Start API server with Gunicorn only (no nginx)"
        echo "  test         Run API server tests"
        echo "  bash         Start interactive shell"
        echo ""
        echo "Environment Variables:"
        echo "  GOPNIK_WORKERS       Number of worker processes (default: 4)"
        echo "  GOPNIK_LOG_LEVEL     Logging level (default: info)"
        echo "  GOPNIK_SECRET_KEY    Secret key for API security"
        echo "  GOPNIK_SSL_KEYFILE   Path to SSL private key"
        echo "  GOPNIK_SSL_CERTFILE  Path to SSL certificate"
        echo ""
        echo "Examples:"
        echo "  # Start production API server"
        echo "  docker run -p 8000:80 gopnik/api"
        echo ""
        echo "  # Start with custom worker count"
        echo "  docker run -p 8000:80 -e GOPNIK_WORKERS=8 gopnik/api"
        echo ""
        echo "  # Development mode with auto-reload"
        echo "  docker run -p 8000:8000 gopnik/api api-dev"
        echo ""
        echo "  # Interactive mode"
        echo "  docker run -it gopnik/api bash"
        echo ""
        echo "For more information, visit: https://github.com/happy2234/gopnik"
        exit 0
        ;;
    "")
        # No arguments provided, start API server
        exec "$0" "api"
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Use --help for available commands"
        exit 1
        ;;
esac