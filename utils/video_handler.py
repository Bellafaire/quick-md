import os
import subprocess
import shlex


def create_video_html_tag(relative_path, width="640", loop=True, autoplay=True, controls=True):
    """Generate an HTML video tag for markdown"""
    loop_attr = "loop " if loop else ""
    autoplay_attr = "autoplay " if autoplay else ""
    controls_attr = "controls" if controls else ""
    
    return f'<video width="{width}" {loop_attr}{autoplay_attr}{controls_attr}><source src="{relative_path}" type="video/mp4"></video>'


def progress_file_for(dest_path):
    """Path of the per-job ffmpeg -progress log file for a destination video."""
    return os.path.join(os.path.dirname(dest_path), "." + os.path.basename(dest_path) + ".progress")


def meta_file_for(dest_path):
    """Path of the per-job metadata sidecar (stores the source duration)."""
    return os.path.join(os.path.dirname(dest_path), "." + os.path.basename(dest_path) + ".meta")


def get_video_duration(path):
    """Return the duration of a video in seconds (float) via ffprobe, or None."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            val = result.stdout.strip()
            if val and val.lower() != "n/a":
                return float(val)
    except Exception:
        pass
    return None


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
    # Extract resolution number (remove 'p' suffix)
    resolution_height = resolution[:-1] if resolution.endswith('p') else resolution
    
    # Process to a partial file *beside* the destination (same filesystem),
    # then atomically move it into place. This avoids ever serving a
    # half-written file, and lets the media sidebar detect "processing" by
    # simply checking whether the final file exists yet.
    # Keep the real output extension on the part file so ffmpeg can infer the
    # container format from the filename.
    temp_out = dest_path + ".part" + output_extension
    progress_file = progress_file_for(dest_path)
    meta_file = meta_file_for(dest_path)
    
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-nostats",
        "-progress", progress_file,
        "-i", source_path,
        "-vf", f"scale=-2:{resolution_height}",
        "-preset", compression_level,
        temp_out,
    ]
    ffmpeg_str = " ".join(shlex.quote(a) for a in ffmpeg_cmd)
    move_str = f"mv -f {shlex.quote(temp_out)} {shlex.quote(dest_path)}"
    # Always clean up the working files (raw upload, partial output, and the
    # progress / metadata sidecars), whether ffmpeg succeeded or not.
    cleanup_str = f"rm -f {shlex.quote(temp_out)} {shlex.quote(source_path)} {shlex.quote(progress_file)} {shlex.quote(meta_file)}"
    
    if async_process:
        # Detached background process: encode, then move, then clean up.
        # Each call gets its own process, so multiple uploads can encode
        # concurrently. start_new_session detaches it from the request so it
        # keeps running after the HTTP response is returned.
        shell_cmd = f"{ffmpeg_str} && {move_str}; {cleanup_str}"
        subprocess.Popen(
            shell_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return (True, f"Video processing started in the background. It will appear at {dest_path} when ready.")
    else:
        try:
            result = subprocess.run(ffmpeg_str, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(temp_out):
                subprocess.run(f"{move_str} && {cleanup_str}", shell=True)
                return (True, f"Video processed and saved to {dest_path}")
            else:
                subprocess.run(cleanup_str, shell=True)
                return (False, f"ffmpeg failed: {result.stderr.strip() or 'unknown error'}")
        except Exception as e:
            subprocess.run(cleanup_str, shell=True)
            return (False, f"Video processing failed: {str(e)}")
