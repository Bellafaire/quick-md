# Quick-MD Development Guidelines

This document outlines the development principles and requirements followed during the creation of the Quick-MD web interface.

## Core Principles

### 1. Code Changes
- **Minimal modifications** - Make the smallest possible changes to achieve the goal
- **Surgical precision** - Only modify what's necessary
- **Preserve working code** - Never delete/remove/modify working files unless absolutely necessary
- **Ignore unrelated issues** - Focus only on the task at hand, not pre-existing bugs

### 2. Feature Parity
- **Use existing functions** from `utils/` directory
- **Extensibility is critical** - All features must work in the web interface
- **Shared configuration** - The web interface accesses the `ConfigurationManager`

### 3. Architecture

#### Backend (Flask)
- **Web server** is the application
- **Background thread** - Server runs as daemon thread
- **Clean shutdown** - Server stops on Ctrl+C

#### Configuration Manager
- **Central source of truth** for all paths and settings
- **`.qmd_conf` file** in parent directory manages everything
- **Dual storage** - Maintains both relative (config_raw) and absolute (config) paths
- **Automatic path resolution** - Converts relative paths to absolute at runtime
- **Relative path saving** - Stores paths relative to config file for portability
- **Lists management** - Tracks Images, Videos, and Markdown files
- **Backward compatibility** - Supports both old and new config formats
- **Notebook title** - Configurable title for web interface branding

#### Utility Functions
- **Reusable functions** in `utils/` directory:
  - `image_handler.py` - Image copying and markdown link generation
  - `video_handler.py` - Video processing with ffmpeg
  - `configurations_manager.py` - Config file management
- **Used by the web interface** - all logic lives in shared utils

### 4. User Interface Design

#### Web Interface Features
- **View pages** - Rendered markdown with images/videos/math
- **Edit pages** - Split-view editor with live preview
- **Create pages** - Date-prefixed filenames with original titles
- **Upload media** - Images and videos with processing
- **Media library** - Browse and insert media
- **Auto-save** - Every 10 seconds if content changed
- **MathJax support** - Inline `$...$` and display `$$...$$` equations
- **Vim mode** - Optional CodeMirror Vim keybindings
- **Password protection** - Optional session-based authentication
- **Custom titles** - Configurable notebook title and page titles

#### Mobile Responsiveness
- **Breakpoints**:
  - Desktop: > 968px
  - Tablet: 768px - 968px
  - Mobile: < 480px
- **Flexible layouts** - Buttons wrap gracefully
- **Touch-friendly** - Larger tap targets on mobile
- **Single column** - Editor stacks on small screens

#### Editor Features
- **CodeMirror** - Syntax highlighting, line numbers
- **Auto-expanding** - Editor grows vertically with content (no scrollbars)
- **Full-width default** - Preview hidden by default
- **Split-view option** - Toggle to show editor and preview side-by-side
- **Media picker** - Insert images/videos at cursor
- **Auto-save** - Background saving with status indicator
- **Vim mode** - Full Vim keybindings with mode indicator
- **Live preview** - Updates while typing (debounced 1s)

### 5. File Handling

#### Naming Conventions
- **Date prefixing** - `YYYY_MM_DD_title.extension`
- **Snake case** - Spaces converted to underscores
- **Automatic sanitization** - Handled by `ConfigurationManager`

#### Media Processing
- **Images** - Copied from screenshots directory
- **Videos** - Processed with ffmpeg (resolution, compression)
- **Relative paths** - Auto-detected using `os.path.relpath()` based on actual file locations
- **Config tracking** - All media added to `.qmd_conf`
- **Path migration** - Script available (`migrate_media_paths.py`) to fix old hardcoded paths

#### Markdown Generation
- **Images** - `![alt text](relative/path/filename.png)` (auto-detected path)
- **Videos** - `<video width="640" loop autoplay controls><source src="relative/path/filename.webm"></video>`

