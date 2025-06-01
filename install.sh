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
REINSTALL=false
CREATE_SYMLINKS=false

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
        --reinstall)
            REINSTALL=true
            shift
            ;;
        --symlink)
            CREATE_SYMLINKS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./install.sh [--prod] [--systemd] [--deps] [--reinstall] [--symlink]"
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
        sudo apt-get install -y python3-venv python3-pip python3-full
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-venv python3-pip python3-full
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-venv python3-pip python3-full
    else
        echo -e "${YELLOW}Warning: Could not detect package manager. Please install python3-venv and python3-pip manually.${NC}"
    fi
fi

# Handle reinstall if requested
if [ "$REINSTALL" = true ]; then
    echo -e "${YELLOW}Reinstalling MediaLab Manager...${NC}"
    if [ -d ".venv" ]; then
        echo -e "${BLUE}Removing existing virtual environment...${NC}"
        rm -rf .venv
    fi
    if [ -d "build" ]; then
        echo -e "${BLUE}Removing build directory...${NC}"
        rm -rf build
    fi
    if [ -d "dist" ]; then
        echo -e "${BLUE}Removing dist directory...${NC}"
        rm -rf dist
    fi
    if [ -d "*.egg-info" ]; then
        echo -e "${BLUE}Removing egg-info directories...${NC}"
        rm -rf *.egg-info
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

# Create necessary directories
echo -e "${BLUE}Creating necessary directories...${NC}"
mkdir -p logs
# Set permissions to allow writing from any user (since symlinks run as root)
chmod 777 logs
# Create log file with proper permissions
touch logs/app.log
chmod 666 logs/app.log
# If using symlinks, ensure proper ownership
if [ "$CREATE_SYMLINKS" = true ]; then
    # Get the current user and group
    CURRENT_USER=$(whoami)
    CURRENT_GROUP=$(id -gn)
    # Set ownership of logs directory and file
    sudo chown -R $CURRENT_USER:$CURRENT_GROUP logs
fi

# Create systemd service if requested
if [ "$INSTALL_SYSTEMD" = true ]; then
    echo -e "${BLUE}Creating systemd service...${NC}"
    
    # Get the current user and working directory
    CURRENT_USER=$(whoami)
    WORKING_DIR=$(pwd)
    VENV_PYTHON="$WORKING_DIR/.venv/bin/python"
    
    # Create the service file
    SERVICE_FILE="/etc/systemd/system/medialab-manager.service"
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=MediaLab Manager Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$WORKING_DIR
Environment="PATH=$WORKING_DIR/.venv/bin:\$PATH"
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

# Create symlinks if requested
if [ "$CREATE_SYMLINKS" = true ]; then
    echo -e "${BLUE}Creating system-wide symlinks...${NC}"
    sudo ln -sf "$(pwd)/.venv/bin/mvm" /usr/local/bin/mvm
    sudo ln -sf "$(pwd)/.venv/bin/mvm-service" /usr/local/bin/mvm-service
    echo -e "${GREEN}Symlinks created!${NC}"
fi

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${GREEN}You can now use the following commands:${NC}"
if [ "$CREATE_SYMLINKS" = true ]; then
    echo -e "  ${BLUE}mvm${NC} - The CLI tool (available system-wide)"
    echo -e "  ${BLUE}mvm-service${NC} - The web service (available system-wide)"
else
    echo -e "  ${BLUE}.venv/bin/mvm${NC} - The CLI tool"
    echo -e "  ${BLUE}.venv/bin/mvm-service${NC} - The web service"
    echo -e "  Or activate the virtual environment first:"
    echo -e "    ${BLUE}source .venv/bin/activate${NC}"
    echo -e "    Then use: ${BLUE}mvm${NC} or ${BLUE}mvm-service${NC}"
fi
echo
echo -e "Try it out with: ${BLUE}mvm --help${NC}"
if [ "$INSTALL_SYSTEMD" = false ]; then
    echo -e "Or start the service with: ${BLUE}mvm-service${NC}"
fi 