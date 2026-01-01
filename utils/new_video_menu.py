from datetime import datetime
import os
import asyncio
import subprocess
from utils import video_handler
from textual.app import App, ComposeResult
from textual.containers import Container, Center, Middle, Vertical, Horizontal
from textual.widgets import Static, Button, Input, Label, Checkbox, RadioButton, RadioSet, ProgressBar
from textual.binding import Binding
from textual.screen import Screen
from textual.events import Key
from textual.worker import Worker, WorkerState

class NewVideoMenu(Screen):
    CSS = """
    Screen {
        background: $surface;
    }
    
    #input_container {
        width: 80;
        height: auto;
        background: $panel;
        border: solid $primary;
        padding: 1;
    }
    
    Label {
        margin-bottom: 0;
    }
    
    Input {
        margin-bottom: 0;
    }
    
    Button {
        width: 100%;
        margin-top: 0;
    }
    
    .section-title {
        text-style: bold;
        margin-top: 0;
        margin-bottom: 0;
    }
    
    RadioSet {
        background: $boost;
        padding: 0 1;
        margin-bottom: 0;
        height: auto;
    }
    
    RadioButton {
        margin: 0;
        height: auto;
    }
    
    Checkbox {
        margin: 0;
        height: auto;
    }
    
    ProgressBar {
        margin-top: 0;
        margin-bottom: 0;
    }
    
    #status_label {
        text-align: center;
        color: green;
        height: 1;
    }
    
    Vertical {
        height: auto;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, menu_instance, configuration_manager):
        super().__init__()
        self.menu_instance = menu_instance
        self.configuration_manager = configuration_manager
        self.recent_video = self.get_most_recent_video()
        self.is_processing = False
    
    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                with Container(id="input_container"):
                    yield Label("Convert Video", classes="section-title")
                    
                    # Input file info
                    recent_video_name = os.path.basename(self.recent_video) if self.recent_video else "No recent video found"
                    yield Label(f'Input: {recent_video_name}', id="input_file")
                    
                    # Output filename input
                    yield Label("Output name:")
                    yield Input(placeholder="video_name", id="title_input")
                    yield Label("Output file: ", id="output_label")
                    
                    # Resolution options
                    yield Label("Resolution:", classes="section-title")
                    with RadioSet(id="resolution_set"):
                        yield RadioButton("480p", value=True, id="res_480")
                        yield RadioButton("720p (HD)", id="res_720")
                        yield RadioButton("1080p (Full HD)", id="res_1080")
                        yield RadioButton("Original", id="res_original")
                    
                    # Quality/Compression options
                    yield Label("Compression Quality:", classes="section-title")
                    with RadioSet(id="quality_set"):
                        yield RadioButton("Fast (Lower Quality)", id="quality_fast")
                        yield RadioButton("Medium", value=True, id="quality_medium")
                        yield RadioButton("Slow (Higher Quality)", id="quality_slow")
                    
                    # Output format options
                    yield Label("Options:", classes="section-title")
                    with Vertical():
                        yield Checkbox("Convert to WebM", value=True, id="webm_checkbox")
                        yield Checkbox("Loop video", value=True, id="loop_checkbox")
                        yield Checkbox("Autoplay", value=True, id="autoplay_checkbox")
                        yield Checkbox("Show controls", value=True, id="controls_checkbox")
                    
                    # Progress bar (hidden initially)
                    yield ProgressBar(total=100, show_eta=False, id="progress_bar")
                    yield Label("", id="status_label")
                    
                    # Action buttons
                    yield Button("Convert Video", variant="primary", id="convert_btn")
                    yield Button("Cancel (Esc)", id="cancel_btn")
    
    def on_mount(self) -> None:
        """Focus the input and hide progress bar when the screen is mounted."""
        self.query_one("#title_input", Input).focus()
        self.query_one("#progress_bar", ProgressBar).display = False
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key pressed in the input field."""
        if not self.is_processing:
            self.start_conversion()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input value changes to update the filename preview."""
        self.update_output_filename()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "convert_btn" and not self.is_processing:
            self.start_conversion()
        elif event.button.id == "cancel_btn":
            self.app.pop_screen()
    
    def action_cancel(self) -> None:
        if not self.is_processing:
            self.app.pop_screen()
        else:
            # Allow user to force exit even during processing
            self.app.pop_screen()
    
    def on_key(self, event: Key) -> None:
        """Handle all keyboard input."""
        pass
    
    def update_output_filename(self) -> None:
        """Update the output filename label based on current input."""
        output_label = self.query_one("#output_label", Label)
        title_input = self.query_one("#title_input", Input)
        title = title_input.value.strip()
        
        # Get selected format
        webm_checkbox = self.query_one("#webm_checkbox", Checkbox)
        ext = ".webm" if webm_checkbox.value else os.path.splitext(self.recent_video)[1]
        
        if title:
            output_file_name = self.configuration_manager.sanitize_filename(title, extension=ext)
            output_label.update(f"Output file: {output_file_name}")
        else:
            output_label.update("Output file: ")
    
    def get_selected_resolution(self) -> str:
        """Get the selected resolution option."""
        resolution_set = self.query_one("#resolution_set", RadioSet)
        selected = resolution_set.pressed_button
        
        if selected.id == "res_480":
            return "480"
        elif selected.id == "res_720":
            return "720"
        elif selected.id == "res_1080":
            return "1080"
        else:
            return "original"
    
    def get_selected_quality(self) -> str:
        """Get the selected quality/compression preset."""
        quality_set = self.query_one("#quality_set", RadioSet)
        selected = quality_set.pressed_button
        
        if selected.id == "quality_fast":
            return "ultrafast"
        elif selected.id == "quality_medium":
            return "medium"
        else:
            return "slow"
    
    def start_conversion(self) -> None:
        """Start the video conversion process."""
        title_input = self.query_one("#title_input", Input)
        title = title_input.value.strip()
        
        if not title:
            self.update_status("Please enter an output name", error=True)
            return
        
        if not self.recent_video:
            self.update_status("No input video found", error=True)
            return
        
        # Disable UI elements
        self.is_processing = True
        self.query_one("#convert_btn", Button).disabled = True
        self.query_one("#title_input", Input).disabled = True
        
        # Show progress bar
        progress_bar = self.query_one("#progress_bar", ProgressBar)
        progress_bar.display = True
        progress_bar.update(progress=0)
        
        # Start the worker
        self.run_worker(self.convert_video_worker(), exclusive=True)
    
    async def convert_video_worker(self) -> dict:
        """Worker that performs the video conversion."""
        title_input = self.query_one("#title_input", Input)
        title = title_input.value.strip()
        
        # Get options
        webm_checkbox = self.query_one("#webm_checkbox", Checkbox)
        ext = ".webm" if webm_checkbox.value else os.path.splitext(self.recent_video)[1]
        resolution = self.get_selected_resolution()
        quality = self.get_selected_quality()
        
        # Build output filename
        output_filename = self.configuration_manager.sanitize_filename(title, extension=ext)
        dest_directory = self.configuration_manager.config['local']['videos_path']
        dest_path = os.path.join(dest_directory, output_filename)
        
        # Ensure destination directory exists
        os.makedirs(dest_directory, exist_ok=True)
        
        # Update status (direct call since we're in async context)
        self.update_status(f"Converting video to {resolution}p with {quality} quality...")
        
        # Run ffmpeg conversion with progress tracking
        success = await self.run_ffmpeg_with_progress(
            self.recent_video, dest_path, resolution, quality
        )
        
        if success:
            # Create HTML video tag
            loop_val = self.query_one("#loop_checkbox", Checkbox).value
            autoplay_val = self.query_one("#autoplay_checkbox", Checkbox).value
            controls_val = self.query_one("#controls_checkbox", Checkbox).value
            
            md_path = self.configuration_manager.config['local']['md_path']
            relative_path = os.path.relpath(dest_path, start=md_path)
            video_tag = video_handler.create_video_html_tag(
                relative_path, width="640", loop=loop_val, 
                autoplay=autoplay_val, controls=controls_val
            )
            
            # Save to config
            self.configuration_manager.add_video_to_config(relative_path)
            
            # Copy to clipboard
            video_handler.copy_video_tag_to_clipboard(video_tag)
            
            return {"success": True, "message": f"Video converted successfully! Tag copied to clipboard."}
        else:
            return {"success": False, "message": "Video conversion failed"}
    
    async def run_ffmpeg_with_progress(self, source_path, dest_path, resolution, quality) -> bool:
        """Run ffmpeg and update progress bar."""
        try:
            # Get video duration first
            duration_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", source_path
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            total_duration = float(duration_result.stdout.strip())
            
            # Build ffmpeg command
            scale_filter = f"scale=-2:{resolution}" if resolution != "original" else ""
            
            cmd = ["ffmpeg", "-i", source_path, "-progress", "pipe:1"]
            if scale_filter:
                cmd.extend(["-vf", scale_filter])
            cmd.extend(["-preset", quality, "-y", dest_path])
            
            # Run ffmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                line = line.decode().strip()
                if line.startswith("out_time_ms="):
                    # Extract current time in microseconds
                    time_ms = int(line.split("=")[1])
                    time_seconds = time_ms / 1000000.0
                    
                    # Calculate progress percentage
                    progress = min(int((time_seconds / total_duration) * 100), 99)
                    self.update_progress(progress)
            
            await process.wait()
            
            # Set to 100% when done
            self.update_progress(100)
            
            return process.returncode == 0
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", error=True)
            return False
    
    def update_progress(self, value: int) -> None:
        """Update the progress bar value."""
        progress_bar = self.query_one("#progress_bar", ProgressBar)
        progress_bar.update(progress=value)
    
    def update_status(self, message: str, error: bool = False) -> None:
        """Update the status label."""
        status_label = self.query_one("#status_label", Label)
        if error:
            status_label.styles.color = "red"
        else:
            status_label.styles.color = "green"
        status_label.update(message)
    
    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes."""
        if event.state == WorkerState.SUCCESS:
            result = event.worker.result
            self.update_status(result["message"], error=not result["success"])
            
            # Re-enable UI
            self.is_processing = False
            self.query_one("#convert_btn", Button).disabled = False
            self.query_one("#title_input", Input).disabled = False
            
            if result["success"]:
                # Close the screen after a short delay
                self.set_timer(2.0, self.app.pop_screen)
        elif event.state == WorkerState.ERROR:
            self.update_status("Conversion failed", error=True)
            self.is_processing = False
            self.query_one("#convert_btn", Button).disabled = False
            self.query_one("#title_input", Input).disabled = False
        elif event.state == WorkerState.CANCELLED:
            self.update_status("Conversion cancelled", error=True)
            self.is_processing = False
            self.query_one("#convert_btn", Button).disabled = False
            self.query_one("#title_input", Input).disabled = False

    def get_most_recent_video(self) -> str:
        source_dir = self.configuration_manager.config['global']['videos_dir']
        recent_video = video_handler.get_most_recent_file_in_directory(source_dir)
        return recent_video if recent_video else ""