### 6. Technology Stack

#### Backend
- **Flask** - Web framework
- **Python 3** - Programming language (3.6+, tested on 3.11)
- **Threading** - Background web server
- **YAML** - Configuration file format
- **Session-based auth** - Flask sessions for password protection

#### Frontend
- **Vanilla JavaScript** - No frameworks
- **CodeMirror 5.65.2** - Code editor with Vim mode
- **MathJax 3** - Mathematical equation rendering
- **Markdown** - Content formatting

#### Processing
- **ffmpeg** - Video processing
- **python-markdown** - Server-side markdown rendering

#### Deployment
- **Docker** - Containerized deployment with proper file ownership
- **Docker Compose** - Service orchestration
- **Web-only mode** - Headless server mode for Docker/remote deployments

### 7. Development Workflow

#### Testing
- Only run existing tests
- Don't add new testing tools unless necessary
- Verify features work before and after changes

#### Dependencies
- Use ecosystem tools (`pip install`, etc.)
- Prefer tools over manual changes
- Keep requirements.txt updated

#### Code Style
- Only comment code that needs clarification
- Keep functions focused and small
- Use descriptive variable names

### 8. Key Implementation Details

#### Media Path Fixing
Problem: Markdown files use relative paths `images/file.png`
Solution: `_fix_media_paths()` converts to `/media/images/file.png` for web serving

#### Auto-Save Logic
- Tracks `lastSavedContent` to detect changes
- Only saves if content differs
- Updates status indicator with timestamp
- Runs every 10 seconds via `setInterval`

#### Vim Mode Integration
- CodeMirror editor with Vim keymap
- Mode indicator shows NORMAL/INSERT/VISUAL
- Preference saved in localStorage
- Works in both split and full-editor modes

#### CodeMirror Auto-Expansion
- `viewportMargin: Infinity` renders all lines
- No `max-height` restriction
- Hidden scrollbars via CSS
- Editor grows vertically with content

#### Command Line Arguments
- **Port configuration** - `-p` or `--port` flag (default: 6580)
- **Password protection** - `--password-protect` flag enables authentication
- **Web-only mode** - `--web-only` flag is accepted for backward compatibility (the web server is always started)
- **Password via environment** - `QUICK_MD_PASSWORD` env var for non-interactive setups
- **Examples**:
  - `python3 main.py -p 8080`
  - `python3 main.py --password-protect` (interactive prompt)
  - `export QUICK_MD_PASSWORD=secret && python3 main.py --password-protect` (Docker)
  - `python3 main.py --web-only --port 6580` (headless server)

#### Responsive Button Layout
- `.page-header` - Flex container for title and buttons
- `.button-group` - Wrapping button container
- Mobile: Full-width stacked buttons
- Desktop: Inline buttons next to title

#### Password Protection
- **Session-based authentication** - Uses Flask sessions with secure keys
- **Login page** - Standalone template with password form
- **Route decorator** - `_check_password()` protects all routes except login/logout
- **Logout support** - Conditional logout link in navigation
- **Environment variable** - `QUICK_MD_PASSWORD` for Docker/non-interactive deployments
- **Interactive prompt** - `getpass.getpass()` for native installations
- **Interactive prompt** - `getpass.getpass()` for native installations

#### Page Title Extraction
- **First H1 detection** - Extracts actual page title from markdown content
- **Browser tab titles** - Shows page title instead of filename
- **Page headers** - Displays extracted title in view/edit pages
- **Config storage** - Original titles stored alongside filenames in `.qmd_conf`
- **Backward compatible** - Old format (string filenames) still supported

#### Docker Deployment
- **Web-only mode** - The `--web-only` flag is accepted for backward compatibility
- **File ownership** - Container user matches host UID/GID via build args
- **Environment variables** - `USER_ID`, `GROUP_ID`, `PORT`, `QUICK_MD_PASSWORD`
- **Volume mounting** - Notebook directory mounted at `/notebook`
- **Working directory** - Code runs from `/notebook/quick-md` for correct path resolution
- **No tkinter** - Removed unnecessary GUI dependencies for headless operation
- **Signal handling** - Graceful shutdown with Ctrl+C

