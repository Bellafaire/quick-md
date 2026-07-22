import os
import argparse
import getpass
from utils.configurations_manager import ConfigurationManager
from utils.assets import ensure_vendored_assets

def main():
    parser = argparse.ArgumentParser(description='Quick-md Notebook Manager')
    parser.add_argument('-p', '--port', type=int, default=6580,
                        help='Port for web server (default: 6580)')
    parser.add_argument('--password-protect', action='store_true',
                        help='Enable password protection for the web server')
    parser.add_argument('--web-only', action='store_true',
                        help='Accepted for backward compatibility (the web server is always started)')
    parser.add_argument('--network', action='store_true',
                        help='Bind to all interfaces (0.0.0.0) so the notebook is reachable over the network. Default: localhost only (127.0.0.1).')
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

    from web_server import WebServer
    host = '0.0.0.0' if args.network else '127.0.0.1'
    print(f"Starting Quick-md web server on {host}:{args.port}...")
    if password:
        print("Password protection enabled")
    if not args.network:
        print("(localhost only — pass --network to expose on the network)")
    server = WebServer(configuration_manager, host=host, port=args.port, password=password)
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

if __name__ == "__main__":
    main()