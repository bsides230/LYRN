import json
import os
from pathlib import Path
import customtkinter as ctk
from themed_popup import ThemedPopup, ThemeManager

# --- Constants ---
SCRIPT_DIR = Path(__file__).parent
DEFAULT_LANG = "en"
HELP_CONTENT_PATH = SCRIPT_DIR / "docs" / DEFAULT_LANG / "help_content.json"

class HelpManager:
    """
    Manages loading and retrieving help content from a JSON file.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HelpManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.help_data = {}
        self.load_help_content()

    def load_help_content(self):
        """Loads the help content from the JSON file."""
        if not HELP_CONTENT_PATH.exists():
            print(f"Warning: Help content file not found at {HELP_CONTENT_PATH}")
            return
        try:
            with open(HELP_CONTENT_PATH, 'r', encoding='utf-8') as f:
                self.help_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading help content: {e}")

    def get_help(self, help_code: str) -> dict:
        """
        Retrieves a help topic by its unique code.
        The code can be a flat string like 'mw01' or a nested path like 'main_window.system_status'.
        """
        keys = help_code.split('.')
        data = self.help_data
        try:
            for key in keys:
                # This handles finding a topic by its code inside a nested structure
                if isinstance(data, dict) and key not in data:
                    found = False
                    for sub_key, sub_value in data.items():
                        if isinstance(sub_value, dict) and sub_value.get("code") == key:
                            data = sub_value
                            found = True
                            break
                    if not found:
                         data = data[key] # Fallback to direct key access
                else:
                    data = data[key]

            if isinstance(data, dict) and "title" in data and "text" in data:
                 return data
            else:
                raise KeyError
        except (KeyError, TypeError):
            print(f"Warning: Help code '{help_code}' not found. Returning default.")
            return self.get_help("generic.coming_soon")


class HelpPopup(ThemedPopup):
    """
    A simple popup to display instruction text fetched from the HelpManager.
    """
    def __init__(self, parent, theme_manager: ThemeManager, help_code: str):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.grab_set()

        help_manager = HelpManager()
        help_topic = help_manager.get_help(help_code)

        self.title(help_topic.get("title", "Help"))
        instruction_text = help_topic.get("text", "No help text available for this topic.")

        # --- Dynamic Sizing ---
        lines = instruction_text.count('\n') + 1
        width = 450
        height = 150 + (lines * 15) # Base height + per line
        height = min(max(height, 200), 600) # Clamp height
        self.geometry(f"{width}x{height}")


        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)


        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scrollable_frame.grid(row=0, column=0, sticky="nsew")


        instruction_label = ctk.CTkLabel(
            scrollable_frame,
            text=instruction_text,
            wraplength=width - 60, # Adjust wraplength based on window width
            justify="left",
            anchor="nw"
        )
        instruction_label.pack(expand=True, fill="both")

        ok_button = ctk.CTkButton(main_frame, text="OK", command=self.destroy, width=80)
        ok_button.grid(row=1, column=0, pady=(10, 0))

        self.apply_theme()
        self.focus()
