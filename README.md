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

1. For production:
   ```bash
   docker-compose --profile all up --build
   ```

2. For development:
   ```bash
   # Copy the development environment file
   cp .env.dev.example .env.dev
   
   # Start the development environment
   docker-compose --profile all up --build
   ```

3. Access the services:
   - API: http://localhost:4800
   - Client: http://localhost:4810

4. Stop the containers:
   ```bash
   docker-compose down
   ```

### Development Container

This project includes a VS Code dev container configuration for a consistent development environment that supports both API and client development.

#### Prerequisites
- Docker
- VS Code
- VS Code Remote - Containers extension

#### Setup
1. Clone the repository
2. Copy the development environment file:
   ```bash
   cp .env.dev.example .env.dev
   ```
3. Open the project in VS Code
4. When prompted, click "Reopen in Container" or use the command palette (F1) and select "Remote-Containers: Reopen in Container"

The dev container includes:
- Python 3.8 for API development
- Python 3.11 for client development
- Development tools (black, flake8, pytest)
- Git integration
- VS Code extensions for Python development
- Hot reload for both API and client
- Docker CLI access for client operations

#### Development Workflow
1. The dev container automatically mounts your local directory
2. Both API and client services run with hot reload enabled
3. API runs on port 4800, client on port 4810
4. Changes to either service are immediately reflected
5. Use the integrated terminal in VS Code for running commands
6. Both services can be developed simultaneously in the same container

To start development:
```bash
# Start both services in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Docker Configuration

The project uses a simplified Docker setup with a single `docker-compose.yml` file that handles both development and production environments. This is achieved through:

- Environment variables for configuration
- Docker Compose profiles for service selection
- Conditional volume mounts and commands

### Environment Files

Environment files are used to configure the application for different environments. These files are not tracked in git for security reasons.

1. Set up the development environment:
   ```bash
   # Run the setup script
   ./scripts/setup-dev-env.sh
   
   # Edit the environment file if needed
   nano .env.dev
   ```

2. The script will create a `.env.dev` file with these settings:
   ```ini
   # Development environment configuration
   ENVIRONMENT=development
   
   # Docker configuration
   DOCKERFILE=.devcontainer/Dockerfile
   DOCKER_SOCKET=/var/run/docker.sock
   
   # Mount configurations
   DEV_MOUNT=.:/workspace
   CLIENT_MOUNT=./client:/app
   
   # Command overrides for development
   API_COMMAND=uvicorn app.main:app --host 0.0.0.0 --port 4800 --reload
   CLIENT_COMMAND=uvicorn main:app --host 0.0.0.0 --port 4810 --reload
   ```

Note: The `.env.dev` file should never be committed to version control. Use the setup script to create it locally.

### File Structure
```
.
├── docker-compose.yml        # Main Docker configuration
├── scripts/                  # Utility scripts
│   └── setup-dev-env.sh     # Development environment setup
├── .env.dev                 # Development environment (do not commit)
├── .devcontainer/          # VS Code dev container configuration
│   ├── devcontainer.json
│   └── Dockerfile
└── client/
    └── Dockerfile          # Client-specific Dockerfile
```

### Running the Application

1. Production Mode:
   ```bash
   docker-compose --profile all up --build
   ```

2. Development Mode:
   ```bash
   # Copy the development environment file
   cp .env.dev.example .env.dev
   
   # Start the development environment
   docker-compose --profile all up --build
   ```

3. VS Code Dev Container:
   - Open in VS Code
   - Use "Reopen in Container"
   - Development configuration is automatically applied

The services will be available at:
- API: http://localhost:4800
- Client: http://localhost:4810
