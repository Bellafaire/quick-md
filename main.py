import os
import yaml
from tkinter import Tk, filedialog
from utils.configurations_manager import ConfigurationManager

def main():
    configuration_manager = ConfigurationManager()

    print(configuration_manager.config)


if __name__ == "__main__":
    main()