### 9. File Structure

```
quick-md/
├── main.py                 # Entry point with arg parsing (--port, --password-protect, --web-only)
├── web_server.py           # Flask server with authentication and title extraction
├── requirements.txt        # Python dependencies
├── agents.md              # Development guidelines (this file)
├── README.md              # User documentation
├── DOCKER_QUICKSTART.md   # Docker quick reference
├── Dockerfile             # Container image definition
├── docker-compose.yml     # Service configuration
├── .dockerignore          # Docker build exclusions
├── .env.example           # Environment variable template
├── migrate_media_paths.py # Script to fix old image/video paths
├── utils/
│   ├── configurations_manager.py  # Config with dual path storage
│   ├── image_handler.py          # Auto-detect relative paths
│   └── video_handler.py
└── templates/
    ├── base.html          # Base template with nav, notebook title, MathJax
    ├── login.html         # Password authentication page
    ├── index.html         # Homepage (unused - redirects to main.md)
    ├── view_page.html     # View rendered markdown (shows page title)
    ├── edit_page.html     # Editor with CodeMirror and page title
    ├── new_page.html      # Create new page with title input
    ├── images.html        # Image gallery
    ├── videos.html        # Video gallery
    ├── upload_image.html  # Image upload form
    └── upload_video.html  # Video upload with processing
```

### 10. API Endpoints

```
GET  /                           # Homepage - redirects to /page/main.md
GET  /search?q=...             # Full-text search across all markdown pages (auth protected)
GET  /login                      # Password authentication page
POST /login                      # Process login credentials
GET  /logout                     # Clear session and logout
GET  /page/<filename>            # View rendered markdown page (auth protected)
GET  /edit/<filename>            # Edit page with CodeMirror (auth protected)
POST /save/<filename>            # Save page content (auth protected)
GET  /new_page                   # New page form (auth protected)
POST /new_page                   # Create new page (auth protected)
GET  /images                     # Image gallery (auth protected)
GET  /videos                     # Video gallery (auth protected)
GET  /upload_image               # Image upload form (auth protected)
POST /upload_image               # Upload and process image (auth protected)
GET  /upload_video               # Video upload form (auth protected)
POST /upload_video               # Upload and process video (auth protected)
GET  /media/<path:filename>      # Serve media files (auth protected)
POST /api/markdown_preview       # Convert markdown to HTML (auth protected)
GET  /api/media_list             # Get lists of images and videos (auth protected)
```

**Note:** All routes except `/login` and `/logout` are protected by `_check_password` decorator when password protection is enabled.

### 11. Configuration Example

```yaml
notebook_title: "Test Notebook"
Images:
  - images/2025_12_31_example.png
  - images/2026_02_09_screenshot.png
Markdown:
  # New format with original titles (recommended)
  - filename: 2025_12_31_intro_page.md
    title: "Introduction Page"
  - filename: 2026_02_09_notes.md
    title: "My Research Notes"
  # Old format still supported (backward compatible)
  - 2026_02_10_legacy.md
Videos:
  - videos/2025_12_31_demo.webm
global:
  images_dir: /home/user/Pictures/Screenshots
  videos_dir: /home/user/Videos
local:
  # All paths stored as relative paths for portability
  figures_path: figures
  files_path: files
  images_path: assets      # Auto-detected based on actual uploads
  main_md: main.md
  md_path: .
  videos_path: assets      # Auto-detected based on actual uploads
```

**Key Changes:**
- Added `notebook_title` for web interface branding
- Markdown entries now support dict format with `filename` and `title` keys
- Local paths stored as relative paths (converted to absolute at runtime)
- Media paths auto-detected using `os.path.relpath()`

