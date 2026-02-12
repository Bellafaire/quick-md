import os
import yaml
import argparse
import getpass
from tkinter import Tk, filedialog
from utils.configurations_manager import ConfigurationManager
from utils.menu import Menu

def main():
    parser = argparse.ArgumentParser(description='Quick-md Notebook Manager')
    parser.add_argument('-p', '--port', type=int, default=6580, 
                        help='Port for web server (default: 6580)')
    parser.add_argument('--password-protect', action='store_true',
                        help='Enable password protection for the web server')
    args = parser.parse_args()
    
    password = None
    if args.password_protect:
        password = getpass.getpass("Enter password for web server: ")
        if not password:
            print("Error: Password cannot be empty")
            return
    
    configuration_manager = ConfigurationManager()
    menu = Menu(configuration_manager, port=args.port, password=password)
    menu.display_menu()

if __name__ == "__main__":
    main()


