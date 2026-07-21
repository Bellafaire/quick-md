import os
import yaml
import argparse
import getpass
from utils.configurations_manager import ConfigurationManager
from utils.assets import ensure_vendored_assets
from utils.menu import Menu

def main():
    parser = argparse.ArgumentParser(description='Quick-md Notebook Manager')
    parser.add_argument('-p', '--port', type=int, default=6580, 
                        help='Port for web server (default: 6580)')
    parser.add_argument('--password-protect', action='store_true',
                        help='Enable password protection for the web server')
    parser.add_argument('--web-only', action='store_true',
                        help='Run web server only (no TUI) - useful for Docker')
    args = parser.parse_args()
    
    password = None
    if args.password_protect:
        # Try to get password from environment variable first (for Docker)
        password = os.environ.get('QUICK_MD_PASSWORD')
        if not password:
            # Fall back to interactive prompt (for non-Docker use)
            password = getpass.getpass("Enter password for web server: ")
        if not password:
            print("Error: Password cannot be empty")
            print("Tip: Set QUICK_MD_PASSWORD environment variable or enter password when prompted")
            return
    
    configuration_manager = ConfigurationManager()
    
    # Make sure the offline web assets (CodeMirror 6 editor + MathJax) are
    # present and up to date. No-op when the committed bundles are already in
    # place; rebuilds/downloads only if missing or stale.
    ensure_vendored_assets()
    
    if args.web_only:
        # Web-only mode: Start server and keep running
        from web_server import WebServer
        print(f"Starting Quick-md web server on port {args.port}...")
        if password:
            print("Password protection enabled")
        server = WebServer(configuration_manager, port=args.port, password=password)
        server.start()
        print(f"Web server running at {server.get_address()}")
        print("Press Ctrl+C to stop")
        try:
            # Keep the main thread alive
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down web server...")
    else:
        # Normal mode: Start TUI with web server in background
        menu = Menu(configuration_manager, port=args.port, password=password)
        menu.display_menu()

if __name__ == "__main__":
    main()


