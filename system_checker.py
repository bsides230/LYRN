import os
import json
import customtkinter as ctk
from themed_popup import ThemedPopup

class MissingFilesPopup(ThemedPopup):
    def __init__(self, parent, missing_files, theme_manager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.title("Missing Essential Files")
        self.geometry("500x300")
        self.grab_set()

        label = ctk.CTkLabel(self, text="The following essential files are missing:", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(pady=10, padx=10)

        textbox = ctk.CTkTextbox(self, wrap="word", height=150, border_width=2, border_color=self.theme_manager.get_color("secondary_border_color"))
        textbox.pack(expand=True, fill="both", padx=10, pady=10)
        textbox.insert("end", "\n".join(missing_files))
        textbox.configure(state="disabled")

        info_label = ctk.CTkLabel(self, text="The application may not function correctly without these files.")
        info_label.pack(pady=5)

        ok_button = ctk.CTkButton(self, text="Acknowledge", command=self.destroy)
        ok_button.pack(pady=10)

class SystemChecker:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.essential_files = [
            "automation/scheduler_watcher.py",
            "automation/cycle_watcher.py",
            "automation/scheduler_manager.py",
            "automation_controller.py",
            "cycle_manager.py",
            "episodic_memory_manager.py",
            "delta_manager.py",
            "oss_tool_manager.py"
        ]

    def check_and_create_folders(self):
        """
        Checks for the existence of all folders defined in settings.json
        and creates them if they are missing.
        """
        if not self.settings_manager.settings or "paths" not in self.settings_manager.settings:
            print("Warning: Settings or paths not available for folder check.")
            return

        paths = self.settings_manager.settings["paths"]
        for key, path_value in paths.items():
            if not path_value:
                continue

            # Determine if the path is a directory or a file path
            if path_value.endswith('/') or path_value.endswith('\\'):
                dir_path = path_value
            elif '.' in os.path.basename(path_value): # Simple check for a file extension
                dir_path = os.path.dirname(path_value)
            else: # Assume it's a directory if no extension
                dir_path = path_value

            if dir_path and not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"Created missing directory: {dir_path}")
                except Exception as e:
                    print(f"Error creating directory {dir_path}: {e}")

    def check_essential_files(self):
        """
        Checks for the existence of essential watcher and handler files.
        Returns a list of missing files.
        """
        missing_files = []
        for file_path in self.essential_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        return missing_files

    def show_missing_files_popup(self, parent, missing_files, theme_manager):
        """
        Displays a popup window with a list of missing files.
        """
        if not missing_files:
            return

        popup = MissingFilesPopup(parent, missing_files, theme_manager)
        popup.focus()
