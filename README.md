# medialab-manager

## Installation

### Prerequisites
- Python 3.x
- pip3
- (Optional) System package manager (apt-get, dnf, or yum) for installing dependencies

### Installation Options

The installation script (`install.sh`) supports several options:

```bash
./install.sh [options]
```

Available options:
- `--prod`: Install in production mode (default is development mode)
- `--systemd`: Create and enable a systemd service
- `--deps`: Install system dependencies (requires sudo)
- `--reinstall`: Remove existing installation and perform a fresh install
- `--symlink`: Create system-wide symlinks for commands (requires sudo)

### Installation Methods

1. **Basic Installation** (Development Mode):
```bash
./install.sh
```

2. **Production Installation with Systemd Service**:
```bash
sudo ./install.sh --prod --systemd --symlink
```

3. **Full Installation with Dependencies**:
```bash
sudo ./install.sh --deps --symlink
```

4. **Reinstall** (if you need a fresh start):
```bash
./install.sh --reinstall
```

### Using the Commands

After installation, you can use the commands in three ways:

1. **Using the full path** (no additional setup needed):
```bash
.venv/bin/mvm
.venv/bin/mvm-service
```

2. **Activating the virtual environment** (recommended for development):
```bash
source .venv/bin/activate
mvm
mvm-service
```

3. **Using system-wide commands** (if installed with --symlink):
```bash
mvm
mvm-service
```

### Command Usage

- `mvm`: The CLI tool for managing MediaLab
- `mvm-service`: The web service for MediaLab

Try the CLI tool with:
```bash
mvm --help
```

### Service Management

If installed with `--systemd`, you can manage the service with:
```bash
sudo systemctl status medialab-manager
sudo systemctl stop medialab-manager
sudo systemctl start medialab-manager
```
