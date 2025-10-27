from datetime import datetime
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




