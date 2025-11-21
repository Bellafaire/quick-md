import os
import subprocess
import random
import string
import pyperclip


def get_most_recent_file_in_directory(directory):
    """Get the most recently modified file in a directory"""
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        return None
    most_recent_file = max(files, key=os.path.getmtime)
    return most_recent_file


def create_video_html_tag(relative_path, width="640", loop=True, autoplay=True, controls=True):
    """Generate an HTML video tag for markdown"""
    loop_attr = "loop " if loop else ""
    autoplay_attr = "autoplay " if autoplay else ""
    controls_attr = "controls" if controls else ""
    
    return f'<video width="{width}" {loop_attr}{autoplay_attr}{controls_attr}><source src="{relative_path}" type="video/mp4"></video>'


def copy_video_tag_to_clipboard(video_tag):
    """Copy video HTML tag to system clipboard"""
    try:
        pyperclip.copy(video_tag)
        return True
    except ImportError:
        return False


def process_video_with_ffmpeg(source_path, dest_path, resolution, compression_level, output_extension=".webm", async_process=True):
    """
    Process a video file with ffmpeg
    
    Parameters:
    - source_path: Path to the source video
    - dest_path: Path where the processed video should be saved
    - resolution: Target resolution (e.g., "480p", "720p", "1080p")
    - compression_level: Compression preset (e.g., "low", "medium", "high")
    - output_extension: Extension for output file
    - async_process: If True, run ffmpeg in background
    
    Returns:
    - tuple: (success, message)
    """
    # Generate temp file path
    random_string = ''.join(random.choices(string.ascii_letters, k=20))
    temp_path = f"/tmp/{random_string}{output_extension}"
    
    # Extract resolution number (remove 'p' suffix)
    resolution_height = resolution[:-1] if resolution.endswith('p') else resolution
    
    # Build ffmpeg command
    ffmpeg_cmd = [
        "ffmpeg", "-i", f'"{source_path}"',
        "-vf", f"scale=-2:{resolution_height}",
        "-preset", compression_level,
        temp_path
    ]
    
    if async_process:
        # Run ffmpeg in background and copy result
        subprocess.Popen(
            f"{' '.join(ffmpeg_cmd)} && cp {temp_path} {dest_path}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return (True, f"Video processing started in background. Output will be saved to {dest_path}")
    else:
        try:
            # Run ffmpeg synchronously
            result = subprocess.run(
                ' '.join(ffmpeg_cmd),
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Copy to destination
                subprocess.run(f"cp {temp_path} {dest_path}", shell=True, check=True)
                return (True, f"Video processed and saved to {dest_path}")
            else:
                return (False, f"ffmpeg failed: {result.stderr}")
        except Exception as e:
            return (False, f"Video processing failed: {str(e)}")


def add_video(config_manager, filename, resolution, compression_level, 
              output_extension=".webm", video_width="640", async_process=True):
    """
    Add a video from source directory, process it, and generate HTML tag
    
    Parameters:
    - config_manager: ConfigurationManager instance
    - filename: Name for the destination file (including extension)
    - resolution: Target resolution (e.g., "480p", "720p", "1080p")
    - compression_level: ffmpeg compression preset (e.g., "low", "medium", "high")
    - output_extension: Extension for output file (default: ".webm")
    - video_width: Width attribute for HTML video tag
    - async_process: If True, run ffmpeg in background
    
    Returns:
    - tuple: (success, message, video_tag)
    """
    source_directory = config_manager.config['global']['videos_dir']
    dest_directory = config_manager.config['local']['videos_path']
    md_path = config_manager.config['local']['md_path']
    
    # Find most recent video
    source_path = get_most_recent_file_in_directory(source_directory)
    if not source_path:
        return (False, "No videos found in the specified directory", None)
    
    # Ensure destination directory exists
    os.makedirs(dest_directory, exist_ok=True)
    
    # Full destination path
    dest_path = os.path.join(dest_directory, filename)
    
    # Process video with ffmpeg
    success, process_msg = process_video_with_ffmpeg(
        source_path, dest_path, resolution, compression_level, 
        output_extension, async_process
    )
    
    if not success:
        return (False, process_msg, None)
    
    # Create HTML video tag
    relative_path = os.path.relpath(dest_path, start=md_path)
    video_tag = create_video_html_tag(relative_path, width=video_width)
    
    # Save to config
    config_manager.add_video_to_config(relative_path)
    
    # Copy to clipboard
    clipboard_success = copy_video_tag_to_clipboard(video_tag)
    
    if clipboard_success:
        message = f"{process_msg} Video tag copied to clipboard."
    else:
        message = f"{process_msg} Video tag: {video_tag}"
    
    return (True, message, video_tag)
