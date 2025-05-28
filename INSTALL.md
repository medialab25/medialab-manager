# MediaLab Manager Installation Guide

## Prerequisites
- Python 3
- pip3
- python3-full (required for virtual environment support)

## Installation Options

### Basic Production Installation
```bash
# First, ensure python3-full is installed
sudo apt install python3-full

# Then run the installation script
./install.sh --prod
```

### Production Installation with System Service
This will install the application as a system service that starts automatically on boot:
```bash
# First, ensure python3-full is installed
sudo apt install python3-full

# Then run the installation script
./install.sh --prod --systemd
```

### Complete Production Installation
Includes system dependencies, production mode, and system service:
```bash
# First, ensure python3-full is installed
sudo apt install python3-full

# Then run the installation script
./install.sh --prod --systemd --deps
```

## Troubleshooting

### If you encounter "externally-managed-environment" error
This error occurs on Debian-based systems due to PEP 668. To fix this:

1. Make sure python3-full is installed:
```bash
sudo apt install python3-full
```

2. Remove any existing virtual environment:
```bash
rm -rf .venv
```

3. Run the installation script again with your desired options.

### If the service fails to start
If you see the service failing to start with "activating (auto-restart)", follow these steps:

1. Stop the service:
```bash
sudo systemctl stop medialab-manager
```

2. Check the service configuration:
```bash
sudo cat /etc/systemd/system/medialab-manager.service
```

3. If the service file is missing or incorrect, create it manually:
```bash
sudo tee /etc/systemd/system/medialab-manager.service << EOF
[Unit]
Description=MediaLab Manager Service
After=network.target

[Service]
Type=simple
User=media
WorkingDirectory=/home/media/medialab-manager
Environment="PATH=/home/media/medialab-manager/.venv/bin:\$PATH"
ExecStart=/home/media/medialab-manager/.venv/bin/python -m app.main
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

4. Reload systemd and restart the service:
```bash
sudo systemctl daemon-reload
sudo systemctl restart medialab-manager
```

5. Check the service status:
```bash
sudo systemctl status medialab-manager
```

6. If it's still failing, check the logs:
```bash
sudo journalctl -u medialab-manager -n 50
```

## Managing the Service
If installed with `--systemd`, you can manage the service using:

- Check service status:
```bash
sudo systemctl status medialab-manager
```

- Stop the service:
```bash
sudo systemctl stop medialab-manager
```

- Start the service:
```bash
sudo systemctl start medialab-manager
```

## Available Commands
After installation, you can use:
- `mvm` - The CLI tool
- `mvm-service` - The web service

Try the CLI tool with:
```bash
mvm --help
```

If not installed as a system service, you can start the service manually with:
```bash
mvm-service
``` 