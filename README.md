# quick-md
A git submodule utility for maintaining a markdown notebook with both TUI and web interfaces

## Features

- **TUI (Terminal User Interface)**: Fast keyboard-driven interface using Textual
- **Web Interface**: Browser-based interface for editing and viewing markdown files
- **Dual Access**: Both interfaces run in parallel - use whichever you prefer!
- **Password Protection**: Optional password authentication for web access
- **Configurable Title**: Customize your notebook's display name
- **MathJax Support**: Write mathematical equations using `$` for inline math and `$$` for display equations
- **Docker Support**: Run in a container with proper file ownership
- Create and manage markdown pages with automatic date prefixing
- Add images from screenshots directory with automatic copying and markdown link generation
- Add videos with automatic ffmpeg processing and compression
- View and edit markdown with live preview (web interface)
- Copy markdown links and HTML tags to clipboard

## Setup

You can run Quick-md either natively or using Docker.

### Option 1: Docker (Recommended)

Docker ensures all dependencies are properly installed and files are owned by your user.

#### Prerequisites
- Docker
- Docker Compose

#### Quick Start

1. Clone this repository as a submodule in your markdown notebook:
   ```bash
   git submodule add <repository-url> quick-md
   git submodule update --init --recursive
   ```

2. Navigate to the quick-md directory:
   ```bash
   cd quick-md
   ```

3. Build and run with Docker Compose:
   ```bash
   # Set your user ID and group ID (ensures files are owned by you)
   export USER_ID=$(id -u)
   export GROUP_ID=$(id -g)
   
   # Build and start the container
   docker compose up --build
   ```

4. Access the web interface at **http://localhost:6580**

> **Note:** Docker runs in web-only mode (no TUI). For the TUI interface, use native installation.

#### Docker Configuration Options

**Run in Background:**
```bash
# Start detached (runs in background)
docker compose up -d

# View logs
docker compose logs -f

# Stop when running in background
docker compose down
```

**Custom Port:**
```bash
# Use a different port
export PORT=8080
docker compose up
```

**Password Protection:**

1. Create `.env` file from template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your password:
   ```bash
   QUICK_MD_PASSWORD=your_secure_password_here
   ```

3. Edit `docker-compose.yml` and uncomment the command line:
   ```yaml
   command: python3 main.py --web-only --port 6580 --password-protect
   ```

4. Start or restart the container:
   ```bash
   docker compose up -d
   ```

The password is passed via the `QUICK_MD_PASSWORD` environment variable (no interactive prompt needed in Docker).

**Custom Notebook Location:**
Edit the volumes section in `docker-compose.yml`:
```yaml
volumes:
  - /path/to/your/notebook:/notebook
```

#### Stopping the Container
```bash
# Stop the container
docker compose down

# Stop and remove volumes (removes all data - careful!)
docker compose down -v

# Restart after config changes
docker compose restart
```

> See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for a quick reference guide.

### Option 2: Native Installation

#### Prerequisites
- Python 3.6 or higher
- Git
- ffmpeg (for video processing)

#### Installation

1. Clone this repository as a submodule in your markdown notebook:
   ```bash
   git submodule add <repository-url> quick-md
   git submodule update --init --recursive
   ```

2. Install the required dependencies:
   ```bash
   cd quick-md
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python3 main.py
   ```

