import os
import yaml
from tkinter import Tk, filedialog
from utils.configurations_manager import ConfigurationManager
from utils.menu import Menu

def main():
    configuration_manager = ConfigurationManager()
    menu = Menu(configuration_manager)
    menu.display_menu()

if __name__ == "__main__":
    main()


