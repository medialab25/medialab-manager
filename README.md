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

## Container Setup

### Running with Docker Compose

1. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

2. Access the services:
   - API: http://localhost:4800
   - Client: http://localhost:4810

3. Stop the containers:
   ```bash
   docker-compose down
   ```

### Development Container

This project includes a VS Code dev container configuration for a consistent development environment.

#### Prerequisites
- Docker
- VS Code
- VS Code Remote - Containers extension

#### Setup
1. Clone the repository
2. Open the project in VS Code
3. When prompted, click "Reopen in Container" or use the command palette (F1) and select "Remote-Containers: Reopen in Container"

The dev container includes:
- Python 3.8
- Development tools (black, flake8, pytest)
- Git integration
- VS Code extensions for Python development
- Hot reload for development

#### Development Workflow
1. The dev container automatically mounts your local directory
2. Changes to the code are immediately reflected
3. The API runs with hot reload enabled
4. Use the integrated terminal in VS Code for running commands
