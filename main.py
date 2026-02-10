import os
import yaml
import argparse
from tkinter import Tk, filedialog
from utils.configurations_manager import ConfigurationManager
from utils.menu import Menu

def main():
    parser = argparse.ArgumentParser(description='Quick-md Notebook Manager')
    parser.add_argument('-p', '--port', type=int, default=6580, 
                        help='Port for web server (default: 6580)')
    args = parser.parse_args()
    
    configuration_manager = ConfigurationManager()
    menu = Menu(configuration_manager, port=args.port)
    menu.display_menu()

if __name__ == "__main__":
    main()


