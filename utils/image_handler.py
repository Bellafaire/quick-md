import os
import pyperclip


def get_most_recent_file_in_directory(directory):
    """Get the most recently modified file in a directory"""
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        return None
    most_recent_file = max(files, key=os.path.getmtime)
    return most_recent_file


def copy_image_to_destination(source_path, dest_path, create_dirs=True):
    """Copy an image file from source to destination"""
    if create_dirs:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    with open(source_path, 'rb') as src_file:
        with open(dest_path, 'wb') as dest_file:
            dest_file.write(src_file.read())


def create_markdown_image_link(alt_text, relative_path):
    """Generate a markdown image link"""
    return f"![{alt_text}]({relative_path})"


def copy_markdown_link_to_clipboard(markdown_link):
    """Copy markdown link to system clipboard"""
    try:
        pyperclip.copy(markdown_link)
        return True
    except ImportError:
        return False


def add_image(config_manager, filename, alt_text, relative_images_dir="images"):
    """
    Add an image from source directory to destination directory and generate markdown link
    
    Parameters:
    - config_manager: ConfigurationManager instance
    - filename: Name for the destination file (including extension)
    - alt_text: Alt text for the markdown image
    - relative_images_dir: Relative path prefix for markdown link (e.g., "images")
    
    Returns:
    - tuple: (success, message, markdown_link)
    """
    source_directory = config_manager.config['global']['images_dir']
    dest_directory = config_manager.config['local']['images_path']
    
    # Find most recent image
    source_path = get_most_recent_file_in_directory(source_directory)
    if not source_path:
        return (False, "No images found in the specified directory", None)
    
    # Copy image
    dest_path = os.path.join(dest_directory, filename)
    try:
        copy_image_to_destination(source_path, dest_path)
    except Exception as e:
        return (False, f"Failed to copy image: {str(e)}", None)
    
    # Create markdown link and relative path
    relative_path = f"{relative_images_dir}/{filename}"
    markdown_link = create_markdown_image_link(alt_text, relative_path)
    
    # Save to config
    config_manager.add_image_to_config(relative_path)
    
    # Copy to clipboard
    clipboard_success = copy_markdown_link_to_clipboard(markdown_link)
    
    if clipboard_success:
        message = f"Image copied to {dest_path}. Markdown link copied to clipboard."
    else:
        message = f"Image copied to {dest_path}. Markdown link: {markdown_link}"
    
    return (True, message, markdown_link)
