from datetime import datetime
import os
import yaml

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




