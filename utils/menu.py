from datetime import datetime
import os
from utils import image_handler
from utils import video_handler

class Menu:
    def __init__(self, configuration_manager):
        self.configuration_manager = configuration_manager

        self.options = [
            "New Page", 
            "Add Image", 
            "Add Video",
            "Search Images",
            "Search Videos",
            "Search Markdown",
            "Exit"
        ]

    def sanitize_filename(self, name, extension="", prepend_date=True):
        """Convert a name to snake_case, optionally prepend date, and add extension"""
        sanitized = name.lower().replace(" ", "_")
        if prepend_date:
            sanitized = self.get_date_string_prepend() + "_" + sanitized
        if extension:
            sanitized += extension
        return sanitized

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_menu(self):
        while True:
            self.clear_screen()

            for idx, option in enumerate(self.options, start=1):
                print(f"{idx}. {option}")

            choice = input("Select an option: ")
            try:
                choice = int(choice)
                if choice < 1 or choice > len(self.options):
                    raise ValueError
            except ValueError:
                input("Invalid choice. Press Enter to continue...")
                continue

            choice -= 1
            
            if self.options[choice] == "New Page":
                self.new_page()
            elif self.options[choice] == "Add Image":
                self.add_image()
            elif self.options[choice] == "Add Video":
                self.add_video()
            elif self.options[choice] == "Search Images":
                self.search_images()
            elif self.options[choice] == "Search Videos":
                self.search_videos()
            elif self.options[choice] == "Search Markdown":
                self.search_markdown()
            elif self.options[choice] == "Exit":
                break

    def get_date_string_prepend(self):
        return datetime.now().strftime("%Y_%m_%d")

    def get_date_string(self):
        return datetime.now().strftime("%m/%d/%Y")

    def add_image(self):
        source_dir = self.configuration_manager.config['global']['images_dir']
        
        # Check if there's a recent image first
        recent_image = image_handler.get_most_recent_file_in_directory(source_dir)
        if not recent_image:
            input("No images found in the specified directory. Press Enter to continue...")
            return
        
        print("Found image: ", recent_image)
        new_name = input("Enter new image name (x to cancel): ")

        if new_name.lower() == 'x':
            return

        ext = os.path.splitext(recent_image)[1]
        new_filename = self.sanitize_filename(new_name, extension=ext)
        
        success, message, markdown_link = image_handler.add_image(
            config_manager=self.configuration_manager,
            filename=new_filename,
            alt_text=new_name,
            relative_images_dir="images"
        )
        
        input(f"{message}\nPress Enter to continue...")

    def new_page(self):
        title = input("Enter page title: ")
        filename = self.sanitize_filename(title, extension=".md")
        filepath = os.path.join(self.configuration_manager.config['local']['md_path'], filename)

        title_string = f"{self.get_date_string()} {title}"

        with open(filepath, 'w') as file:
            file.write(f"# {title_string}\n\n")

        with open(self.configuration_manager.config['local']['main_md'], 'a') as main_file:
            main_file.write(f"- [{title_string}]({filename})\n")

        # Save markdown file to config
        self.configuration_manager.add_markdown_to_config(filename)

        input(f"New page created at {filepath}. Press Enter to continue...")

    def add_video(self):
        source_dir = self.configuration_manager.config['global']['videos_dir']
        
        # Check if there's a recent video first
        recent_video = video_handler.get_most_recent_file_in_directory(source_dir)
        if not recent_video:
            input("No videos found in the specified directory. Press Enter to continue...")
            return
        
        print("Found video: ", recent_video)
        title = input("Enter new video name (x to cancel): ")
        if title.lower() == 'x':
            return
            
        ext = ".webm"
        new_filename = self.sanitize_filename(title, extension=ext)

        resolutions = {"1": "480p", "2": "720p", "3": "1080p"}
        compression = {"1": "low", "2": "medium", "3": "high"}

        print("Select resolution:")
        for key, value in resolutions.items():
            print(f"{key}: {value}")
        resolution_choice = input("Enter choice (1-3): ")

        print("Select compression level:")
        for key, value in compression.items():
            print(f"{key}: {value}")
        compression_choice = input("Enter choice (1-3): ")

        if (resolution_choice not in resolutions) or (compression_choice not in compression):
            input("Invalid choice. Aborting. Press Enter to continue...")
            return

        resolution = resolutions[resolution_choice]
        compression_level = compression[compression_choice]

        success, message, video_tag = video_handler.add_video(
            config_manager=self.configuration_manager,
            filename=new_filename,
            resolution=resolution,
            compression_level=compression_level,
            output_extension=ext,
            video_width="640",
            async_process=True
        )
        
        input(f"{message}\nPress Enter to continue...")
    
    def live_search(self, items, item_type="item"):
        """
        Interactive live search with highlighting
        Returns selected item or None if cancelled
        """
        import sys
        import tty
        import termios
        
        search_term = ""
        
        def highlight_match(text, search):
            """Highlight matching portion in red"""
            if not search:
                return text
            lower_text = text.lower()
            lower_search = search.lower()
            if lower_search in lower_text:
                idx = lower_text.index(lower_search)
                return (text[:idx] + 
                       f"\033[91m{text[idx:idx+len(search)]}\033[0m" + 
                       text[idx+len(search):])
            return text
        
        def display_results(search, items):
            # Clear screen and move cursor to top left
            sys.stdout.write("\033[2J\033[1;1H")
            sys.stdout.flush()
            
            # Filter and sort by relevance
            if search:
                filtered = [(item, item.lower().index(search.lower()) if search.lower() in item.lower() else 999) 
                           for item in items if search.lower() in item.lower()]
                filtered.sort(key=lambda x: x[1])
                filtered = [item[0] for item in filtered]
            else:
                filtered = items
            
            # Build output as a single string to avoid cursor issues
            output = []
            output.append(f"Search {item_type}: {search if search else '(type to search)'}")
            output.append("-" * 60)
            
            # Display top 10 matches
            if filtered:
                for idx, item in enumerate(filtered[:10], start=1):
                    highlighted = highlight_match(item, search)
                    output.append(f"{idx}. {highlighted}")
                
                if len(filtered) > 10:
                    output.append("")
                    output.append(f"... and {len(filtered) - 10} more results")
            else:
                output.append("No matches found")
            
            output.append("")
            output.append("[Type to filter | Enter to select | Esc to cancel]")
            
            sys.stdout.write("\r\n".join(output) + "\r\n")
            sys.stdout.flush()
            return filtered
        
        # Display initial results
        filtered = display_results(search_term, items)
        
        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(fd)
            
            while True:
                char = sys.stdin.read(1)
                
                # ESC key
                if char == '\x1b':
                    # Check if it's an escape sequence
                    next_char = sys.stdin.read(1)
                    if next_char == '[':
                        sys.stdin.read(1)  # consume the final character
                        continue
                    else:
                        # Plain ESC, cancel
                        return None
                
                # Enter key
                elif char == '\r' or char == '\n':
                    break
                
                # Backspace
                elif char == '\x7f':
                    if search_term:
                        search_term = search_term[:-1]
                        filtered = display_results(search_term, items)
                
                # Regular character
                elif char.isprintable():
                    search_term += char
                    filtered = display_results(search_term, items)
        
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        # Show selection prompt
        sys.stdout.write("\n")
        sys.stdout.flush()
        
        if not filtered:
            return None
        
        choice = input("Select number (or x to cancel): ")
        if choice.lower() == 'x':
            return None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(filtered):
                return filtered[idx]
        except ValueError:
            pass
        
        return None
    
    def search_images(self):
        """Search through saved images and copy markdown link to clipboard"""
        images = self.configuration_manager.config.get('Images', [])
        if not images:
            input("No images found in configuration. Press Enter to continue...")
            return
        
        selected_image = self.live_search(images, "images")
        
        if selected_image:
            # Extract filename for alt text
            alt_text = selected_image.split('/')[-1].rsplit('.', 1)[0]
            markdown_link = image_handler.create_markdown_image_link(alt_text, selected_image)
            
            if image_handler.copy_markdown_link_to_clipboard(markdown_link):
                input(f"\nMarkdown link copied to clipboard: {markdown_link}\nPress Enter to continue...")
            else:
                input(f"\nMarkdown link: {markdown_link}\nPress Enter to continue...")
    
    def search_videos(self):
        """Search through saved videos and copy HTML tag to clipboard"""
        videos = self.configuration_manager.config.get('Videos', [])
        if not videos:
            input("No videos found in configuration. Press Enter to continue...")
            return
        
        selected_video = self.live_search(videos, "videos")
        
        if selected_video:
            video_tag = video_handler.create_video_html_tag(selected_video, width="640")
            
            if video_handler.copy_video_tag_to_clipboard(video_tag):
                input(f"\nVideo tag copied to clipboard: {video_tag}\nPress Enter to continue...")
            else:
                input(f"\nVideo tag: {video_tag}\nPress Enter to continue...")
    
    def search_markdown(self):
        """Search through saved markdown files and copy link to clipboard"""
        markdown_files = self.configuration_manager.config.get('Markdown', [])
        if not markdown_files:
            input("No markdown files found in configuration. Press Enter to continue...")
            return
        
        selected_md = self.live_search(markdown_files, "markdown files")
        
        if selected_md:
            # Extract title from filename (remove date and extension)
            filename = selected_md.rsplit('.', 1)[0]
            parts = filename.split('_', 3)
            title = parts[3] if len(parts) > 3 else filename
            title = title.replace('_', ' ').title()
            
            markdown_link = f"[{title}]({selected_md})"
            
            try:
                import pyperclip
                pyperclip.copy(markdown_link)
                input(f"\nMarkdown link copied to clipboard: {markdown_link}\nPress Enter to continue...")
            except ImportError:
                input(f"\nMarkdown link: {markdown_link}\nPress Enter to continue...")

