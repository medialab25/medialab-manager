# MediaLab Manager Installation Guide

## Prerequisites
- Python 3
- pip3

## Installation Options

### Basic Production Installation
```bash
./install.sh --prod
```

### Production Installation with System Service
This will install the application as a system service that starts automatically on boot:
```bash
./install.sh --prod --systemd
```

### Complete Production Installation
Includes system dependencies, production mode, and system service:
```bash
./install.sh --prod --systemd --deps
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