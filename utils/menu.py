from datetime import datetime
import os
from utils import image_handler
from textual.app import App, ComposeResult
from textual.containers import Container, Center, Middle
from textual.widgets import Static, Button, Input, Label
from textual.binding import Binding
from textual.screen import Screen
from textual.events import Key

from utils.new_page_menu import NewPageMenu
from utils.new_image_menu import NewImageMenu
from utils.new_video_menu import NewVideoMenu

class Menu:
    def __init__(self, configuration_manager, port=6580, password=None):
        self.configuration_manager = configuration_manager
        self.port = port
        self.password = password

        self.options = [
            "New Page", 
            "Add Image", 
            "Add Video",
            #"Search Images",
            #"Search Videos",
            #"Search Markdown",
            "Exit"
        ]
    
    def display_menu(self):
        app = MenuApp(self.configuration_manager, self, self.port, self.password)
        app.run()


class MenuApp(App):
    CSS = """
    Screen {
        background: $surface;
    }
    
    #header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #menu_container {
        width: 50;
        height: auto;
    }
    
    #web_server_status {
        dock: bottom;
        height: 1;
        text-align: right;
        color: $success;
        text-style: italic;
        padding-right: 2;
    }
    
    Button {
        width: 100%;
        margin: 0;
    }
    
    Button:focus {
        background: $panel;
    }
    
    Button:hover {
        background: $accent;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "select(0)", "Option 1"),
        Binding("2", "select(1)", "Option 2"),
        Binding("3", "select(2)", "Option 3"),
        Binding("4", "select(3)", "Option 4"),
        Binding("5", "select(4)", "Option 5"),
        Binding("6", "select(5)", "Option 6"),
        Binding("7", "select(6)", "Option 7"),
    ]
    
    def __init__(self, configuration_manager, menu_instance, port=6580, password=None):
        super().__init__()
        self.configuration_manager = configuration_manager
        self.menu_instance = menu_instance
        self.options = menu_instance.options
        self.port = port
        self.password = password
        self.web_server = None
    
    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                yield Static("Quick-md", id="header")
                with Container(id="menu_container"):
                    yield Static("Select an option:", id="title")
                    for idx, option in enumerate(self.options, start=1):
                        button = Button(f"{idx}. {option}", id=f"btn_{idx}")
                        button.can_focus = False
                        yield button
        yield Static("", id="web_server_status")
    
    def on_mount(self) -> None:
        """Start web server when app mounts"""
        try:
            from web_server import WebServer
            self.web_server = WebServer(self.configuration_manager, port=self.port, password=self.password)
            self.web_server.start()
            address = self.web_server.get_address()
            status = f"Web server: {address}"
            if self.password:
                status += " (password protected)"
            self.query_one("#web_server_status", Static).update(status)
        except Exception as e:
            self.query_one("#web_server_status", Static).update(f"Web server: Error starting")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Only handle buttons from the main menu (they start with "btn_")
        if not event.button.id or not event.button.id.startswith("btn_"):
            return
        
        button_label = str(event.button.label)
        option = button_label.split(". ", 1)[1]
        self.handle_option(option)
    
    def action_select(self, index: int) -> None:
        if 0 <= index < len(self.options):
            option = self.options[index]
            self.handle_option(option)
    
    def handle_option(self, option: str) -> None:
        if option == "Exit":
            self.exit()
        elif option == "New Page":
            self.push_screen(NewPageMenu(self.menu_instance, self.configuration_manager))
        elif option == "Add Image":
            self.push_screen(NewImageMenu(self.menu_instance, self.configuration_manager))
        elif option == "Add Video":
            self.push_screen(NewVideoMenu(self.menu_instance, self.configuration_manager))
        elif option == "Search Images":
            # TODO: Implement search images
            pass
        elif option == "Search Videos":
            # TODO: Implement search videos
            pass
        elif option == "Search Markdown":
            # TODO: Implement search markdown
            pass

    
    #def clear_screen(self):
    #    os.system('cls' if os.name == 'nt' else 'clear')

    #def display_menu(self):
    #    while True:
    #        self.clear_screen()

    #        for idx, option in enumerate(self.options, start=1):
    #            print(f"{idx}. {option}")

    #        choice = input("Select an option: ")
    #        try:
    #            choice = int(choice)
    #            if choice < 1 or choice > len(self.options):
    #                raise ValueError
    #        except ValueError:
    #            input("Invalid choice. Press Enter to continue...")
    #            continue

    #        choice -= 1
    #        
    #        if self.options[choice] == "New Page":
    #            self.new_page()
    #        elif self.options[choice] == "Add Image":
    #            self.add_image()
    #        elif self.options[choice] == "Add Video":
    #            self.add_video()
    #        elif self.options[choice] == "Search Images":
    #            self.search_images()
    #        elif self.options[choice] == "Search Videos":
    #            self.search_videos()
    #        elif self.options[choice] == "Search Markdown":
    #            self.search_markdown()
    #        elif self.options[choice] == "Exit":
    #            break

    #def get_date_string_prepend(self):
    #    return datetime.now().strftime("%Y_%m_%d")

    #def get_date_string(self):
    #    return datetime.now().strftime("%m/%d/%Y")



    #def add_video(self):
    #    source_dir = self.configuration_manager.config['global']['videos_dir']
    #    
    #    # Check if there's a recent video first
    #    recent_video = video_handler.get_most_recent_file_in_directory(source_dir)
    #    if not recent_video:
    #        input("No videos found in the specified directory. Press Enter to continue...")
    #        return
    #    
    #    print("Found video: ", recent_video)
    #    title = input("Enter new video name (x to cancel): ")
    #    if title.lower() == 'x':
    #        return
    #        
    #    ext = ".webm"
    #    new_filename = self.sanitize_filename(title, extension=ext)

    #    resolutions = {"1": "480p", "2": "720p", "3": "1080p"}
    #    compression = {"1": "low", "2": "medium", "3": "high"}

    #    print("Select resolution:")
    #    for key, value in resolutions.items():
    #        print(f"{key}: {value}")
    #    resolution_choice = input("Enter choice (1-3): ")

    #    print("Select compression level:")
    #    for key, value in compression.items():
    #        print(f"{key}: {value}")
    #    compression_choice = input("Enter choice (1-3): ")

    #    if (resolution_choice not in resolutions) or (compression_choice not in compression):
    #        input("Invalid choice. Aborting. Press Enter to continue...")
    #        return

    #    resolution = resolutions[resolution_choice]
    #    compression_level = compression[compression_choice]

    #    success, message, video_tag = video_handler.add_video(
    #        config_manager=self.configuration_manager,
    #        filename=new_filename,
    #        resolution=resolution,
    #        compression_level=compression_level,
    #        output_extension=ext,
    #        video_width="640",
    #        async_process=True
    #    )
    #    
    #    input(f"{message}\nPress Enter to continue...")
    #
    #def live_search(self, items, item_type="item"):
    #    """
    #    Interactive live search with highlighting
    #    Returns selected item or None if cancelled
    #    """
    #    import sys
    #    import tty
    #    import termios
    #    
    #    search_term = ""
    #    
    #    def highlight_match(text, search):
    #        """Highlight matching portion in red"""
    #        if not search:
    #            return text
    #        lower_text = text.lower()
    #        lower_search = search.lower()
    #        if lower_search in lower_text:
    #            idx = lower_text.index(lower_search)
    #            return (text[:idx] + 
    #                   f"\033[91m{text[idx:idx+len(search)]}\033[0m" + 
    #                   text[idx+len(search):])
    #        return text
    #    
    #    def display_results(search, items):
    #        # Clear screen and move cursor to top left
    #        sys.stdout.write("\033[2J\033[1;1H")
    #        sys.stdout.flush()
    #        
    #        # Filter and sort by relevance
    #        if search:
    #            filtered = [(item, item.lower().index(search.lower()) if search.lower() in item.lower() else 999) 
    #                       for item in items if search.lower() in item.lower()]
    #            filtered.sort(key=lambda x: x[1])
    #            filtered = [item[0] for item in filtered]
    #        else:
    #            filtered = items
    #        
    #        # Build output as a single string to avoid cursor issues
    #        output = []
    #        output.append(f"Search {item_type}: {search if search else '(type to search)'}")
    #        output.append("-" * 60)
    #        
    #        # Display top 10 matches
    #        if filtered:
    #            for idx, item in enumerate(filtered[:10], start=1):
    #                highlighted = highlight_match(item, search)
    #                output.append(f"{idx}. {highlighted}")
    #            
    #            if len(filtered) > 10:
    #                output.append("")
    #                output.append(f"... and {len(filtered) - 10} more results")
    #        else:
    #            output.append("No matches found")
    #        
    #        output.append("")
    #        output.append("[Type to filter | Enter to select | Esc to cancel]")
    #        
    #        sys.stdout.write("\r\n".join(output) + "\r\n")
    #        sys.stdout.flush()
    #        return filtered
    #    
    #    # Display initial results
    #    filtered = display_results(search_term, items)
    #    
    #    # Save terminal settings
    #    fd = sys.stdin.fileno()
    #    old_settings = termios.tcgetattr(fd)
    #    
    #    try:
    #        tty.setraw(fd)
    #        
    #        while True:
    #            char = sys.stdin.read(1)
    #            
    #            # ESC key
    #            if char == '\x1b':
    #                # Check if it's an escape sequence
    #                next_char = sys.stdin.read(1)
    #                if next_char == '[':
    #                    sys.stdin.read(1)  # consume the final character
    #                    continue
    #                else:
    #                    # Plain ESC, cancel
    #                    return None
    #            
    #            # Enter key
    #            elif char == '\r' or char == '\n':
    #                break
    #            
    #            # Backspace
    #            elif char == '\x7f':
    #                if search_term:
    #                    search_term = search_term[:-1]
    #                    filtered = display_results(search_term, items)
    #            
    #            # Regular character
    #            elif char.isprintable():
    #                search_term += char
    #                filtered = display_results(search_term, items)
    #    
    #    finally:
    #        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    #    
    #    # Show selection prompt
    #    sys.stdout.write("\n")
    #    sys.stdout.flush()
    #    
    #    if not filtered:
    #        return None
    #    
    #    choice = input("Select number (or x to cancel): ")
    #    if choice.lower() == 'x':
    #        return None
    #    
    #    try:
    #        idx = int(choice) - 1
    #        if 0 <= idx < len(filtered):
    #            return filtered[idx]
    #    except ValueError:
    #        pass
    #    
    #    return None
    #
    #def search_images(self):
    #    """Search through saved images and copy markdown link to clipboard"""
    #    images = self.configuration_manager.config.get('Images', [])
    #    if not images:
    #        input("No images found in configuration. Press Enter to continue...")
    #        return
    #    
    #    selected_image = self.live_search(images, "images")
    #    
    #    if selected_image:
    #        # Extract filename for alt text
    #        alt_text = selected_image.split('/')[-1].rsplit('.', 1)[0]
    #        markdown_link = image_handler.create_markdown_image_link(alt_text, selected_image)
    #        
    #        if image_handler.copy_markdown_link_to_clipboard(markdown_link):
    #            input(f"\nMarkdown link copied to clipboard: {markdown_link}\nPress Enter to continue...")
    #        else:
    #            input(f"\nMarkdown link: {markdown_link}\nPress Enter to continue...")
    #
    #def search_videos(self):
    #    """Search through saved videos and copy HTML tag to clipboard"""
    #    videos = self.configuration_manager.config.get('Videos', [])
    #    if not videos:
    #        input("No videos found in configuration. Press Enter to continue...")
    #        return
    #    
    #    selected_video = self.live_search(videos, "videos")
    #    
    #    if selected_video:
    #        video_tag = video_handler.create_video_html_tag(selected_video, width="640")
    #        
    #        if video_handler.copy_video_tag_to_clipboard(video_tag):
    #            input(f"\nVideo tag copied to clipboard: {video_tag}\nPress Enter to continue...")
    #        else:
    #            input(f"\nVideo tag: {video_tag}\nPress Enter to continue...")
    #
    #def search_markdown(self):
    #    """Search through saved markdown files and copy link to clipboard"""
    #    markdown_files = self.configuration_manager.config.get('Markdown', [])
    #    if not markdown_files:
    #        input("No markdown files found in configuration. Press Enter to continue...")
    #        return
    #    
    #    selected_md = self.live_search(markdown_files, "markdown files")
    #    
    #    if selected_md:
    #        # Extract title from filename (remove date and extension)
    #        filename = selected_md.rsplit('.', 1)[0]
    #        parts = filename.split('_', 3)
    #        title = parts[3] if len(parts) > 3 else filename
    #        title = title.replace('_', ' ').title()
    #        
    #        markdown_link = f"[{title}]({selected_md})"
    #        
    #        try:
    #            import pyperclip
    #            pyperclip.copy(markdown_link)
    #            input(f"\nMarkdown link copied to clipboard: {markdown_link}\nPress Enter to continue...")
    #        except ImportError:
    #            input(f"\nMarkdown link: {markdown_link}\nPress Enter to continue...")

