from datetime import datetime
import os
from utils import image_handler
from textual.app import App, ComposeResult
from textual.containers import Container, Center, Middle
from textual.widgets import Static, Button, Input, Label
from textual.binding import Binding
from textual.screen import Screen
from textual.events import Key

class NewImageMenu(Screen):
    CSS = """
    Screen {
        background: $surface;
    }
    
    #input_container {
        width: 60;
        height: auto;
        background: $panel;
        border: solid $primary;
        padding: 1;
    }
    
    Label {
        margin-bottom: 1;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    Button {
        width: 100%;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "create", "Create Page")
    ]
    
    def __init__(self, menu_instance, configuration_manager):
        super().__init__()
        self.menu_instance = menu_instance
        self.configuration_manager = configuration_manager
        self.recent_image = self.get_most_recent_image()
    
    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                with Container(id="input_container"):
                    yield Label("New Page")
                    yield Label("Enter new image name:")
                    yield Input(placeholder="New Image Name", id="title_input")
                    recent_image_name = os.path.basename(self.recent_image) if self.recent_image else "No recent image found"
                    yield Label(f'Input File: {recent_image_name}', id="input_file")
                    yield Label("Output file name:", id="output_label")
                    yield Button("Copy (Enter)", variant="primary", id="copy_btn")
                    yield Button("Cancel (Esc)", id="cancel_btn")
    
    def on_mount(self) -> None:
        """Focus the input when the screen is mounted."""
        self.query_one("#title_input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key pressed in the input field."""
        self.create_page()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input value changes to update the filename preview."""
        self.update_output_filename()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy_btn":
            self.create_page()
        elif event.button.id == "cancel_btn":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        self.app.pop_screen()
    
    def action_create(self) -> None:
        """Action triggered by Enter key binding when input is not focused."""
        self.create_page()
    
    def on_key(self, event: Key) -> None:
        """Handle all keyboard input in the New Page screen."""
        # Log the key press for debugging
    
    def update_output_filename(self) -> None:
        """Update the output filename label based on current input."""
        output_label = self.query_one("#output_label", Label)
        title_input = self.query_one("#title_input", Input)
        title = title_input.value.strip()
        if title:
            ext = os.path.splitext(self.recent_image)[1]
            output_file_name = self.configuration_manager.sanitize_filename(title, extension=ext)
            output_label.update(f"Output file name: {output_file_name}")
        else:
            output_label.update("Output file name:")

    def create_page(self) -> None:
        title_input = self.query_one("#title_input", Input)
        title = title_input.value.strip()
        if title:
            self.add_image()
            self.app.pop_screen()

    def get_most_recent_image(self) -> str:
        source_dir = self.configuration_manager.config['global']['images_dir']
        
        # Check if there's a recent image first
        recent_image = image_handler.get_most_recent_file_in_directory(source_dir)
        if not recent_image:
            return ""

        return recent_image

    def add_image(self):
        #new_name = input("Enter new image name (x to cancel): ")
        #if new_name.lower() == 'x':
        #    return

        ext = os.path.splitext(self.recent_image)[1]
        title_input = self.query_one("#title_input", Input).value.strip()
        new_filename = self.configuration_manager.sanitize_filename(title_input, extension=ext)
        
        success, message, markdown_link = image_handler.add_image(
            config_manager=self.configuration_manager,
            filename=new_filename,
            alt_text=title_input,
            relative_images_dir="images"
        )
        


