# quick-md
A git submodule utility to create shortcuts for maintaining a markdown notebook

## Features

- **TUI (Terminal User Interface)**: Fast keyboard-driven interface using Textual
- **Web Interface**: Browser-based interface for editing and viewing markdown files
- **Dual Access**: Both interfaces run in parallel - use whichever you prefer!
- **MathJax Support**: Write mathematical equations using `$` for inline math and `$$` for display equations
- Create and manage markdown pages with automatic date prefixing
- Add images from screenshots directory with automatic copying and markdown link generation
- Add videos with automatic ffmpeg processing and compression
- View and edit markdown with live preview (web interface)
- Copy markdown links and HTML tags to clipboard

## Setup

### Prerequisites
- Python 3.6 or higher
- Git
- ffmpeg (for video processing)

### Installation

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

The TUI will launch and the web server will start automatically. The web server address will be displayed in the bottom right of the TUI (default: http://0.0.0.0:5000).

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

Access the web interface at http://localhost:5000 in your browser.

Features:
- **View Pages**: Browse all markdown files with rendered preview (supports MathJax)
- **Edit Pages**: Edit markdown with live preview panel (MathJax renders in real-time)
- **Create Pages**: Web form to create new pages
- **Upload Images**: Drag-and-drop image upload with instant markdown link
- **Upload Videos**: Video upload with processing options (resolution, compression)
- **Media Library**: Browse all images and videos with one-click markdown/HTML copying
- **Math Support**: Write equations using `$...$` for inline and `$$...$$` for display equations

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

The application will create a `.qmd_conf` file in the parent directory on first run. You can customize the following paths:

- **local**: Paths relative to the quick-md directory
  - `md_path`: Directory for markdown files
  - `images_path`: Directory for images
  - `videos_path`: Directory for videos
  - `figures_path`: Directory for figures
  - `files_path`: Directory for other files
  - `main_md`: Path to main markdown index file

- **global**: System-wide paths
  - `images_dir`: Default directory to find screenshots (e.g., `~/Pictures/Screenshots/`)
  - `videos_dir`: Default directory to find videos (e.g., `~/Videos`)

## Architecture

The application uses a shared `ConfigurationManager` that both the TUI and web interface access. This ensures feature parity between both interfaces:

- Both use the same underlying functions from `utils/` directory
- Changes made in one interface are immediately visible in the other
- The web server runs in a background thread, allowing both interfaces to run simultaneously

## Requirements

- PyYAML>=6.0
- pyperclip>=1.8.2
- textual>=0.47.0
- Flask>=3.0.0
- markdown>=3.5.0
