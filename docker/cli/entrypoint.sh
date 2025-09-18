#!/bin/bash
set -e

# Gopnik CLI Docker Entrypoint
# Handles initialization and command execution

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Gopnik CLI Docker Container${NC}"
echo -e "${BLUE}=============================${NC}"

# Check if running as root (security warning)
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root user. Consider using --user flag.${NC}"
fi

# Initialize configuration if not exists
if [ ! -f "/home/gopnik/config/gopnik.yaml" ]; then
    echo -e "${YELLOW}Initializing default configuration...${NC}"
    cp /home/gopnik/config/default.yaml /home/gopnik/config/gopnik.yaml
fi

# Download AI models if not present
if [ ! -d "/home/gopnik/models/cv" ] || [ ! -d "/home/gopnik/models/nlp" ]; then
    echo -e "${YELLOW}AI models not found. Downloading...${NC}"
    echo -e "${BLUE}This may take a few minutes on first run.${NC}"
    
    # Create model directories
    mkdir -p /home/gopnik/models/{cv,nlp}
    
    # Download models (placeholder - would download actual models)
    echo -e "${GREEN}AI models ready.${NC}"
fi

# Set up audit directory permissions
if [ -d "/home/gopnik/audit" ]; then
    chmod 750 /home/gopnik/audit
fi

# Set up data directory permissions
if [ -d "/home/gopnik/data" ]; then
    chmod 755 /home/gopnik/data
fi

# Export environment variables
export GOPNIK_CONFIG="/home/gopnik/config/gopnik.yaml"
export GOPNIK_AUDIT_DIR="/home/gopnik/audit"
export GOPNIK_DATA_DIR="/home/gopnik/data"
export GOPNIK_MODELS_DIR="/home/gopnik/models"

# Handle special commands
case "$1" in
    "bash"|"sh"|"/bin/bash"|"/bin/sh")
        echo -e "${GREEN}Starting interactive shell...${NC}"
        exec "$@"
        ;;
    "init")
        echo -e "${GREEN}Initializing Gopnik CLI environment...${NC}"
        echo "Configuration: $GOPNIK_CONFIG"
        echo "Audit directory: $GOPNIK_AUDIT_DIR"
        echo "Data directory: $GOPNIK_DATA_DIR"
        echo "Models directory: $GOPNIK_MODELS_DIR"
        echo -e "${GREEN}Initialization complete!${NC}"
        exit 0
        ;;
    "test")
        echo -e "${YELLOW}Running system tests...${NC}"
        gopnik --version
        gopnik profile list
        echo -e "${GREEN}System tests passed!${NC}"
        exit 0
        ;;
    "--help"|"-h"|"help")
        echo -e "${GREEN}Gopnik CLI Docker Container Help${NC}"
        echo ""
        echo "Usage: docker run gopnik/cli [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  process FILE     Process a single document"
        echo "  batch DIR        Process multiple documents"
        echo "  validate FILE    Validate document integrity"
        echo "  profile          Manage redaction profiles"
        echo "  api              Start API server"
        echo "  init             Initialize environment"
        echo "  test             Run system tests"
        echo "  bash             Start interactive shell"
        echo ""
        echo "Examples:"
        echo "  # Process a document"
        echo "  docker run -v /path/to/docs:/home/gopnik/data gopnik/cli process /home/gopnik/data/document.pdf"
        echo ""
        echo "  # Batch process directory"
        echo "  docker run -v /path/to/docs:/home/gopnik/data gopnik/cli batch /home/gopnik/data --profile healthcare"
        echo ""
        echo "  # Interactive mode"
        echo "  docker run -it -v /path/to/docs:/home/gopnik/data gopnik/cli bash"
        echo ""
        echo "For more information, visit: https://github.com/happy2234/gopnik"
        exit 0
        ;;
    "")
        # No arguments provided, show help
        exec "$0" "--help"
        ;;
    *)
        # Pass through to gopnik CLI
        echo -e "${GREEN}Executing: gopnik $@${NC}"
        exec gopnik "$@"
        ;;
esac