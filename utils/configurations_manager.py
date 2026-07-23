import os
import yaml
from datetime import datetime

class ConfigurationManager:
    def __init__(self):
        # get path to this script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.abspath(os.path.join(self.script_dir, '../../.qmd_conf'))

        self.config_raw = self.load_config()  # Keep original relative paths
        self.config = {}  # Will contain absolute paths
        self.check_config()

        # check if the config file exists, if not prompt to create one
        if not os.path.exists(self.config_path):

            # show the default yaml file and confirm the user wants to save it
            print("Default Configuration: \n", yaml.dump(self.config_raw, default_flow_style=False))
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
        return {
            "notebook_title": "Quick-md Notebook",
            "default_image_width": 600,
            "local": {
                "md_path": "docs/",
                "images_path": "docs/images", 
                "videos_path": "docs/videos", 
                "figures_path": "docs/figures", 
                "files_path": "docs/files", 
                "main_md": "docs/main.md"
            }, 
            "global": {
                "images_dir": "~/Pictures/Screenshots/",
                "videos_dir": "~/Videos"
            },
            "theme": {
                "base": "#f4f5f7",
                "surface": "#ffffff",
                "accent": "#3498db"
            },
            "Images": [],
            "Videos": [],
            "Drawio": [],
            "Markdown": []
        }

    def check_config(self): 
        #confirm that all config options in default are present in self.config_raw, if not use default
        default_config = self.get_default_config()

        for field, value in default_config.items():

            # add any missing fields with default
            if field not in self.config_raw:
                self.config_raw[field] = value

            else:
                # Handle dictionary fields (local, global)
                if isinstance(value, dict):
                    for option, value in value.items():
                        if option not in self.config_raw[field]:
                            self.config_raw[field][option] = value
                # Handle list fields (Images, Videos, Markdown)
                elif isinstance(value, list):
                    if not isinstance(self.config_raw[field], list):
                        self.config_raw[field] = value

    def sub_config_paths(self):
        self.check_config()
        # Start with a copy of raw config
        import copy
        self.config = copy.deepcopy(self.config_raw)
        
        # Base path for resolving relative paths (directory containing config file)
        config_dir = os.path.dirname(self.config_path)
        
        # Convert relative paths to absolute in self.config (working copy).
        # Only the local/global sections hold paths; other dict sections (e.g.
        # theme) hold scalar values that must NOT be path-resolved.
        for section in ('local', 'global'):
            options = self.config.get(section)
            if not isinstance(options, dict):
                continue
            for option, path in options.items():
                # Expand ~ and resolve relative to the config file directory
                expanded_path = os.path.expanduser(path)
                if not os.path.isabs(expanded_path):
                    abs_path = os.path.abspath(os.path.join(config_dir, expanded_path))
                else:
                    abs_path = expanded_path
                abs_path = os.path.normpath(abs_path)
                self.config[section][option] = abs_path

        main_md = self.config['local']['main_md']
        os.makedirs(os.path.dirname(main_md), exist_ok=True)
        if not os.path.exists(main_md):
            with open(main_md, 'w') as f:
                f.write(f"# {self.config.get('notebook_title', 'Notebook')}\n\n")

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        return self.get_default_config()

    def save_config(self):
        """Save config with relative paths in the local section"""
        import copy
        config_to_save = copy.deepcopy(self.config_raw)
        
        # Base path for converting to relative (directory containing config file)
        config_dir = os.path.dirname(self.config_path)
        
        # Convert absolute paths back to relative in the local section
        if 'local' in config_to_save and isinstance(config_to_save['local'], dict):
            for option, path in config_to_save['local'].items():
                if isinstance(path, str) and os.path.isabs(path):
                    # Convert to relative path from the config file location
                    rel_path = os.path.relpath(path, config_dir)
                    config_to_save['local'][option] = rel_path
        
        with open(self.config_path, 'w') as file:
            yaml.safe_dump(config_to_save, file)
    
    def reload_config(self):
        """Re-read config from disk before making any edits."""
        self.config_raw = self.load_config()
        self.sub_config_paths()

    def add_image_to_config(self, relative_path):
        """Add an image path to the Images list in config"""
        self.reload_config()
        if "Images" not in self.config_raw:
            self.config_raw["Images"] = []
        if relative_path not in self.config_raw["Images"]:
            self.config_raw["Images"].append(relative_path)
            # Also update working copy
            if "Images" not in self.config:
                self.config["Images"] = []
            self.config["Images"].append(relative_path)
            self.save_config()
    
    def add_video_to_config(self, relative_path):
        """Add a video path to the Videos list in config"""
        self.reload_config()
        if "Videos" not in self.config_raw:
            self.config_raw["Videos"] = []
        if relative_path not in self.config_raw["Videos"]:
            self.config_raw["Videos"].append(relative_path)
            # Also update working copy
            if "Videos" not in self.config:
                self.config["Videos"] = []
            self.config["Videos"].append(relative_path)
            self.save_config()
    
    def add_drawio_to_config(self, relative_path):
        """Add a drawio diagram path to the Drawio list in config"""
        self.reload_config()
        if "Drawio" not in self.config_raw:
            self.config_raw["Drawio"] = []
        if relative_path not in self.config_raw["Drawio"]:
            self.config_raw["Drawio"].append(relative_path)
            # Also update working copy
            if "Drawio" not in self.config:
                self.config["Drawio"] = []
            self.config["Drawio"].append(relative_path)
            self.save_config()

    def add_markdown_to_config(self, relative_path, original_title=None):
        """Add a markdown path to the Markdown list in config with optional original title"""
        self.reload_config()
        if "Markdown" not in self.config_raw:
            self.config_raw["Markdown"] = []
        
        # Check if this is already in the config
        for item in self.config_raw["Markdown"]:
            if isinstance(item, dict):
                if item.get("filename") == relative_path:
                    return
            elif item == relative_path:
                # Old format, don't add duplicate
                return
        
        # Add new entry with original title if provided
        if original_title:
            new_entry = {
                "filename": relative_path,
                "title": original_title
            }
            self.config_raw["Markdown"].append(new_entry)
            # Also update working copy
            if "Markdown" not in self.config:
                self.config["Markdown"] = []
            self.config["Markdown"].append(new_entry)
        else:
            self.config_raw["Markdown"].append(relative_path)
            # Also update working copy
            if "Markdown" not in self.config:
                self.config["Markdown"] = []
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


