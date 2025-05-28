#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
INSTALL_MODE="dev"
INSTALL_SYSTEMD=false
INSTALL_DEPS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod)
            INSTALL_MODE="prod"
            shift
            ;;
        --systemd)
            INSTALL_SYSTEMD=true
            shift
            ;;
        --deps)
            INSTALL_DEPS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./install.sh [--prod] [--systemd] [--deps]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Starting MediaLab Manager installation...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Install system dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    echo -e "${BLUE}Installing system dependencies...${NC}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-venv python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-venv python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-venv python3-pip
    else
        echo -e "${YELLOW}Warning: Could not detect package manager. Please install python3-venv and python3-pip manually.${NC}"
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install the package
echo -e "${BLUE}Installing MediaLab Manager...${NC}"
if [ "$INSTALL_MODE" = "dev" ]; then
    echo -e "${YELLOW}Installing in development mode${NC}"
    pip install -e .
else
    echo -e "${YELLOW}Installing in production mode${NC}"
    pip install .
fi

if [ $? -ne 0 ]; then
    echo "Error: Failed to install package"
    exit 1
fi

# Create systemd service if requested
if [ "$INSTALL_SYSTEMD" = true ]; then
    echo -e "${BLUE}Creating systemd service...${NC}"
    
    # Get the absolute path of the virtual environment's Python
    VENV_PYTHON=$(realpath .venv/bin/python)
    
    # Create the service file
    SERVICE_FILE="/etc/systemd/system/medialab-manager.service"
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=MediaLab Manager Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(dirname $VENV_PYTHON):\$PATH"
ExecStart=$VENV_PYTHON -m app.main
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable the service
    sudo systemctl daemon-reload
    sudo systemctl enable medialab-manager
    sudo systemctl start medialab-manager
    
    echo -e "${GREEN}Systemd service created and started!${NC}"
    echo -e "You can manage the service with:"
    echo -e "  ${BLUE}sudo systemctl status medialab-manager${NC}"
    echo -e "  ${BLUE}sudo systemctl stop medialab-manager${NC}"
    echo -e "  ${BLUE}sudo systemctl start medialab-manager${NC}"
fi

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${GREEN}You can now use the following commands:${NC}"
echo -e "  ${BLUE}mvm${NC} - The CLI tool"
echo -e "  ${BLUE}mvm-service${NC} - The web service"
echo
echo -e "Try it out with: ${BLUE}mvm --help${NC}"
if [ "$INSTALL_SYSTEMD" = false ]; then
    echo -e "Or start the service with: ${BLUE}mvm-service${NC}"
fi 