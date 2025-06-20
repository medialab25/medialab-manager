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

## Configuration

### Environment Variables

MediaLab Manager supports configuration via environment variables with the `MEDIALAB_` prefix. Copy `env.example` to `.env` and modify as needed:

```bash
cp env.example .env
```

#### Application Settings

```bash
MEDIALAB_PROJECT_NAME=MediaLab Manager
MEDIALAB_VERSION=0.1.0
MEDIALAB_DESCRIPTION=MediaLab Management System
```

#### Database Settings

```bash
MEDIALAB_DATABASE_MAIN_DB_PATH=data/main.db
MEDIALAB_DATABASE_MEDIA_DB_PATH=data/media.db
```

#### Notification Settings

```bash
# SMTP Configuration
MEDIALAB_NOTIFICATION_SMTP_RELAY=192.168.2.1
MEDIALAB_NOTIFICATION_SMTP_PORT=25
MEDIALAB_NOTIFICATION_SMTP_FROM=MediaLab Admin <admin@spongnet.uk>
MEDIALAB_NOTIFICATION_SMTP_TO=medialab25@icloud.com
```

#### Task Settings

```bash
MEDIALAB_TASKS_FILE=tasks.json
```

#### Server Settings (optional - these have defaults)

```bash
MEDIALAB_HOST=0.0.0.0
MEDIALAB_PORT=4800
MEDIALAB_DEBUG_PORT=4801
MEDIALAB_DEBUG=false
```

### Docker Compose

MediaLab Manager includes Docker Compose examples for easy deployment:

#### Simple Deployment

For basic deployment without external dependencies:

```bash
# Copy the simple example
cp docker-compose.simple.yml docker-compose.yml

# Edit environment variables as needed
nano docker-compose.yml

# Start the service
docker-compose up -d
```

#### Full Deployment

For deployment with all features enabled:

```bash
# Copy the full example
cp docker-compose.example.yml docker-compose.yml

# Edit environment variables as needed
nano docker-compose.yml

# Start the service
docker-compose up -d
```

#### Key Configuration Points

- **Volumes**: Mount `config.json` for MEDIA_DATA, `tasks.json` for task configuration
- **Data Persistence**: Mount `./data` and `./logs` directories
- **Media Access**: Mount your media storage paths (adjust as needed)
- **Environment Variables**: All settings can be configured via environment variables
- **Ports**: Default web interface on port 4800, debug on 4801

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

### Sudo Access Setup

If your tasks require sudo privileges, you'll need to configure sudo access for the service user. Here's how to set it up:

1. Create a sudoers file for the service:
```bash
sudo visudo -f /etc/sudoers.d/medialab-manager
```

2. Add the following line (replace `media` with your service user and adjust the paths):
```
media ALL=(ALL) NOPASSWD: /usr/bin/snapraid, /path/to/other/script.sh
```

3. Set the correct permissions:
```bash
sudo chmod 440 /etc/sudoers.d/medialab-manager
```

Important security notes:
- Only grant sudo access to specific commands that absolutely need it
- Use absolute paths in the sudoers file
- Regularly audit sudo access
- Document which commands have sudo access and why
- Consider using a dedicated service user with limited permissions

### Available Commands

```bash
mvm
mvm-service
```
