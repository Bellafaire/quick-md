# quick-md
A git submodule utility for maintaining a markdown notebook with both TUI and web interfaces

## Features

- **TUI (Terminal User Interface)**: Fast keyboard-driven interface using Textual
- **Web Interface**: Browser-based interface for editing and viewing markdown files
- **Dual Access**: Both interfaces run in parallel - use whichever you prefer!
- **Password Protection**: Optional password authentication for web access
- **Configurable Title**: Customize your notebook's display name
- **MathJax Support**: Write mathematical equations using `$` for inline math and `$$` for display equations
- **Fully Offline Editor**: The web editor (CodeMirror 6 + Vim keybindings) and MathJax are vendored locally — no CDN calls, so editing and math rendering keep working with no internet connection
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

3. Build and run with the included launcher script:
   ```bash
   ./run.sh
   ```

4. Access the web interface at **http://localhost:6580**

> The `run.sh` script uses `docker run` (no Docker Compose required), so you can
> launch as many independent instances as you like — just give each one a unique
> `--container` name and `--port`.
>
> **Note:** Docker runs in web-only mode (no TUI). For the TUI interface, use native installation.

#### `run.sh` Options

```
./run.sh [options]

  -n, --notebook PATH       Notebook directory to mount (default: parent of this repo)
  -p, --port PORT           Host port (default: 6580)
  -c, --container NAME      Container name (default: quick_md_notebook)
                             Override when running multiple instances.
  --image NAME              Image name (default: quick-md)
  --password PASSWORD       Enable password protection with this password.
  --password-protect        Enable password protection (password read from
                             --password, $QUICK_MD_PASSWORD, or a prompt).
  --screenshots PATH        Read-only mount of a host screenshots directory.
  --videos PATH             Read-only mount of a host videos directory.
  --build                   Force a rebuild of the image.
  -d, --detach              Run in the background.
  -h, --help                Show help.
```

Most flags also have matching environment variables (`QUICK_MD_NOTEBOOK`,
`QUICK_MD_PORT`, `QUICK_MD_CONTAINER`, `QUICK_MD_IMAGE`, `QUICK_MD_PASSWORD`,
`USER_ID`, `GROUP_ID`) which act as defaults.

#### Running Multiple Instances

```bash
# First notebook on port 6580
./run.sh -c quick_md_work       -p 6580 -n ~/notebooks/work

# Second notebook on port 6581
./run.sh -c quick_md_personal   -p 6581 -n ~/notebooks/personal
```

#### Running in the Background

```bash
./run.sh -d                       # start detached
docker logs -f quick_md_notebook  # follow logs
docker stop quick_md_notebook     # stop
```

#### Password Protection

```bash
./run.sh --password-protect                       # from $QUICK_MD_PASSWORD or prompt
./run.sh --password-protect --password 's3cret'   # inline
```

#### Migrating from docker-compose

The old `docker-compose.yml` is kept for backward compatibility, but `run.sh`
is now the recommended way to launch the container. Translate your compose
settings into `run.sh` flags: port → `--port`, container name → `--container`,
notebook volume → `--notebook`, password env → `--password-protect`.

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
- **Edit Pages**: Split-panel editor with live preview (MathJax renders in real-time). Includes a persistent **media sidebar** for browsing/inserting images and videos, sorted by upload date, with grep-style filename search. Optional **Vim mode** (toggle in the editor header) powered by `@replit/codemirror-vim`.
- **Content Width**: A width selector in the nav (Narrow / Standard / Full) controls how wide the reader and editor span — `Full` uses the whole window for maximum editor and preview space. The choice is remembered across sessions.
- **Create Pages**: Web form to create new pages with custom titles
- **Upload Images**: Drag-and-drop image upload with instant markdown link generation
- **Upload Videos**: Video upload with processing options (resolution, compression via ffmpeg)
- **Media Library**: Browse all images and videos (sorted newest-first by upload date) with one-click markdown/HTML copying
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

## Vendored / Offline Assets

The web editor and math rendering work with **no internet connection**. Their
JavaScript is bundled and shipped locally under `static/js/` and served by
Flask's built-in static route (`/static/...`), so there are no runtime CDN
calls. This avoids the failure mode where a dropped connection breaks the
editor.

- `static/js/qmd-editor.js` — a single, minified ES module bundling
  **CodeMirror 6**, `@replit/codemirror-vim` (Vim keybindings),
  `@codemirror/lang-markdown`, and the One Dark theme. All CM6 core packages
  are inlined into one file (CM6 requires a single shared copy of the core).
- `static/js/mathjax-tex-svg.js` — MathJax 3 with the **SVG output renderer**
  (chosen over CHTML because SVG needs no font files, making true offline use
  trivial). The input config (`$...$` inline, `$$...$$` display) is unchanged.

### Rebuilding the editor bundle

The committed `static/js/qmd-editor.js` is produced from the entry in
`vendor/qmd-editor.entry.js` by `vendor/build.sh` (uses `esbuild` via `npx`).
You only need to run this if you want to change the editor packages or versions:

```bash
cd quick-md/vendor
./build.sh      # requires node + npm; writes ../static/js/qmd-editor.js
```

`vendor/.build/` (node_modules) is gitignored; the generated bundle in
`static/js/` is committed so normal users never need a build step.

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
