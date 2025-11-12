from datetime import datetime
import random
import subprocess
import string
import os
import yaml
import pyperclip

class Menu:
    def __init__(self, configuration_manager):
        self.configuration_manager = configuration_manager

        self.options = [
            "New Page", 
            "Add Image", 
            "Add Video", 
            "Exit"
        ]

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

    def get_most_recent_file_in_directory(self, directory):
        files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        if not files:
            return None
        most_recent_file = max(files, key=os.path.getmtime)
        return most_recent_file

    def add_image(self):
        image_path = self.get_most_recent_file_in_directory(self.configuration_manager.config['global']['images_dir'])
        print("Found image: ", image_path)

        new_name = input("Enter new image name (x to cancel): ")

        if new_name.lower() == 'x':
            return

        if image_path:
            ext = os.path.splitext(image_path)[1]

            # construct new file name and destination path following the date prepend and snakecase format
            new_filename = new_name + ext
            new_filename = self.get_date_string_prepend() + "_" + new_filename.replace(" ", "_").lower()
            dest_path = os.path.join(self.configuration_manager.config['local']['images_path'], new_filename)

            # make images directory if it doesn't exist
            os.makedirs(self.configuration_manager.config['local']['images_path'], exist_ok=True)

            # copy image to destination
            with open(image_path, 'rb') as src_file:
                with open(dest_path, 'wb') as dest_file:
                    dest_file.write(src_file.read())

            input(f"Image copied to {dest_path}")

            # create image markdown link and add to clipboard
            # this lets the user just paste it into whatever markdown file they're writing
            markdown_link = f"![{new_name}](images/{new_filename})"
            try:
                pyperclip.copy(markdown_link)
                input("Markdown image link copied to clipboard. Press Enter to continue...")
            except ImportError:
                input(f"pyperclip not installed. Here is the markdown link:\n{markdown_link}\nPress Enter to continue...")
        else:
            input("No images found in the specified directory. Press Enter to continue...")

    def new_page(self):
        title = input("Enter page title: ")
        filename = self.get_date_string_prepend() + "_" + title.lower().replace(" ", "_") + ".md"
        filepath = os.path.join(self.configuration_manager.config['local']['md_path'], filename)

        title_string = f"{self.get_date_string()} {title}"

        with open(filepath, 'w') as file:
            file.write(f"# {title_string}\n\n")

        with open(self.configuration_manager.config['local']['main_md'], 'a') as main_file:
            main_file.write(f"- [{title_string}]({filename})\n")

        input(f"New page created at {filepath}. Press Enter to continue...")

    def add_video(self):
        # Get the most recent video from the global videos directory
        video_path = self.get_most_recent_file_in_directory(self.configuration_manager.config['global']['videos_dir'])
        print("Found video: ", video_path)
        title = input("Enter new video name (x to cancel): ")
        if title.lower() == 'x':
            return
            
        ext = ".webm" # webm for smaller file sizes  
        dest_folder = self.configuration_manager.config['local']['videos_path']

        # make videos directory if it doesn't exist
        os.makedirs(dest_folder, exist_ok=True)

        new_name = self.get_date_string_prepend() + "_" + title.lower().replace(" ", "_") + ext
        new_name = os.path.join(dest_folder, new_name)

        if video_path:
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
                print("Invalid choice. Aborting.")
                return

            resolution = resolutions[resolution_choice]
            compression_level = compression[compression_choice]

            # Define output path in /tmp/
            random_string = ''.join(random.choices(string.ascii_letters, k=20))
            temp_path = f"/tmp/{random_string}{ext}" # one day someone will file a bug report because of a 1 in 52^20 chance of collision

            # Build ffmpeg command
            ffmpeg_cmd = [
                "ffmpeg", "-i", "\"%s\"" % video_path,
                "-vf", f"scale=-2:{resolution[:-1]}",
                "-preset", compression_level,
                temp_path
            ]

            # Run ffmpeg in the background and copy result to the global videos directory
            subprocess.Popen(
                f"{' '.join(ffmpeg_cmd)} && cp {temp_path} {new_name}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Copy video tag to clipboard
            relative_path = os.path.relpath(f'{new_name}', start=self.configuration_manager.config['local']['md_path'])
         
            video_tag = f'<video width="640" loop autoplay controls><source src="{relative_path}" type="video/mp4"></video>'
            pyperclip.copy(video_tag)

