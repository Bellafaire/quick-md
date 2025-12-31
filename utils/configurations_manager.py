import os
import yaml
from tkinter import Tk, filedialog
from datetime import datetime


class ConfigurationManager:
    def __init__(self):
        # get path to this script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.abspath(os.path.join(self.script_dir, '../../.qmd_conf'))

        self.config = self.load_config()
        self.check_config()

        # check if the config file exists, if not prompt to create one
        if not os.path.exists(self.config_path):

            # show the default yaml file and confirm the user wants to save it
            print("Default Configuration: \n", yaml.dump(self.config, default_flow_style=False))
            print("Would you like to save the above configuration file? (y/n): ", end="")

            if 'y' in input().strip().lower():
                self.save_config()
                print("Default configuration saved to", self.config_path)

            print("You can modify the configuration file directly at this path later.")

            # allow exit
            print("Would you like to exit? (y/n): ", end="")
            if 'y' in input().strip().lower():
                exit(0)

        self.sub_config_paths()

        #print(self.config)

    def get_default_config(self):
        # the paths are a little wonky for now. 
        # TODO: global paths should be imported from an environment variable or similar these are the locations 
        # where the user stores their images/videos generally on their system. 
        return {
            "local": {
                "md_path": "../../",
                "images_path": "../../images", 
                "videos_path": "../../videos", 
                "figures_path": "../../figures", 
                "files_path": "../../files", 
                "main_md": "../../main.md"
            }, 
            "global": {
                "images_dir": "~/Pictures/Screenshots/",
                "videos_dir": "~/Videos"
            },
            "Images": [],
            "Videos": [],
            "Markdown": []
        }

    def check_config(self): 
        #confirm that all config options in default are present in self.config, if not use default
        default_config = self.get_default_config()

        for field, value in default_config.items():

            # add any missing fields with default
            if field not in self.config:
                self.config[field] = value

            else:
                # Handle dictionary fields (local, global)
                if isinstance(value, dict):
                    for option, value in value.items():
                        if option not in self.config[field]:
                            self.config[field][option] = value
                # Handle list fields (Images, Videos, Markdown)
                elif isinstance(value, list):
                    if not isinstance(self.config[field], list):
                        self.config[field] = value

    def sub_config_paths(self):
        self.check_config()
        for section, options in self.config.items():
            # Only process dictionary sections (local, global) for path substitution
            if isinstance(options, dict):
                for option, path in options.items():
                    abs_path = os.path.abspath(os.path.join(self.script_dir, os.path.expanduser(path)))
                    abs_path = os.path.normpath(abs_path)
                    self.config[section][option] = abs_path

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        return self.get_default_config()

    def save_config(self):
        with open(self.config_path, 'w') as file:
            yaml.safe_dump(self.config, file)
    
    def add_image_to_config(self, relative_path):
        """Add an image path to the Images list in config"""
        if "Images" not in self.config:
            self.config["Images"] = []
        if relative_path not in self.config["Images"]:
            self.config["Images"].append(relative_path)
            self.save_config()
    
    def add_video_to_config(self, relative_path):
        """Add a video path to the Videos list in config"""
        if "Videos" not in self.config:
            self.config["Videos"] = []
        if relative_path not in self.config["Videos"]:
            self.config["Videos"].append(relative_path)
            self.save_config()
    
    def add_markdown_to_config(self, relative_path):
        """Add a markdown path to the Markdown list in config"""
        if "Markdown" not in self.config:
            self.config["Markdown"] = []
        if relative_path not in self.config["Markdown"]:
            self.config["Markdown"].append(relative_path)
            self.save_config()

    def sanitize_filename(self, name, extension="", prepend_date=True):
        """Convert a name to snake_case, optionally prepend date, and add extension"""
        sanitized = name.lower().replace(" ", "_")
        if prepend_date:
            sanitized = self.get_date_string_prepend() + "_" + sanitized
        if extension:
            sanitized += extension
        return sanitized
   
    def get_date_string_prepend(self):
        return datetime.now().strftime("%Y_%m_%d")

    def get_date_string(self):
        return datetime.now().strftime("%m/%d/%Y")


