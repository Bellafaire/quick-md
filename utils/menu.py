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
            async_process=False
        )
        
        input(f"{message}\nPress Enter to continue...")

