import os


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