### 12. User Experience Guidelines

#### Visual Feedback
- **Success messages** - Green background, auto-dismiss
- **Error messages** - Red background, persistent
- **Auto-save indicator** - Timestamp updates, brief green flash
- **Vim mode indicator** - Color-coded by mode (green/blue/orange)

#### Progressive Enhancement
- **Optional features** - Vim mode, preview toggle, etc.
- **Persistent preferences** - localStorage for user choices
- **Graceful degradation** - Works without JavaScript for basic viewing

#### Performance
- **Debounced updates** - 1 second delay for preview
- **Auto-save throttling** - Only saves if content changed
- **Lazy loading** - Media loaded on demand

## Summary

The Quick-MD web interface was built with these principles:
1. **Web-first** - All functionality exposed through the web interface
2. **Parallel operation** - Both interfaces run simultaneously
3. **Shared codebase** - Reuse utility functions
4. **Mobile-first** - Responsive design for all devices
5. **Optional enhancements** - Vim mode, auto-save, password protection, etc.
6. **Minimal changes** - Surgical modifications only
7. **User-friendly** - Clear feedback and intuitive controls
8. **Extensible** - Easy to add new features
9. **Portable** - Relative path storage allows notebook relocation
10. **Deployable** - Docker support with proper file ownership

All features are exposed through the web interface, providing enhancements specific to the browser environment (live preview, media sidebar, etc.).

## Recent Major Changes

### Password Protection (2026-02-12)
- Added `--password-protect` command-line flag
- Session-based authentication using Flask sessions
- `_check_password` decorator protects all routes except login/logout
- `QUICK_MD_PASSWORD` environment variable for Docker/non-interactive use
- Interactive `getpass.getpass()` prompt for native installations
- Login/logout pages with proper redirects
- `--web-only` flag is accepted for backward compatibility (the web server is always started)

### Docker Support (2026-02-12)
- Complete Docker setup with Dockerfile and docker-compose.yml
- `--web-only` flag accepted for backward compatibility (web server always starts)
- Container user matches host UID/GID via build args
- Working directory at `/notebook/quick-md` for correct path resolution
- Volume mount at `/notebook` for notebook directory
- Environment variables: `USER_ID`, `GROUP_ID`, `PORT`, `QUICK_MD_PASSWORD`
- Removed tkinter dependency (not needed for headless operation)
- Documentation: README.md, DOCKER_QUICKSTART.md, .env.example

### Configurable Notebook Title (2026-02-12)
- Added `notebook_title` field to config
- Context processor makes title available to all templates
- Displayed in header, page titles, and login page
- Defaults to "Quick-md Notebook" if not set

### Page Title Storage & Display (2026-02-12)
- Markdown entries now support dict format: `{filename: "...", title: "..."}`
- Original page titles stored in config (not just filenames)
- `_extract_title_from_markdown()` finds first H1 heading
- Browser tab titles show actual page titles
- Page headers display extracted titles
- Backward compatible with old string format

### Auto-Detected Media Paths (2026-02-12)
- `os.path.relpath()` calculates relative paths dynamically
- No hardcoded "images/" or "videos/" directories
- Works with any directory structure (assets/, media/, etc.)
- Applied to `image_handler.py` and upload routes
- `migrate_media_paths.py` script fixes old config entries

### Relative Path Storage (2026-02-12)
- ConfigurationManager maintains dual storage:
  - `config_raw`: relative paths (as stored in file)
  - `config`: absolute paths (resolved at runtime)
- `sub_config_paths()` resolves relative to config file directory
- `save_config()` converts absolute back to relative
- Allows notebook to be moved without breaking references
- All `local` section paths stored as relative

### Migration & Backward Compatibility
- Old config format (string filenames) still works
- `check_config()` ensures backward compatibility
- Migration script available for media path fixes
- Automatic path resolution handles both formats
