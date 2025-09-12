import customtkinter as ctk
import json
import os
from themed_popup import ThemedPopup, ThemeManager

class FullRWIViewerPopup(ThemedPopup):
    """A popup for viewing and editing the entire rwi_instructions.txt file."""
    def __init__(self, parent, theme_manager: ThemeManager, rwi_path: str, lock_path: str):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.title("Full RWI Viewer/Editor")
        self.geometry("700x500")
        self.grab_set()

        self.rwi_path = rwi_path
        self.lock_path = lock_path
        self.is_locked = self._is_locked()

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(main_frame, wrap="word", border_width=2, border_color=self.theme_manager.get_color("secondary_border_color"))
        self.textbox.grid(row=0, column=0, sticky="nsew")

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        self.lock_switch_var = ctk.BooleanVar(value=self.is_locked)
        self.lock_switch = ctk.CTkSwitch(button_frame, text="Lock File", variable=self.lock_switch_var, command=self.toggle_lock)
        self.lock_switch.pack(side="left", padx=10)

        self.save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_file)
        self.save_button.pack(side="right", padx=5)

        close_button = ctk.CTkButton(button_frame, text="Close", command=self.destroy)
        close_button.pack(side="right", padx=5)

        self._load_file_content()
        self.update_widget_states()
        self.apply_theme()

    def _is_locked(self) -> bool:
        """Checks if the RWI file is locked."""
        if not os.path.exists(self.lock_path):
            return False
        try:
            with open(self.lock_path, 'r') as f:
                data = json.load(f)
                return data.get("locked", False)
        except (IOError, json.JSONDecodeError):
            return False

    def _set_lock(self, locked: bool):
        """Sets the lock state in the lock file."""
        try:
            with open(self.lock_path, 'w') as f:
                json.dump({"locked": locked}, f)
        except IOError as e:
            print(f"Error saving lock file: {e}")

    def _load_file_content(self):
        """Loads the content of the RWI file into the textbox."""
        try:
            with open(self.rwi_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.textbox.insert("1.0", content)
        except FileNotFoundError:
            self.textbox.insert("1.0", f"Error: File not found at {self.rwi_path}")
        except Exception as e:
            self.textbox.insert("1.0", f"Error loading file: {e}")

    def update_widget_states(self):
        """Enables or disables widgets based on the lock state."""
        if self.is_locked:
            self.textbox.configure(state="disabled")
            self.save_button.configure(state="disabled")
        else:
            self.textbox.configure(state="normal")
            self.save_button.configure(state="normal")

    def toggle_lock(self):
        """Handles the lock switch being toggled."""
        self.is_locked = self.lock_switch_var.get()
        self._set_lock(self.is_locked)
        self.update_widget_states()

    def save_file(self):
        """Saves the content of the textbox back to the RWI file."""
        if self.is_locked:
            print("Cannot save, file is locked.")
            # Optionally show a message to the user
            return

        content = self.textbox.get("1.0", "end-1c")
        try:
            with open(self.rwi_path, 'w', encoding='utf-8') as f:
                f.write(content)
            # Find the parent_app to call update_status
            if hasattr(self.parent, 'parent_app'):
                 self.parent.parent_app.update_status("Full RWI file saved.", "green")
            print("RWI file saved successfully.")
        except Exception as e:
            if hasattr(self.parent, 'parent_app'):
                 self.parent.parent_app.update_status(f"Error saving RWI file: {e}", "red")
            print(f"Error saving RWI file: {e}")