The TUI will launch and the web server will start automatically. The web server address will be displayed in the bottom right of the TUI (default: http://0.0.0.0:6580).

### Command Line Options

```bash
# Custom port
python3 main.py --port 8080

# Enable password protection (interactive prompt)
python3 main.py --password-protect

# Or set password via environment variable
export QUICK_MD_PASSWORD=your_password
python3 main.py --password-protect

# Web-only mode (no TUI) - useful for servers/Docker
python3 main.py --web-only

# Combine options
python3 main.py --web-only --port 8080 --password-protect
```

**Available Options:**
- `--port PORT`: Specify web server port (default: 6580)
- `--password-protect`: Enable password authentication for web access
- `--web-only`: Run web server only without TUI (keeps server alive)

**Password Methods:**
1. **Interactive**: Run with `--password-protect` and enter password when prompted
2. **Environment Variable**: Set `QUICK_MD_PASSWORD` before running (useful for scripts/Docker)

## Usage

### TUI (Terminal Interface)

Navigate the menu using:
- Number keys (1-4) to select options
- `q` to quit
- Arrow keys and Enter to interact with forms

Features:
- **New Page**: Create a new markdown page with date-prefixed filename
- **Add Image**: Copy the most recent screenshot from your screenshots directory
- **Add Video**: Process and add videos with customizable resolution and compression

### Web Interface

Access the web interface at http://localhost:6580 in your browser (or your custom port).

**Features:**
- **View Pages**: Browse all markdown files with rendered preview (supports MathJax)
- **Edit Pages**: Split-panel editor with live preview (MathJax renders in real-time)
- **Create Pages**: Web form to create new pages with custom titles
- **Upload Images**: Drag-and-drop image upload with instant markdown link generation
- **Upload Videos**: Video upload with processing options (resolution, compression via ffmpeg)
- **Media Library**: Browse all images and videos with one-click markdown/HTML copying
- **Math Support**: Write equations using `$...$` for inline and `$$...$$` for display equations
- **Password Protection**: Optional authentication (see command line options)
- **Custom Titles**: Both notebook title and individual page titles are configurable

**Page Titles:**
The web interface displays actual page titles (extracted from the first H1 heading) instead of filenames in the browser tab and page headers.

### Mathematical Equations

The web interface supports MathJax for rendering mathematical equations:

**Inline equations** - Use single dollar signs:
```markdown
The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$ which solves ax² + bx + c = 0.
```

**Display equations** - Use double dollar signs:
```markdown
$$
E = mc^2
$$

$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$
```

### Configuration

The application will create a `.qmd_conf` file in the parent directory on first run. This file can be customized to fit your needs.

**Notebook Title:**
```yaml
notebook_title: "My Research Notes"
```
This appears in the web interface header and page titles.

**Markdown Pages:**
```yaml
Markdown:
  - filename: "2024_01_15_my_page.md"
    title: "My Page Title"
  - "2024_01_14_another.md"  # Old format (backward compatible)
```
The new format stores both the filename and original title for each page.

**Local Paths** (relative to config file):
```yaml
local:
  md_path: .                    # Markdown files directory
  images_path: assets           # Images directory  
  videos_path: assets           # Videos directory
  figures_path: assets          # Figures directory
  files_path: assets            # Other files directory
  main_md: main.md             # Main index file
```

**Global Paths** (system-wide):
```yaml
global:
  images_dir: ~/Pictures/Screenshots/  # Default screenshots location
  videos_dir: ~/Videos                 # Default videos location
```

**Important Notes:**
- All paths in the `local` section are stored as **relative paths** and automatically resolved to absolute paths at runtime
- Media paths (images/videos) are auto-detected based on where files are uploaded
- The config file maintains backward compatibility with older formats

## Architecture

The application uses a shared `ConfigurationManager` that both the TUI and web interface access. This ensures feature parity between both interfaces:

- Both use the same underlying functions from `utils/` directory
- Changes made in one interface are immediately visible in the other
- The web server runs in a background thread, allowing both interfaces to run simultaneously
- Docker mode runs web-only (no TUI) with the server kept alive indefinitely

**Configuration Storage:**
- The config file stores relative paths which are resolved to absolute paths at runtime
- Both the raw config (relative) and resolved config (absolute) are maintained
- This allows the notebook to be moved without breaking path references

## Requirements

### Python Dependencies
- PyYAML>=6.0
- pyperclip>=1.8.2
- textual>=0.47.0
- Flask>=3.0.0
- markdown>=3.5.0

### System Dependencies
- ffmpeg (for video processing)
- Docker & Docker Compose (optional, for containerized deployment)
