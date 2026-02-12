# Quick-MD Development Guidelines

This document outlines the development principles and requirements followed during the creation of the Quick-MD web interface.

## Core Principles

### 1. Code Changes
- **Minimal modifications** - Make the smallest possible changes to achieve the goal
- **Surgical precision** - Only modify what's necessary
- **Preserve working code** - Never delete/remove/modify working files unless absolutely necessary
- **Ignore unrelated issues** - Focus only on the task at hand, not pre-existing bugs

### 2. Feature Parity
- **Identical functionality** between TUI and web interface
- **Use existing functions** from `utils/` directory
- **Extensibility is critical** - All features must work in both interfaces
- **Shared configuration** - Both interfaces access the same `ConfigurationManager`

### 3. Architecture

#### Backend (Flask)
- **Web server runs in parallel** with TUI
- **Background thread** - Server runs as daemon thread
- **No conflicts** - Both interfaces can run simultaneously
- **Clean shutdown** - Server stops when TUI exits

#### Configuration Manager
- **Central source of truth** for all paths and settings
- **`.qmd_conf` file** in parent directory manages everything
- **Automatic path resolution** - Handles relative and absolute paths
- **Lists management** - Tracks Images, Videos, and Markdown files

#### Utility Functions
- **Reusable functions** in `utils/` directory:
  - `image_handler.py` - Image copying and markdown link generation
  - `video_handler.py` - Video processing with ffmpeg
  - `configurations_manager.py` - Config file management
- **Shared by both interfaces** - TUI and web use same logic

### 4. User Interface Design

#### Web Interface Features
- **View pages** - Rendered markdown with images/videos/math
- **Edit pages** - Split-view editor with live preview
- **Create pages** - Date-prefixed filenames
- **Upload media** - Images and videos with processing
- **Media library** - Browse and insert media
- **Auto-save** - Every 10 seconds if content changed
- **MathJax support** - Inline `$...$` and display `$$...$$` equations
- **Vim mode** - Optional CodeMirror Vim keybindings

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
- **Relative paths** - Auto-detected based on configured directory structure
- **Config tracking** - All media added to `.qmd_conf`

#### Markdown Generation
- **Images** - `![alt text](relative/path/filename.png)` (auto-detected path)
- **Videos** - `<video width="640" loop autoplay controls><source src="relative/path/filename.webm"></video>`
- **Clipboard support** - Markdown/HTML copied to clipboard (TUI)

### 6. Technology Stack

#### Backend
- **Flask** - Web framework
- **Python 3** - Programming language
- **Threading** - Background web server
- **YAML** - Configuration file format

#### Frontend
- **Vanilla JavaScript** - No frameworks
- **CodeMirror 5.65.2** - Code editor with Vim mode
- **MathJax 3** - Mathematical equation rendering
- **Markdown** - Content formatting

#### Processing
- **ffmpeg** - Video processing
- **python-markdown** - Server-side markdown rendering

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
- Port configuration via `-p` or `--port` flag
- Default port: 6580
- Example: `python3 main.py -p 8080`

#### Responsive Button Layout
- `.page-header` - Flex container for title and buttons
- `.button-group` - Wrapping button container
- Mobile: Full-width stacked buttons
- Desktop: Inline buttons next to title

### 9. File Structure

```
quick-md/
├── main.py                 # TUI entry point (accepts --port flag)
├── web_server.py           # Flask server (runs in thread)
├── requirements.txt        # Python dependencies
├── agents.md              # Development guidelines (this file)
├── utils/
│   ├── configurations_manager.py
│   ├── image_handler.py
│   ├── video_handler.py
│   ├── menu.py            # TUI menu with web server integration
│   ├── new_page_menu.py
│   ├── new_image_menu.py
│   └── new_video_menu.py
└── templates/
    ├── base.html          # Base template with nav and MathJax
    ├── index.html         # Homepage (unused - redirects to main.md)
    ├── view_page.html     # View rendered markdown
    ├── edit_page.html     # Editor with CodeMirror and Vim mode
    ├── new_page.html      # Create new page form
    ├── images.html        # Image gallery
    ├── videos.html        # Video gallery
    ├── upload_image.html  # Image upload form
    └── upload_video.html  # Video upload with processing
```

### 10. API Endpoints

```
GET  /                           # Homepage - redirects to /page/main.md
GET  /page/<filename>            # View rendered markdown page
GET  /edit/<filename>            # Edit page with CodeMirror
POST /save/<filename>            # Save page content
GET  /new_page                   # New page form
POST /new_page                   # Create new page
GET  /images                     # Image gallery
GET  /videos                     # Video gallery
GET  /upload_image               # Image upload form
POST /upload_image               # Upload and process image
GET  /upload_video               # Video upload form
POST /upload_video               # Upload and process video
GET  /media/<path:filename>      # Serve media files
POST /api/markdown_preview       # Convert markdown to HTML
GET  /api/media_list             # Get lists of images and videos
```

### 11. Configuration Example

```yaml
Images:
  - images/2025_12_31_example.png
  - images/2026_02_09_screenshot.png
Markdown:
  - 2025_12_31_intro_page.md
  - 2026_02_09_notes.md
Videos:
  - videos/2025_12_31_demo.webm
global:
  images_dir: /home/user/Pictures/Screenshots
  videos_dir: /home/user/Videos
local:
  figures_path: /home/user/notebook/figures
  files_path: /home/user/notebook/files
  images_path: /home/user/notebook/images
  main_md: /home/user/notebook/main.md
  md_path: /home/user/notebook
  videos_path: /home/user/notebook/videos
```

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
1. **Feature parity** - Same functionality as TUI
2. **Parallel operation** - Both interfaces run simultaneously
3. **Shared codebase** - Reuse utility functions
4. **Mobile-first** - Responsive design for all devices
5. **Optional enhancements** - Vim mode, auto-save, etc.
6. **Minimal changes** - Surgical modifications only
7. **User-friendly** - Clear feedback and intuitive controls
8. **Extensible** - Easy to add new features

All features maintain consistency between the TUI and web interfaces while providing enhancements specific to each environment (keyboard shortcuts for TUI, live preview for web).
