from datetime import datetime
import os
from utils import image_handler
from utils import video_handler
from textual.app import App, ComposeResult
from textual.containers import Container, Center, Middle
from textual.widgets import Static, Button, Input, Label
from textual.binding import Binding
from textual.screen import Screen
from textual.events import Key

class NewPageMenu(Screen):
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
    
    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                with Container(id="input_container"):
                    yield Label("New Page")
                    yield Label("Enter page title:")
                    yield Input(placeholder="Page title", id="title_input")
                    yield Label("Output file name:", id="output_label")
                    yield Button("Create (Enter)", variant="primary", id="create_btn")
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
        if event.button.id == "create_btn":
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
            output_file_name = self.configuration_manager.sanitize_filename(title, extension=".md")
            output_label.update(f"Output file name: {output_file_name}")
        else:
            output_label.update("Output file name:")

    def create_page(self) -> None:
        title_input = self.query_one("#title_input", Input)
        title = title_input.value.strip()
        if title:
            self.new_page(title)
            self.app.pop_screen()

    def new_page(self, title):
        filename = self.configuration_manager.sanitize_filename(title, extension=".md")
        filepath = os.path.join(self.configuration_manager.config['local']['md_path'], filename)

        title_string = f"{self.configuration_manager.get_date_string()} {title}"

        # add title to markdown file
        with open(filepath, 'w') as file:
            file.write(f"# {title_string}\n\n")

        # append to main markdown file
        with open(self.configuration_manager.config['local']['main_md'], 'a') as main_file:
            main_file.write(f"- [{title_string}]({filename})\n")

        # Save markdown file to config with original title
        self.configuration_manager.add_markdown_to_config(filename, original_title=title)


