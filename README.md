# quick-md
A git submodule utility to create shortcuts for maintaining a markdown notebook

## Setup

### Prerequisites
- Python 3.6 or higher
- Git

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
   python main.py
   ```

### Configuration

The application will create a `.qmd_conf` file in the project directory on first run. You can customize the following paths:

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
