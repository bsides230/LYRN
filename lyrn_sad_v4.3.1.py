"""
LYRN-AI Interface

"""

import os
import sys
import json
import subprocess
import re
import time
import queue
import threading
import io
import contextlib
import gc
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import shutil
from tkinter import colorchooser, filedialog
import tkinter as tk
from delta_manager import DeltaManager
from automation_controller import AutomationController, Job
from color_picker import CustomColorPickerPopup
from file_lock import SimpleFileLock
from oss_tool_manager import OSSToolManager, OSSTool
from themed_popup import ThemedPopup, ThemeManager
from automation.scheduler_manager import SchedulerManager
import calendar
from cycle_manager import CycleManager
from episodic_memory_manager import EpisodicMemoryManager
from system_checker import SystemChecker
from full_rwi_viewer_popup import FullRWIViewerPopup
from chat_manager import ChatManager
from help_manager import HelpManager, HelpPopup

# CustomTkinter imports
import customtkinter as ctk
from llama_cpp import Llama
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None
    print("Warning: Pillow library not found. Image features will be disabled.")


# System monitoring imports
import psutil
try:
    import pynvml
except ImportError:
    pynvml = None

# Set initial appearance
ctk.set_appearance_mode("dark")

# Script directory and settings path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(SCRIPT_DIR, "settings.json")
THEME_PATH = os.path.join(SCRIPT_DIR, "lyrn-theme.json")

# LYRN-AI Brand Colors
LYRN_PURPLE = "#7552bf"
LYRN_ACCENT = "#A855F7"
LYRN_SUCCESS = "#10B981"
LYRN_WARNING = "#F59E0B"
LYRN_ERROR = "#EF4444"
LYRN_INFO = "#3B82F6"

class Tooltip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text, delay=1000):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def schedule_tooltip(self, event=None):
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def show_tooltip(self):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(self.tooltip_window, text=self.text, corner_radius=5, fg_color="#333333", text_color="white", padx=10, pady=5)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None



class ThemedInputDialog(ThemedPopup):
    """A themed version of CTkInputDialog."""
    def __init__(self, parent, theme_manager: ThemeManager, text: str, title: str):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.title(title)
        self.geometry("300x150")
        self.grab_set()

        self._user_input = None

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(main_frame, text=text, wraplength=260).pack(pady=(0, 10))
        self.entry = ctk.CTkEntry(main_frame)
        self.entry.pack(fill="x")
        self.entry.focus()

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(15, 0))
        ok_button = ctk.CTkButton(button_frame, text="OK", command=self._ok_event)
        ok_button.pack(side="left", padx=5)
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self._cancel_event)
        cancel_button.pack(side="right", padx=5)

        self.entry.bind("<Return>", self._ok_event)
        self.bind("<Escape>", self._cancel_event)

        self.apply_theme()
        self.wait_window()

    def _ok_event(self, event=None):
        self._user_input = self.entry.get()
        self.grab_release()
        self.destroy()

    def _cancel_event(self, event=None):
        self._user_input = None
        self.grab_release()
        self.destroy()

    def get_input(self):
        return self._user_input

class InstructionPopup(ThemedPopup):
    """A simple popup to display instruction text."""
    def __init__(self, parent, theme_manager: ThemeManager, title: str, instruction: str):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.title(title)
        self.geometry("400x200")
        self.grab_set()

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        instruction_label = ctk.CTkLabel(
            main_frame,
            text=instruction,
            wraplength=360,
            justify="left"
        )
        instruction_label.pack(expand=True)

        ok_button = ctk.CTkButton(main_frame, text="OK", command=self.destroy)
        ok_button.pack(pady=(10, 0))

        self.apply_theme()


class FileViewerPopup(ThemedPopup):
    """A popup to display file content, with an optional refresh button."""
    def __init__(self, parent, theme_manager: ThemeManager, title: str, content_source: Path or str, config: dict, is_content_str: bool = False):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.title(title)
        self.geometry("600x500")
        # self.grab_set() # Removed to allow interaction with the parent window

        self.content_source = content_source
        self.config = config
        self.is_content_str = is_content_str
        self.parent_app = parent.parent_app # To call parent methods like update_status

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(main_frame, wrap="word", border_width=2, border_color=self.theme_manager.get_color("secondary_border_color"))
        self.textbox.grid(row=0, column=0, sticky="nsew")

        self.refresh_content() # Load initial content

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, pady=(10, 0))

        if not self.is_content_str:
            refresh_button = ctk.CTkButton(button_frame, text="Refresh", command=self.refresh_content)
            refresh_button.pack(side="left", padx=(0, 10))

        ok_button = ctk.CTkButton(button_frame, text="Close", command=self.destroy)
        ok_button.pack(side="left")

        self.apply_theme()

    def refresh_content(self):
        """Loads or reloads the content into the textbox."""
        try:
            if self.is_content_str:
                content = self.content_source
            else:
                path = Path(self.content_source)
                if path.exists():
                    content = path.read_text(encoding='utf-8')
                else:
                    content = "[File not found or not specified]"

            begin_bracket = self.config.get("begin_bracket", "")
            end_bracket = self.config.get("end_bracket", "")
            full_content = f"{begin_bracket}\n{content}\n{end_bracket}"

            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", full_content)
            self.textbox.configure(state="disabled")
            if not self.is_content_str:
                 self.parent_app.update_status(f"Refreshed: {os.path.basename(self.content_source)}", LYRN_INFO)


        except Exception as e:
            error_message = f"Error refreshing content: {e}"
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", error_message)
            self.textbox.configure(state="disabled")


class DraggableListbox(ctk.CTkScrollableFrame):
    """A scrollable frame that supports reordering of items via buttons."""
    def __init__(self, master, command=None, rwi_instructions=None, theme_manager=None, rwi_save_callback=None, parent_popup=None, toggle_command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.parent_popup = parent_popup
        self.toggle_command = toggle_command
        self.rwi_instructions = rwi_instructions or {}
        self.theme_manager = theme_manager
        self.rwi_save_callback = rwi_save_callback
        self.items = []
        self.item_map = {}
        self.selected_item = None

    def get_selected_item(self):
        """Returns the currently selected item's frame."""
        return self.selected_item

    def add_item(self, item_data: dict, **kwargs):
        """Adds a new item to the list."""
        text = item_data["path"]
        is_pinned = item_data.get("pinned", False)
        is_active = item_data.get("active", True)

        item_frame = ctk.CTkFrame(self, corner_radius=3)
        if is_pinned:
            # A light purple to indicate pinned status, works in light/dark themes
            item_frame.configure(fg_color=("#E8D5F9", "#402354"))
        item_frame.pack(fill="x", padx=5, pady=3)

        # Pin button
        pin_char = "📌" if is_pinned else "📍"
        pin_button = ctk.CTkButton(item_frame, text=pin_char, width=30,
                                   command=lambda frame=item_frame: self.toggle_pin(frame))
        pin_button.pack(side="left", padx=5, pady=5)

        # Toggle switch
        toggle_var = ctk.BooleanVar(value=is_active)
        toggle_switch = ctk.CTkSwitch(item_frame, text="", variable=toggle_var,
                                      command=lambda: self.toggle_command(item_data["path"], toggle_var.get()))
        toggle_switch.pack(side="left", padx=5, pady=5)


        label = ctk.CTkLabel(item_frame, text=text, anchor="w", **kwargs)
        label.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        for widget in [item_frame, label]:
            widget.bind("<ButtonPress-1>", lambda e, frame=item_frame: self._on_press(e, frame))

        self.items.append(item_frame)
        self.item_map[item_frame] = item_data

    def toggle_pin(self, item_frame):
        """Toggles the pinned state of an item and re-sorts the list."""
        item_data = self.item_map[item_frame]
        item_data["pinned"] = not item_data.get("pinned", False)

        # Re-sort all items based on pinned status, then by their original order (for stability)
        self.items.sort(key=lambda frame: not self.item_map[frame].get("pinned", False))

        # Repack all items in the new order
        for item in self.items:
            item.pack_forget()
        for item in self.items:
            item.pack(fill="x", padx=5, pady=3)
            # Update visual state
            is_pinned = self.item_map[item].get("pinned", False)
            pin_char = "📌" if is_pinned else "📍"
            item.winfo_children()[0].configure(text=pin_char) # Assumes pin button is the first child
            if is_pinned:
                item.configure(fg_color=("#E8D5F9", "#402354"))
            else:
                item.configure(fg_color="transparent")


        # Trigger the command to save the new state
        if self.command:
            self.command(self.get_item_objects())

    def clear(self):
        """Removes all items from the list."""
        for item in self.items:
            item.destroy()
        self.items.clear()
        self.item_map.clear()

    def get_item_objects(self) -> List[dict]:
        """Returns the list of item data objects in their current order."""
        return [self.item_map[item] for item in self.items]

    def _on_press(self, event, widget):
        """Callback for when a mouse button is pressed on an item. Handles SELECTION only."""
        # Find the actual frame to select from the widget that was clicked
        if isinstance(widget, (ctk.CTkLabel, ctk.CTkButton)):
            frame_to_select = widget.master
        else:
            frame_to_select = widget

        # Update selection
        self.selected_item = frame_to_select

        # Visual feedback for selection
        for item in self.items:
            is_pinned = self.item_map[item].get("pinned", False)
            if item == self.selected_item:
                item.configure(fg_color=LYRN_PURPLE) # Highlight color for selection
            elif is_pinned:
                item.configure(fg_color=("#E8D5F9", "#402354")) # Pinned color
            else:
                item.configure(fg_color="transparent") # Default color

        # Call parent to populate the editor panel
        component_name = self.item_map[self.selected_item]["path"]
        if self.parent_popup and hasattr(self.parent_popup, 'populate_editor_panel'):
            self.parent_popup.populate_editor_panel(component_name)

    def move_item_up(self):
        """Moves the selected item up in the list."""
        if not self.selected_item:
            return

        index = self.items.index(self.selected_item)
        if index == 0:
            return

        # Prevent unpinned item from moving into the pinned section
        num_pinned = sum(1 for item in self.items if self.item_map[item].get("pinned", False))
        is_selected_pinned = self.item_map[self.selected_item].get("pinned", False)
        if not is_selected_pinned and index == num_pinned:
            return # At the boundary, cannot move up

        # Swap items
        self.items.insert(index - 1, self.items.pop(index))

        # Repack all items
        for item in self.items:
            item.pack_forget()
        for item in self.items:
            item.pack(fill="x", padx=5, pady=3)

        # Save the new order
        if self.command:
            self.command(self.get_item_objects())

    def move_item_down(self):
        """Moves the selected item down in the list."""
        if not self.selected_item:
            return

        index = self.items.index(self.selected_item)
        if index >= len(self.items) - 1:
            return

        # Prevent pinned item from moving into the unpinned section
        num_pinned = sum(1 for item in self.items if self.item_map[item].get("pinned", False))
        is_selected_pinned = self.item_map[self.selected_item].get("pinned", False)
        if is_selected_pinned and index == num_pinned - 1:
            return # At the boundary, cannot move down

        # Swap items
        self.items.insert(index + 1, self.items.pop(index))

        # Repack all items
        for item in self.items:
            item.pack_forget()
        for item in self.items:
            item.pack(fill="x", padx=5, pady=3)

        # Save the new order
        if self.command:
            self.command(self.get_item_objects())


class LanguageManager:
    """Manages loading and retrieving translated UI strings."""
    def __init__(self, language="en"):
        self.language_dir = os.path.join(SCRIPT_DIR, "languages")
        self.language = language
        self.strings = {}
        self.load_language()

    def load_language(self, language: str = None):
        """Loads a language file from the 'languages' directory."""
        if language:
            self.language = language

        lang_file_path = os.path.join(self.language_dir, f"{self.language}.json")

        if not os.path.exists(lang_file_path):
            print(f"Warning: Language file not found for '{self.language}'. Falling back to returning keys.")
            self.strings = {}
            return

        try:
            with open(lang_file_path, 'r', encoding='utf-8') as f:
                self.strings = json.load(f)
            print(f"Loaded language: {self.language}")
        except Exception as e:
            print(f"Error loading language file {lang_file_path}: {e}")
            self.strings = {}

    def get_available_languages(self) -> List[str]:
        """Scans the languages directory for available language files."""
        if not os.path.exists(self.language_dir):
            return ["en"]  # Fallback

        try:
            languages = [f.split('.')[0] for f in os.listdir(self.language_dir) if f.endswith(".json")]
            return sorted(languages) if languages else ["en"]
        except Exception as e:
            print(f"Error scanning for languages: {e}")
            return ["en"]

    def get(self, key: str, **kwargs) -> str:
        """Gets a translated string by key, with optional formatting."""
        string = self.strings.get(key, key) # Return key if not found for easy debugging
        if kwargs:
            try:
                string = string.format(**kwargs)
            except KeyError as e:
                print(f"Warning: Missing format key {e} in language string for key '{key}'")
        return string

class SettingsManager:
    """Enhanced settings manager with UI preferences"""

    def __init__(self):
        self.settings = None
        self.first_boot = False
        self.ui_settings = {
            "font_size": 12,
            "window_size": "1400x900",
            "confirmation_preferences": {},
            "save_chat_history": True,
            "chat_history_length": 10,
            "show_thinking_text": True,
            "chat_colors": {
                "user_text": "#00C0A0",
                "assistant_text": "#FFFFFF",
                "thinking_text": "#FFD700",
                "system_text": "#B0B0B0"
            }
        }
        self.load_or_detect_first_boot()

    def get_setting(self, key: str, default: any = None) -> any:
        """Gets a setting from the UI settings."""
        return self.ui_settings.get(key, default)

    def set_setting(self, key: str, value: any):
        """Sets a setting in the UI settings and saves it."""
        self.ui_settings[key] = value
        self.save_settings()

    def load_or_detect_first_boot(self):
        """Load settings or create a default one on first boot."""
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = data.get('settings', {})
                    self.ui_settings.update(data.get('ui_settings', {}))

                # Resolve relative paths for the current session
                if "paths" in self.settings:
                    for key, path in self.settings["paths"].items():
                        if path and not os.path.isabs(path):
                            self.settings["paths"][key] = os.path.join(SCRIPT_DIR, path)

                print("Settings loaded successfully")
                self.ensure_automation_flag()
                self.ensure_next_job_flag()
                self.ensure_llm_status_flag()
            except Exception as e:
                print(f"Error loading settings: {e}. Assuming first boot.")
                self.first_boot = True
        else:
            print("No settings.json found - First boot detected. Creating default settings.")
            self.first_boot = True

        if self.first_boot:
            # Create and save a default settings file
            self.settings = self.create_empty_settings_structure()
            default_paths = {
                "static_snapshots": "build_prompt/static_snapshots",
                "dynamic_snapshots": "build_prompt/dynamic_snapshots",
                "active_jobs": "build_prompt/active_jobs",
                "deltas": "deltas",
                "chat": "chat",
                "output": "output",
                "keywords": "active_keywords",
                "topics": "active_topics",
                "active_chunk": "active_chunk",
                "chunk_queue": "automation/chunk_queue.json",
                "job_list": "automation/job_list.txt",
                "job_log": "automation/job_log.json",
                "automation_flag_path": "global_flags/automation.txt",
                "chunk_queue_path": "automation/chunk_queue.json",
                "chat_dir": "chat",
                "chat_parsed_dir": "chat_parsed",
                "audit_dir": "automation/job_audit",
                "metrics_logs": "metrics_logs"
            }
            self.settings["paths"] = default_paths
            self.save_settings() # This saves the file with relative paths

            # Now resolve paths for the current session
            for key, path in self.settings["paths"].items():
                if path and not os.path.isabs(path):
                    self.settings["paths"][key] = os.path.join(SCRIPT_DIR, path)

            self.ensure_automation_flag()
            self.ensure_next_job_flag()
            self.ensure_llm_status_flag()

    def create_empty_settings_structure(self) -> dict:
        """Create empty settings structure for first boot"""
        return {
            "active": {
                "model_path": "",
                "n_ctx": 8192,
                "n_threads": 8,
                "n_gpu_layers": 0,
                "max_tokens": 2048,
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "stream": True
            },
            "paths": {
                "static_snapshots": "",
                "dynamic_snapshots": "",
                "active_jobs": "",
                "deltas": "",
                "chat": "",
                "output": "",
                "keywords": "",
                "topics": "",
                "active_chunk": "",
                "chunk_queue": "",
                "job_list": "",
                "job_log": "",
                "automation_flag_path": "",
                "chunk_queue_path": "",
                "chat_dir": "",
                "chat_parsed_dir": "",
                "audit_dir": "",
                "metrics_logs": ""
            }
        }

    def save_settings(self, settings: dict = None):
        """Save settings and UI preferences to JSON file"""
        try:
            if os.path.exists(SETTINGS_PATH):
                backup_path = SETTINGS_PATH + '.bk'
                shutil.copy2(SETTINGS_PATH, backup_path)

            data = {
                "settings": settings or self.settings,
                "ui_settings": self.ui_settings
            }

            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            if settings:
                self.settings = settings
            self.first_boot = False
            print("Settings saved successfully")

        except Exception as e:
            print(f"Error saving settings: {e}")

    def ensure_automation_flag(self):
        """Ensure automation flag is set to 'off' on startup"""
        if not self.settings or "paths" not in self.settings:
            return

        flag_path = self.settings["paths"].get("automation_flag_path", "")
        if not flag_path:
            return

        os.makedirs(os.path.dirname(flag_path), exist_ok=True)
        try:
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write("off")
        except Exception as e:
            print(f"Warning: Could not set automation flag: {e}")

    def ensure_next_job_flag(self):
        """Ensure next job flag is initialized to 'false' on startup"""
        next_job_path = os.path.join(SCRIPT_DIR, "global_flags", "next_job.txt")
        os.makedirs(os.path.dirname(next_job_path), exist_ok=True)

        try:
            with open(next_job_path, 'w', encoding='utf-8') as f:
                f.write("false")
            print("Next job flag initialized to 'false'")
        except Exception as e:
            print(f"Warning: Could not initialize next job flag: {e}")

    def ensure_llm_status_flag(self):
        """Ensure LLM status flag is initialized to 'idle' on startup."""
        llm_status_path = os.path.join(SCRIPT_DIR, "global_flags", "llm_status.txt")
        os.makedirs(os.path.dirname(llm_status_path), exist_ok=True)
        try:
            with open(llm_status_path, 'w', encoding='utf-8') as f:
                f.write("idle")
            print("LLM status flag initialized to 'idle'")
        except Exception as e:
            print(f"Warning: Could not initialize LLM status flag: {e}")

    def set_automation_flag(self, state: str):
        """Set automation flag to 'on' or 'off'"""
        if not self.settings or "paths" not in self.settings:
            return

        flag_path = self.settings["paths"].get("automation_flag_path", "")
        if not flag_path:
            return

        try:
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write(state)
        except Exception as e:
            print(f"Error setting automation flag: {e}")

class SnapshotLoader:
    """Loads the static base prompt from the 'build_prompt' directory."""

    def __init__(self, parent_app, settings_manager: SettingsManager, automation_controller: AutomationController):
        self.parent_app = parent_app
        self.settings_manager = settings_manager
        self.automation_controller = automation_controller
        self.build_prompt_dir = os.path.join(SCRIPT_DIR, "build_prompt")
        self.master_prompt_path = os.path.join(self.build_prompt_dir, "master_prompt.txt")
        self.config_path = os.path.join(self.build_prompt_dir, "builder_config.json")
        self.prompt_order_path = os.path.join(self.build_prompt_dir, "prompt_order.json")

    def _load_json_file(self, path: str) -> Optional[list or dict]:
        """Safely loads a JSON file and returns its content."""
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading JSON file {path}: {e}")
            return None

    def _load_text_file(self, path: str) -> str:
        """Safely loads a text file and returns its content."""
        if not os.path.exists(path):
            print(f"Warning: Text file not found at {path}")
            return ""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except IOError as e:
            print(f"Error reading text file {path}: {e}")
            return ""

    def build_master_prompt_from_components(self) -> str:
        """Builds the master prompt by concatenating enabled components based on their new config files."""
        config = self._load_json_file(self.config_path)
        if config and config.get("master_prompt_locked", False):
            print("Master prompt is locked. Loading directly from file.")
            return self._load_text_file(self.master_prompt_path)

        print("Building master prompt from components...")

        prompt_parts = []

        components_path = os.path.join(self.build_prompt_dir, "components.json")
        components = self._load_json_file(components_path) or []

        # Filter for active components and sort by order
        active_components = sorted([c for c in components if c.get('active', True)], key=lambda x: x.get('order', 0))

        # --- Build the Static RWI block first ---
        rwi_config_path = os.path.join(self.build_prompt_dir, "rwi_config.json")
        rwi_config = self._load_json_file(rwi_config_path) or {}
        rwi_start_bracket = rwi_config.get("begin_bracket", "###RWI_INSTRUCTIONS_START###")
        rwi_end_bracket = rwi_config.get("end_bracket", "###RWI_INSTRUCTIONS_END###")

        rwi_parts = []
        rwi_intro = self._load_text_file(os.path.join(self.build_prompt_dir, "rwi_intro.txt"))

        for component in active_components:
            component_name = component['name']
            if component_name == "RWI": continue # Skip the RWI meta-component itself

            config_path = os.path.join(self.build_prompt_dir, component_name, "config.json")

            config = self._load_json_file(config_path)
            if config and "rwi_text" in config and config["rwi_text"]:
                rwi_parts.append(config["rwi_text"])

        if rwi_intro or rwi_parts:
            full_rwi_content = "\n\n".join([rwi_intro] + rwi_parts if rwi_intro else rwi_parts)
            full_rwi_block = f"{rwi_start_bracket}\n{full_rwi_content}\n{rwi_end_bracket}"
            prompt_parts.append(full_rwi_block)

        # --- Build the rest of the prompt components ---
        for component in active_components:
            component_name = component['name']
            if component_name == "RWI":
                continue

            # Handle the special "jobs" component
            if component_name == "jobs":
                jobs_config_path = os.path.join(self.build_prompt_dir, "jobs", "config.json")
                jobs_config = self._load_json_file(jobs_config_path) or {}

                all_jobs = self.automation_controller.job_definitions
                if all_jobs:
                    job_instructions_parts = []
                    job_begin_bracket = jobs_config.get("job_begin_bracket", "")
                    job_end_bracket = jobs_config.get("job_end_bracket", "")

                    for job_name, job_data in all_jobs.items():
                        instruction = job_data.get("instructions", "")

                        start_bracket = job_begin_bracket.replace("*job_name*", job_name)
                        end_bracket = job_end_bracket.replace("*job_name*", job_name)

                        job_instructions_parts.append(f"{start_bracket}\n{instruction}\n{end_bracket}")

                    full_jobs_content = "\n\n".join(job_instructions_parts)

                    main_instructions = jobs_config.get("instructions", "")
                    if main_instructions:
                        full_jobs_content = f"{main_instructions}\n\n{full_jobs_content}"

                    section_begin_bracket = jobs_config.get("begin_bracket", "")
                    section_end_bracket = jobs_config.get("end_bracket", "")

                    jobs_block = f"{section_begin_bracket}\n{full_jobs_content}\n{section_end_bracket}"
                    prompt_parts.append(jobs_block)
                continue

            # Handle the new "oss_tools" component
            if component_name == "oss_tools":
                oss_tools_config_path = os.path.join(self.build_prompt_dir, "oss_tools", "config.json")
                oss_tools_config = self._load_json_file(oss_tools_config_path) or {}
                all_tools = self.parent_app.oss_tool_manager.get_all_tools()

                if all_tools:
                    tool_parts = []
                    tool_begin_bracket = oss_tools_config.get("tool_begin_bracket", "")
                    tool_end_bracket = oss_tools_config.get("tool_end_bracket", "")

                    for tool in all_tools:
                        definition = tool.params.get("definition", "")
                        if not definition:
                            continue

                        start_bracket = tool_begin_bracket.replace("*tool_name*", tool.name)
                        end_bracket = tool_end_bracket.replace("*tool_name*", tool.name)
                        tool_parts.append(f"{start_bracket}\n{definition}\n{end_bracket}")

                    full_tools_content = "\n\n".join(tool_parts)

                    main_instructions = oss_tools_config.get("instructions", "")
                    if main_instructions:
                        full_tools_content = f"{main_instructions}\n\n{full_tools_content}"

                    section_begin_bracket = oss_tools_config.get("begin_bracket", "")
                    section_end_bracket = oss_tools_config.get("end_bracket", "")

                    oss_tools_block = f"{section_begin_bracket}\n{full_tools_content}\n{section_end_bracket}"
                    prompt_parts.append(oss_tools_block)
                continue

            component_dir = os.path.join(self.build_prompt_dir, component_name)

            # Generic component handling
            config_path = os.path.join(component_dir, "config.json")
            config = self._load_json_file(config_path)
            if not config:
                print(f"Warning: Could not load config for component: {component_name}")
                continue

            begin_bracket = config.get("begin_bracket", "")
            end_bracket = config.get("end_bracket", "")
            content_file = config.get("content_file") or config.get("output_file")

            if not content_file:
                print(f"Warning: No content file specified for component: {component_name}")
                continue

            content_path = os.path.join(component_dir, content_file)
            content = self._load_text_file(content_path)

            if content:
                # Assemble the block using the specified brackets and content
                formatted_block = f"{begin_bracket}\n{content}\n{end_bracket}"
                prompt_parts.append(formatted_block)

        full_prompt_text = "\n\n".join(prompt_parts)
        try:
            with open(self.master_prompt_path, 'w', encoding='utf-8') as f:
                f.write(full_prompt_text)
            print("Master prompt file built successfully from components.")
        except IOError as e:
            print(f"Error writing master prompt file: {e}")

        return full_prompt_text

    def load_base_prompt(self) -> str:
        """
        Builds and loads the master prompt file from components.
        """
        print("Loading base prompt...")
        return self.build_master_prompt_from_components()

# JobProcessor class removed, its functionality is being replaced by AutomationController.

class EnhancedPerformanceMetrics:
    """Enhanced performance metrics with better parsing and display"""

    def __init__(self):
        self.reset_metrics()

    def reset_metrics(self):
        """Reset all metrics to zero"""
        self.kv_cache_reused = 0
        self.prompt_tokens = 0
        self.prompt_speed = 0.0
        self.eval_tokens = 0
        self.eval_speed = 0.0
        self.total_tokens = 0
        self.total_time = 0.0
        self.load_time = 0.0
        self.generation_time_ms = 0.0
        self.tokenization_time_ms = 0.0
        self.kv_caching_time_ms = 0.0

    def parse_llama_logs(self, log_output: str):
        """Enhanced parsing with better error handling"""
        try:
            # Parse KV cache
            kv_match = re.search(r'(\d+)\s+prefix-match hit', log_output)
            if kv_match:
                self.kv_cache_reused = int(kv_match.group(1))

            # Parse prompt evaluation
            prompt_match = re.search(
                r'prompt eval time\s*=\s*([\d.]+)\s*ms\s*/\s*(\d+)\s*tokens.*?([\d.]+)\s*ms per token',
                log_output
            )
            if prompt_match:
                self.tokenization_time_ms = float(prompt_match.group(1))
                self.prompt_tokens = int(prompt_match.group(2))
                ms_per_token = float(prompt_match.group(3))
                self.prompt_speed = 1000.0 / ms_per_token if ms_per_token > 0 else 0.0

            # Parse generation
            eval_match = re.search(
                r'eval time\s*=\s*([\d.]+)\s*ms\s*/\s*(\d+)\s*runs.*?([\d.]+)\s*ms per token',
                log_output
            )
            if eval_match:
                self.generation_time_ms = float(eval_match.group(1))
                self.eval_tokens = int(eval_match.group(2))
                ms_per_token = float(eval_match.group(3))
                self.eval_speed = 1000.0 / ms_per_token if ms_per_token > 0 else 0.0

            self.total_tokens = self.prompt_tokens + self.eval_tokens + self.kv_cache_reused

        except Exception as e:
            print(f"Metrics parsing error: {e}")

    def save_metrics_log(self, settings_manager: SettingsManager):
        """Save formatted metrics to log file"""
        if not settings_manager.settings:
            return

        metrics_dir = settings_manager.settings["paths"].get("metrics_logs", "")
        if not metrics_dir:
            metrics_dir = os.path.join(SCRIPT_DIR, "metrics_logs")

        os.makedirs(metrics_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(metrics_dir, f"log_{timestamp}.txt")

        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"LYRN-AI Performance Metrics Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"KV Cache Reused: {self.kv_cache_reused:,} tokens\n")
                f.write(f"Prompt Tokens: {self.prompt_tokens:,}\n")
                f.write(f"Prompt Speed: {self.prompt_speed:.2f} tok/s\n")
                f.write(f"Generation Tokens: {self.eval_tokens:,}\n")
                f.write(f"Generation Speed: {self.eval_speed:.2f} tok/s\n")
                f.write(f"Total Tokens: {self.total_tokens:,}\n")
                f.write(f"Load Time: {self.load_time:.2f} ms\n")
                f.write(f"Total Time: {self.total_time:.2f} s\n")

            print(f"Metrics saved to: {log_file}")
            return log_file

        except Exception as e:
            print(f"Error saving metrics log: {e}")
            return None

class SystemResourceMonitor:
    """Monitors system resources like CPU, RAM, and VRAM in a background thread."""
    def __init__(self, update_queue):
        self.update_queue = update_queue
        self.running = False
        self.thread = None
        self.nvml_initialized = False

        if pynvml:
            try:
                pynvml.nvmlInit()
                self.nvml_initialized = True
                print("NVML initialized for GPU monitoring.")
            except Exception as e:
                print(f"Warning: Could not initialize NVML for GPU monitoring: {e}")

    def get_stats(self) -> Dict[str, any]:
        """Fetches current system stats."""
        stats = {
            "ram_percent": 0, "ram_used_gb": 0, "ram_total_gb": 0,
            "cpu": 0, "cpu_temp": "N/A",
            "vram_percent": 0, "vram_used_gb": 0, "vram_total_gb": 0,
            "disk_percent": 0, "disk_used_gb": 0, "disk_total_gb": 0
        }

        try:
            ram_info = psutil.virtual_memory()
            stats["ram_percent"] = ram_info.percent
            stats["ram_used_gb"] = ram_info.used / (1024**3)
            stats["ram_total_gb"] = ram_info.total / (1024**3)
        except Exception as e:
            print(f"Could not get RAM info: {e}")

        try:
            # Get disk usage for the drive where the script is located
            disk_info = psutil.disk_usage(os.path.abspath(SCRIPT_DIR))
            stats["disk_percent"] = disk_info.percent
            stats["disk_used_gb"] = disk_info.used / (1024**3)
            stats["disk_total_gb"] = disk_info.total / (1024**3)
        except Exception as e:
            print(f"Could not get Disk info: {e}")

        try:
            stats["cpu"] = psutil.cpu_percent()
        except Exception as e:
            print(f"Could not get CPU percent: {e}")

        # Get CPU temperature
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                stats["cpu_temp"] = f"{temps['coretemp'][0].current:.1f}°C"
            elif 'k10temp' in temps: # for AMD CPUs
                stats["cpu_temp"] = f"{temps['k10temp'][0].current:.1f}°C"
            elif temps:
                key = list(temps.keys())[0]
                stats["cpu_temp"] = f"{temps[key][0].current:.1f}°C"
        except (AttributeError, KeyError, IndexError, PermissionError) as e:
             # print(f"Could not get CPU temp: {e}")
            pass  # Silently ignore if temp sensors are not available/readable

        # Get VRAM usage if NVML is available
        if self.nvml_initialized:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                stats["vram_percent"] = (info.used / info.total) * 100
                stats["vram_used_gb"] = info.used / (1024**3)
                stats["vram_total_gb"] = info.total / (1024**3)
            except Exception as e:
                # This can happen if the driver is not running, etc.
                pass

        return stats

    def _monitor_loop(self):
        """The main loop that runs in a thread."""
        while self.running:
            try:
                stats = self.get_stats()
                self.update_queue.put(('system_stats', stats))
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(5) # Wait longer on error

    def start(self):
        """Starts the monitoring thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            print("System resource monitor started.")

    def stop(self):
        """Stops the monitoring thread and cleans up."""
        self.running = False
        if self.nvml_initialized:
            try:
                pynvml.nvmlShutdown()
                print("NVML shut down.")
            except Exception as e:
                print(f"Warning: NVML shutdown failed: {e}")

class StreamHandler:
    """Enhanced stream handler with better metrics capture and special channel parsing."""

    def __init__(self, gui_queue, metrics: EnhancedPerformanceMetrics, role_mappings: dict, role_color_tags: dict):
        self.gui_queue = gui_queue
        self.metrics = metrics
        self.role_mappings = role_mappings
        self.role_color_tags = role_color_tags
        self.current_response = ""
        self.is_finished = False
        self.log_buffer = ""
        self.buffer = ""
        self.current_role = "final_output"  # Start with a default role
        self.role_tags = {
            "<|channel|>analysis<|message|>": "thinking_process",
            "<|start|>assistant<|channel|>final<|message|>": "final_output",
        }


    def _process_buffer(self):
        """
        Processes the internal buffer for role tags, sends tokens to the GUI,
        and manages role changes.
        """
        while True:
            found_tag = None
            found_pos = -1
            found_role = ""

            # Find the earliest occurrence of any of the defined role tags in the buffer
            for tag, role in self.role_tags.items():
                pos = self.buffer.find(tag)
                if pos != -1 and (found_pos == -1 or pos < found_pos):
                    found_pos = pos
                    found_tag = tag
                    found_role = role

            if found_tag:
                # A tag was found. The content before this tag belongs to the current role.
                content_before_tag = self.buffer[:found_pos]
                if content_before_tag:
                    self.gui_queue.put(('token', content_before_tag, self.current_role))
                    if self.current_role == 'final_output':
                        self.current_response += content_before_tag

                # Check for role transition to add spacing
                if self.current_role == "thinking_process" and found_role == "final_output":
                    self.gui_queue.put(('token', '\n', 'system_text'))

                # We have a new role.
                self.current_role = found_role

                # Remove the processed content and the tag itself from the buffer, then continue the loop.
                self.buffer = self.buffer[found_pos + len(found_tag):]
            else:
                # No tag found. To stream, we can send *most* of the buffer,
                # but keep a tail end to avoid sending a partial tag.
                # The longest tag is 46 chars. Let's use a safe buffer size like 50.
                if len(self.buffer) > 50:
                    content_to_stream = self.buffer[:-50]
                    if content_to_stream:
                        self.gui_queue.put(('token', content_to_stream, self.current_role))
                        if self.current_role == 'final_output':
                            self.current_response += content_to_stream
                        self.buffer = self.buffer[-50:]
                break

    def handle_token(self, token_data):
        """Handle streaming tokens by adding to a buffer and processing it."""
        if 'choices' in token_data and len(token_data['choices']) > 0:
            delta = token_data['choices'][0].get('delta', {})
            content = delta.get('content', '')

            if content:
                self.buffer += content
                self._process_buffer()

            finish_reason = token_data['choices'][0].get('finish_reason')
            if finish_reason is not None:
                # The stream is finished. Flush any remaining content in the buffer.
                if self.buffer:
                    self.gui_queue.put(('token', self.buffer, self.current_role))
                    if self.current_role == 'final_output':
                        self.current_response += self.buffer
                    self.buffer = ""

                self.is_finished = True
                self.gui_queue.put(('finished', self.current_response))

    def capture_logs(self, log_content: str):
        """Enhanced log capture"""
        self.log_buffer += log_content
        if any(marker in self.log_buffer for marker in ["llama_perf_context_print", "eval time", "prompt eval time"]):
            self.metrics.parse_llama_logs(self.log_buffer)
            self.gui_queue.put(('metrics_update', ''))

    def get_response(self) -> str:
        return self.current_response

class QueueIO(io.TextIOBase):
    """A file-like object that writes to a queue."""
    def __init__(self, q):
        self.queue = q

    def write(self, s):
        self.queue.put(s)
        return len(s)

    def flush(self):
        pass

class ConsoleRedirector:
    """Manages the redirection of stdout and stderr to a queue."""
    def __init__(self, queue):
        self.queue = queue
        self.stream = QueueIO(self.queue)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def start(self):
        """Redirect stdout and stderr."""
        sys.stdout = self.stream
        sys.stderr = self.stream
        print("Console output redirected to GUI.")

    def stop(self):
        """Restore original stdout and stderr."""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class LogViewerPopup(ThemedPopup):
    """A popup window that displays redirected console output."""
    def __init__(self, parent, log_queue: queue.Queue, settings_manager: SettingsManager, theme_manager: ThemeManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.log_queue = log_queue
        self.settings_manager = settings_manager

        self.title("LLM & System Log")
        self.geometry("800x600")
        self.minsize(400, 300)

        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        # --- Top bar for controls ---
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=(10,0))

        self.on_top_var = ctk.BooleanVar(value=True)
        self.on_top_checkbox = ctk.CTkCheckBox(top_frame, text="Keep on Top", variable=self.on_top_var, command=self.toggle_on_top)
        self.on_top_checkbox.pack(side="left", padx=10)
        self.toggle_on_top() # Apply the default state on launch

        # --- Main textbox ---
        self.textbox = ctk.CTkTextbox(self, wrap="word", font=("Consolas", 11), border_width=2, border_color=self.theme_manager.get_color("secondary_border_color"))
        self.textbox.pack(expand=True, fill="both", padx=10, pady=10)
        self.textbox.configure(state="disabled")

        self.after(100, self.process_log_queue)
        self.apply_theme()

    def toggle_on_top(self):
        """Toggles the always-on-top status of the log viewer."""
        is_on_top = self.on_top_var.get()
        self.attributes("-topmost", is_on_top)

    def process_log_queue(self):
        """Checks the queue for new output and displays it."""
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.textbox.configure(state="normal")
                self.textbox.insert("end", line)
                self.textbox.see("end")
                self.textbox.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_log_queue)


class JournalLogger:
    """Handles the creation and appending of structured journal logs for full auditability."""
    def __init__(self, chat_dir: str):
        self.chat_dir = Path(chat_dir)
        self.chat_dir.mkdir(parents=True, exist_ok=True)
        self.current_log_path = None

    def start_log(self) -> str:
        """
        Starts a new log file with a timestamp and returns the path.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        timestamp_str = datetime.now().strftime("#%Y-%m-%d %H:%M:%S#")
        filename = f"chat_{timestamp}.txt"
        self.current_log_path = self.chat_dir / filename
        # Create the file immediately and write the timestamp
        with open(self.current_log_path, 'w', encoding='utf-8') as f:
            f.write(f"{timestamp_str}\n\n")
        return str(self.current_log_path)

    def append_log(self, role: str, content: str):
        """
        Appends a new section to the current log file.
        Role can be 'USER', 'THINKING', or 'RESPONSE'.
        """
        if not self.current_log_path:
            print("Error: start_log() must be called before appending.")
            return

        role_upper = role.upper()
        if role_upper == "RESPONSE":
            role_upper = "ASSISTANT"
        start_tag = f"#{role_upper}_START#"
        end_tag = f"#{role_upper}_END#"

        formatted_content = f"{start_tag}\n{content}\n{end_tag}\n\n"

        try:
            with open(self.current_log_path, 'a', encoding='utf-8') as f:
                f.write(formatted_content)
        except Exception as e:
            print(f"Error appending to log file {self.current_log_path}: {e}")

    def new_log_session(self):
        """Resets the current_log_path to ensure the next write starts a new file."""
        self.current_log_path = None

class ModelSelectorPopup(ThemedPopup):
    """A popup window to select a model and configure settings on startup."""
    def __init__(self, parent, settings_manager: SettingsManager, theme_manager: ThemeManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.settings_manager = settings_manager

        self.title("Model Settings")
        self.geometry("600x550")
        self.minsize(500, 500)
        self.grab_set() # Modal - prevent interaction with main window

        self.model_path = ""
        self.model_settings = {}
        self.dont_show_again = ctk.BooleanVar(value=False)

        self.create_widgets()
        self.load_models()
        self.load_current_settings()
        self.apply_theme()

    def create_widgets(self):
        """Create widgets for the popup."""
        main_frame = self

        try:
            title_font = ctk.CTkFont(family="Consolas", size=16, weight="bold")
            font = ctk.CTkFont(family="Consolas", size=12)
        except:
            title_font = ("Consolas", 16, "bold")
            font = ("Consolas", 12)

        ctk.CTkLabel(main_frame, text="Select a Model to Load", font=title_font).pack(pady=(0, 20))

        # Model selection dropdown
        model_frame = ctk.CTkFrame(main_frame)
        model_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(model_frame, text="Model File:", font=font).pack(side="left", padx=10)
        self.model_dropdown = ctk.CTkComboBox(model_frame, values=[""], font=font)
        self.model_dropdown.set("")
        self.model_dropdown.pack(side="left", expand=True, fill="x", padx=10)

        # Model parameters
        params_frame = ctk.CTkFrame(main_frame)
        params_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(params_frame, text="Model Parameters", font=font).pack()

        grid_frame = ctk.CTkFrame(params_frame)
        grid_frame.pack(pady=10)

        params = [
            ("Context Size:", "n_ctx", 0, 0), ("Threads:", "n_threads", 0, 2),
            ("GPU Layers:", "n_gpu_layers", 1, 0), ("Temperature:", "temperature", 1, 2),
            ("Max Tokens:", "max_tokens", 2, 0), ("Top P:", "top_p", 2, 2),
            ("Top K:", "top_k", 3, 0), ("Batch Size:", "n_batch", 3, 2),
            ("Chat Format:", "chat_format", 4, 0)
        ]

        self.model_entries = {}
        for label, key, row, col in params:
            ctk.CTkLabel(grid_frame, text=label, font=font).grid(row=row, column=col, padx=10, pady=5, sticky="e")
            entry = ctk.CTkEntry(grid_frame, width=120, font=font)
            entry.grid(row=row, column=col+1, padx=10, pady=5, sticky="w")
            self.model_entries[key] = entry


        # Warning Label
        warning_label = ctk.CTkLabel(
            main_frame,
            text="Warning: You must reload the model for any changes to take effect.",
            text_color=LYRN_WARNING,
            font=font,
            wraplength=550, # Ensure text wraps nicely
            justify="center"
        )
        warning_label.pack(pady=(15, 0), padx=20)

        # Bottom frame for checkbox and buttons
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.pack(fill="x", padx=10, pady=(15, 0))

        self.dont_show_checkbox = ctk.CTkCheckBox(
            bottom_frame, text="Don't show this again on startup",
            font=font, variable=self.dont_show_again
        )
        self.dont_show_checkbox.pack(side="left", padx=10)

        self.load_button = ctk.CTkButton(bottom_frame, text="Load Model", font=font, command=self.load_model)
        self.load_button.pack(side="right", padx=10)

        # --- Preset Management ---
        preset_frame = ctk.CTkFrame(main_frame)
        preset_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(preset_frame, text="Presets:", font=font).pack(side="left", padx=10)

        save_preset_button = ctk.CTkButton(preset_frame, text="Save", width=50, font=font, command=self.save_preset)
        save_preset_button.pack(side="left", padx=5)

        for i in range(1, 6):
            preset_button = ctk.CTkButton(preset_frame, text=str(i), width=30, font=font, command=lambda num=i: self.load_preset(num))
            preset_button.pack(side="left", padx=5)

    def save_preset(self):
        """Saves the current model settings as a numbered preset."""
        dialog = ThemedInputDialog(self, self.theme_manager, text="Enter preset number to save (1-5):", title="Save Preset")
        preset_num_str = dialog.get_input()

        if not preset_num_str or not preset_num_str.isdigit() or not 1 <= int(preset_num_str) <= 5:
            print("Invalid preset number. Please enter a number between 1 and 5.")
            # Optionally, show a message to the user
            return

        preset_num = preset_num_str

        # Gather current settings from the UI
        selected_model_file = self.model_dropdown.get()
        if not selected_model_file:
            print("Cannot save preset without a selected model.")
            return

        preset_data = {
            "model_path": os.path.join(SCRIPT_DIR, "models", selected_model_file)
        }
        for key, entry in self.model_entries.items():
            value = entry.get()
            if key in ["n_ctx", "n_threads", "n_gpu_layers", "max_tokens", "n_batch", "top_k"]:
                try:
                    preset_data[key] = int(value)
                except (ValueError, TypeError):
                    preset_data[key] = self.settings_manager.create_empty_settings_structure()["active"].get(key, 0)
            elif key in ["temperature", "top_p"]:
                try:
                    preset_data[key] = float(value)
                except (ValueError, TypeError):
                    preset_data[key] = self.settings_manager.create_empty_settings_structure()["active"].get(key, 0.0)
            elif key == "chat_format":
                preset_data[key] = None if not value else value
            else:
                # This case might not be hit with the new structure, but it's safe to keep
                preset_data[key] = value

        # Save to settings.json
        if "model_presets" not in self.settings_manager.settings:
            self.settings_manager.settings["model_presets"] = {}

        self.settings_manager.settings["model_presets"][preset_num] = preset_data
        self.settings_manager.save_settings()
        print(f"Preset '{preset_num}' saved successfully.")
        # Optionally, update a status label in the popup
        self.parent_app.update_status(f"Preset {preset_num} saved.", LYRN_SUCCESS)


    def load_preset(self, preset_num: int):
        """Loads a model settings preset and populates the UI."""
        preset_num_str = str(preset_num)
        presets = self.settings_manager.settings.get("model_presets", {})

        if preset_num_str not in presets:
            print(f"Preset '{preset_num_str}' not found.")
            self.parent_app.update_status(f"Preset {preset_num_str} not found.", LYRN_WARNING)
            return

        preset_data = presets[preset_num_str]

        # Populate UI fields
        for key, entry in self.model_entries.items():
            entry.delete(0, "end")
            value = preset_data.get(key)
            if key == "chat_format":
                 entry.insert(0, "" if value is None else str(value))
            elif value is not None:
                entry.insert(0, str(value))

        model_path = preset_data.get("model_path", "")
        if model_path:
            model_filename = os.path.basename(model_path)
            if model_filename in self.model_dropdown.cget("values"):
                self.model_dropdown.set(model_filename)
                self.model_dropdown.update() # Force UI to process the change immediately

        print(f"Preset '{preset_num_str}' loaded.")
        self.parent_app.update_status(f"Preset {preset_num_str} loaded.", LYRN_INFO)
        self.apply_theme()

    def load_models(self):
        """Scan the models directory and populate the dropdown."""
        models_dir = os.path.join(SCRIPT_DIR, "models")
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            self.model_dropdown.configure(values=["'models' folder created."])
            return

        try:
            model_files = [f for f in os.listdir(models_dir) if f.endswith((".gguf", ".bin"))]
            if model_files:
                self.model_dropdown.configure(values=model_files)
                self.model_dropdown.set(model_files[0])
            else:
                self.model_dropdown.configure(values=[""])
                self.model_dropdown.set("")
        except Exception as e:
            self.model_dropdown.configure(values=[f"Error: {e}"])
            print(f"Error scanning for models: {e}")

    def load_current_settings(self):
        """Load current model settings from settings manager."""
        if not self.settings_manager.settings:
            return

        active_settings = self.settings_manager.settings.get("active", {})
        for key, entry in self.model_entries.items():
            entry.delete(0, "end")
            if key == "chat_format":
                # Default to None if missing. Show empty string for None, otherwise the value.
                val = active_settings.get(key, None)
                entry.insert(0, "" if val is None else str(val))
            else:
                # Keep original behavior for other settings for now
                default_value = ""
                entry.insert(0, str(active_settings.get(key, default_value)))

        # Pre-select model in dropdown if it exists
        current_model_path = active_settings.get("model_path", "")
        if current_model_path:
            model_filename = os.path.basename(current_model_path)
            if model_filename in self.model_dropdown.cget("values"):
                self.model_dropdown.set(model_filename)


    def load_model(self):
        """Save settings, trigger model load in parent, and close popup."""
        # 1. Get settings from UI
        selected_model_file = self.model_dropdown.get()
        if not selected_model_file or "No models found" in selected_model_file:
            # Maybe show an error label in the popup
            print("No valid model selected.")
            return

        self.model_path = os.path.join(SCRIPT_DIR, "models", selected_model_file)

        new_active_settings = self.settings_manager.settings.get("active", {}).copy()
        new_active_settings["model_path"] = self.model_path

        for key, entry in self.model_entries.items():
            value = entry.get()
            if key in ["n_ctx", "n_threads", "n_gpu_layers", "max_tokens", "n_batch", "top_k"]:
                try:
                    new_active_settings[key] = int(value)
                except (ValueError, TypeError):
                    print(f"Warning: Could not parse '{value}' for '{key}'. Using default.")
                    # Use a sensible default from the empty structure if parsing fails
                    new_active_settings[key] = self.settings_manager.create_empty_settings_structure()["active"].get(key, 0)
            elif key in ["temperature", "top_p"]:
                try:
                    new_active_settings[key] = float(value)
                except (ValueError, TypeError):
                    print(f"Warning: Could not parse '{value}' for '{key}'. Using default.")
                    new_active_settings[key] = self.settings_manager.create_empty_settings_structure()["active"].get(key, 0.0)
            elif key == "chat_format":
                # If the value is an empty string, save None. Otherwise, save the string.
                new_active_settings[key] = None if not value else value
            else:
                new_active_settings[key] = value


        # 2. Save settings
        self.settings_manager.settings["active"] = new_active_settings
        if self.dont_show_again.get():
            self.settings_manager.ui_settings["show_model_selector"] = False

        self.settings_manager.save_settings()

        # 3. Trigger load in parent
        self.parent_app.update_status("Loading selected model...", LYRN_INFO)
        threading.Thread(target=self.parent_app.setup_model, daemon=True).start()

        # 4. Close popup
        self.grab_release()
        self.destroy()

class CommandPalette(ThemedPopup):
    def __init__(self, parent, commands: List[Dict[str, any]], theme_manager: ThemeManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.all_commands = commands
        self.filtered_commands = commands

        self.title("Command Palette")
        self.geometry("600x350")
        self.minsize(400, 300)
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        try:
            font = ctk.CTkFont(family="Consolas", size=14)
        except:
            font = ("Consolas", 14)

        self.search_entry = ctk.CTkEntry(self, placeholder_text="Type a command...", font=font)
        self.search_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._filter_commands)
        self.search_entry.focus()

        self.results_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.results_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.bind("<Escape>", lambda e: self.destroy())

        self._populate_command_list()
        self.apply_theme()

    def _filter_commands(self, event=None):
        search_term = self.search_entry.get().lower()
        if not search_term:
            self.filtered_commands = self.all_commands
        else:
            self.filtered_commands = [
                cmd for cmd in self.all_commands
                if search_term in cmd["name"].lower()
            ]
        self._populate_command_list()

    def _populate_command_list(self):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Add new results
        for i, cmd in enumerate(self.filtered_commands):
            btn = ctk.CTkButton(
                self.results_frame,
                text=cmd["name"],
                anchor="w",
                command=lambda c=cmd: self._execute_command(c["command"])
            )
            btn.pack(fill="x", padx=5, pady=3)
            if i == 0: # Select the first item
                btn.focus()
                self.bind("<Return>", lambda e, c=cmd: self._execute_command(c["command"]))


    def _execute_command(self, command_func):
        self.destroy()
        self.parent_app.after(50, command_func) # Use after to ensure palette closes first

class TabbedSettingsDialog(ThemedPopup):
    """Enhanced settings dialog with tabs"""

    def __init__(self, parent, settings_manager: SettingsManager, theme_manager: ThemeManager, language_manager: LanguageManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.settings_manager = settings_manager
        self.language_manager = language_manager

        self.title(self.language_manager.get("settings_window_title"))
        self.geometry("900x750")
        self.minsize(800, 650)

        self.show_model_selector_var = ctk.BooleanVar()

        self.create_widgets()
        self.load_current_settings()
        self.apply_theme()
        self.refresh_chat_color_previews()

    def open_theme_builder(self):
        """Opens the theme builder popup."""
        if not hasattr(self.parent_app, 'theme_builder_popup') or not self.parent_app.theme_builder_popup.winfo_exists():
            self.parent_app.theme_builder_popup = ThemeBuilderPopup(self, self.theme_manager, self.language_manager)
            self.parent_app.theme_builder_popup.focus()
        else:
            self.parent_app.theme_builder_popup.lift()
            self.parent_app.theme_builder_popup.focus()

    def create_widgets(self):
        """Create tabbed interface"""
        # Main tabview
        self.tabview = ctk.CTkTabview(self, width=850, height=600)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Create tabs
        self.tab_paths = self.tabview.add(self.language_manager.get("tab_directory_paths"))
        # self.tab_prompt = self.tabview.add(self.language_manager.get("tab_prompt_manager")) # Tab is being removed
        # self.tab_personality = self.tabview.add("Personality")
        self.tab_ui_settings = self.tabview.add("UI Settings")
        self.tab_chat = self.tabview.add("Chat")
        self.tab_advanced = self.tabview.add(self.language_manager.get("tab_advanced"))

        # Add help buttons to tab headers
        self.add_help_to_tab(self.tab_paths, "settings_popup.directory_paths")
        self.add_help_to_tab(self.tab_ui_settings, "settings_popup.ui_settings")
        self.add_help_to_tab(self.tab_chat, "settings_popup.chat_settings")
        self.add_help_to_tab(self.tab_advanced, "settings_popup.advanced_settings")

        self.create_paths_tab()
        # self.create_prompt_manager_tab() # Logic moved to popup
        # self.create_personality_tab()
        self.create_ui_settings_tab()
        self.create_chat_tab()
        self.create_advanced_tab()

        # Button frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.save_button = ctk.CTkButton(button_frame, text=self.language_manager.get("button_save_all"),
                                        command=self.save_all_settings)
        self.save_button.pack(side="left", padx=10, pady=10)
        Tooltip(self.save_button, self.parent_app.tooltips.get("save_all_settings_button", ""))

        self.cancel_button = ctk.CTkButton(button_frame, text=self.language_manager.get("button_cancel"),
                                          command=self.destroy)
        self.cancel_button.pack(side="right", padx=10, pady=10)
        Tooltip(self.cancel_button, self.parent_app.tooltips.get("cancel_settings_button", ""))

    def add_help_to_tab(self, tab_frame, help_code):
        """Adds a help button to the top-right corner of a tab frame."""
        help_button = ctk.CTkButton(
            tab_frame,
            text="?",
            width=28,
            height=28,
            command=lambda: self.parent_app.show_help(help_code)
        )
        help_button.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

    def create_paths_tab(self):
        """Create directory paths tab"""
        try:
            font = ctk.CTkFont(family="Consolas", size=12)
        except:
            font = ("Consolas", 12)

        # Scrollable frame for paths
        scroll_frame = ctk.CTkScrollableFrame(self.tab_paths)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.path_entries = {}
        path_labels = {
            "static_snapshots": "Static Snapshots Directory",
            "dynamic_snapshots": "Dynamic Snapshots Directory",
            "active_jobs": "Active Jobs Directory",
            "deltas": "Deltas Directory",
            "chat": "Chat Directory",
            "output": "Output Directory",
            "metrics_logs": "Metrics Logs Directory"
        }

        for key, label in path_labels.items():
            ctk.CTkLabel(scroll_frame, text=f"{label}:", font=font).pack(
                anchor="w", padx=10, pady=(10, 0))
            entry = ctk.CTkEntry(scroll_frame, font=font)
            entry.pack(fill="x", padx=10, pady=(0, 5))
            self.path_entries[key] = entry

    def create_chat_tab(self):
        """Create the Chat settings tab with a refactored layout."""
        try:
            font = ctk.CTkFont(family="Consolas", size=12)
            title_font = ctk.CTkFont(family="Consolas", size=14, weight="bold")
        except:
            font = ("Consolas", 12)
            title_font = ("Consolas", 14, "bold")

        # Main frame with 2 columns
        self.tab_chat.grid_columnconfigure(0, weight=1)
        self.tab_chat.grid_columnconfigure(1, weight=1)
        self.tab_chat.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(self.tab_chat)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        right_frame = ctk.CTkFrame(self.tab_chat)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)

        # --- LEFT FRAME: History and Injection ---
        ctk.CTkLabel(left_frame, text="Chat History & Context", font=title_font).pack(pady=(10, 20))

        # Chat History Saving Toggle
        self.save_chat_history_var = ctk.BooleanVar()
        self.save_chat_history_switch = ctk.CTkSwitch(left_frame, text="Save Chat History", variable=self.save_chat_history_var, font=font)
        self.save_chat_history_switch.pack(anchor="w", padx=20, pady=10)
        Tooltip(self.save_chat_history_switch, "If enabled, conversations will be saved to the episodic memory.")

        # Chat History Length Stepper
        length_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        length_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(length_frame, text="History Length:", font=font).pack(side="left")

        self.history_length_entry = ctk.CTkEntry(length_frame, width=50, font=font, justify="center")
        self.history_length_entry.pack(side="left", padx=10)

        stepper_frame = ctk.CTkFrame(length_frame, fg_color="transparent")
        stepper_frame.pack(side="left")

        up_button = ctk.CTkButton(stepper_frame, text="▲", width=25, height=12, font=font, command=self.increase_history_length)
        up_button.pack(pady=(0,1))
        down_button = ctk.CTkButton(stepper_frame, text="▼", width=25, height=12, font=font, command=self.decrease_history_length)
        down_button.pack(pady=(1,0))

        Tooltip(length_frame, "How many past user/assistant message pairs to include in the context for the LLM. 0 means none.")

        # Injection Toggles
        self.enable_deltas_var = ctk.BooleanVar()
        self.enable_deltas_switch = ctk.CTkSwitch(left_frame, text="Enable Delta Injection", variable=self.enable_deltas_var, font=font)
        self.enable_deltas_switch.pack(anchor="w", padx=20, pady=10)
        Tooltip(self.enable_deltas_switch, "If enabled, deltas will be injected into the prompt.")

        self.enable_chat_history_var = ctk.BooleanVar()
        self.enable_chat_history_switch = ctk.CTkSwitch(left_frame, text="Enable Chat History Injection", variable=self.enable_chat_history_var, font=font)
        self.enable_chat_history_switch.pack(anchor="w", padx=20, pady=10)
        Tooltip(self.enable_chat_history_switch, "If enabled, chat history will be injected into the prompt.")

        # Folder Management
        folder_frame = ctk.CTkFrame(left_frame)
        folder_frame.pack(fill="x", padx=15, pady=20)
        ctk.CTkLabel(folder_frame, text="Folder Management", font=font).pack(anchor="w", pady=(0, 10))
        clear_chat_folder_button = ctk.CTkButton(folder_frame, text="Clear Chat Folder", font=font, command=self.parent_app.clear_chat_folder)
        clear_chat_folder_button.pack(side="left", padx=5, pady=5)
        Tooltip(clear_chat_folder_button, "Deletes all saved chat log files from the chat directory.")
        open_chat_folder_button = ctk.CTkButton(folder_frame, text="Open Chat Folder", font=font, command=self.parent_app.open_chat_folder)
        open_chat_folder_button.pack(side="left", padx=5, pady=5)
        Tooltip(open_chat_folder_button, "Open chat folder in file explorer.")

        # Chat History Button
        history_button = ctk.CTkButton(left_frame, text="View Chat History", font=font, command=self.parent_app.open_memory_popup)
        history_button.pack(fill="x", padx=15, pady=10)
        Tooltip(history_button, "Open the chat history viewer.")

        # --- RIGHT FRAME: Appearance ---
        ctk.CTkLabel(right_frame, text="Chat Appearance", font=title_font).pack(pady=(10, 20))

        # Toggle for thinking/analysis text
        self.show_thinking_var = ctk.BooleanVar()
        self.show_thinking_switch = ctk.CTkSwitch(right_frame, text="Show Thinking/Analysis Text", variable=self.show_thinking_var, font=font)
        self.show_thinking_switch.pack(anchor="w", padx=20, pady=10)
        Tooltip(self.show_thinking_switch, "Toggle the visibility of the model's intermediate thinking and analysis steps.")

        # Color settings
        color_frame = ctk.CTkFrame(right_frame)
        color_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.color_setting_widgets = {}
        color_roles = {
            "user_text": "User Text",
            "thinking_text": "Thinking/Analysis Text",
            "assistant_text": "Assistant Text",
            "system_text": "System Text"
        }

        for key, label_text in color_roles.items():
            row_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(row_frame, text=label_text, font=font, width=150, anchor="w").pack(side="left")
            hex_entry = ctk.CTkEntry(row_frame, font=font, width=90)
            hex_entry.pack(side="left", padx=10)

            preview = ctk.CTkFrame(row_frame, width=28, height=28, border_width=1)
            preview.pack(side="left", padx=5)

            hex_entry.bind("<KeyRelease>", lambda e, k=key: self.update_color_preview(k))
            self.color_setting_widgets[key] = {'entry': hex_entry, 'preview': preview}

    def update_color_preview(self, key: str):
        """Updates the color preview swatch from the hex entry."""
        widget_set = self.color_setting_widgets.get(key)
        if not widget_set:
            return

        hex_code = widget_set['entry'].get()
        # Basic validation for a hex color
        if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_code):
            widget_set['preview'].configure(fg_color=hex_code)
        else:
            # Indicate invalid color, e.g., by setting a default or error color
            widget_set['preview'].configure(fg_color="gray")

    def refresh_chat_color_previews(self):
        """Force-update the color swatches after a theme change might have reset them."""
        if hasattr(self, 'color_setting_widgets'):
            for key in self.color_setting_widgets:
                self.update_color_preview(key)

    def increase_history_length(self):
        try:
            current_value = int(self.history_length_entry.get())
            self.history_length_entry.delete(0, "end")
            self.history_length_entry.insert(0, str(current_value + 1))
        except ValueError:
            self.history_length_entry.delete(0, "end")
            self.history_length_entry.insert(0, "10")

    def decrease_history_length(self):
        try:
            current_value = int(self.history_length_entry.get())
            if current_value > 0:
                self.history_length_entry.delete(0, "end")
                self.history_length_entry.insert(0, str(current_value - 1))
        except ValueError:
            self.history_length_entry.delete(0, "end")
            self.history_length_entry.insert(0, "10")

    def create_ui_settings_tab(self):
        """Create the UI settings tab."""
        try:
            font = ctk.CTkFont(family="Consolas", size=12)
            title_font = ctk.CTkFont(family="Consolas", size=14, weight="bold")
        except:
            font = ("Consolas", 12)
            title_font = ("Consolas", 14, "bold")

        self.tab_ui_settings.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.tab_ui_settings, text="User Interface Customization",
                    font=title_font).pack(pady=20)

        # --- Language Settings ---
        language_frame = ctk.CTkFrame(self.tab_ui_settings)
        language_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(language_frame, text="Language", font=title_font).pack(pady=10, anchor="w", padx=10)

        lang_select_frame = ctk.CTkFrame(language_frame)
        lang_select_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(lang_select_frame, text="Display Language:", font=font).pack(side="left", padx=5)

        available_languages = self.language_manager.get_available_languages()
        self.language_var = ctk.StringVar(value=self.language_manager.language)
        self.language_selector = ctk.CTkComboBox(lang_select_frame, values=available_languages, variable=self.language_var, font=font)
        self.language_selector.pack(side="left", padx=5, expand=True, fill="x")

        # We will add functionality later. For now, just save the setting.
        # A restart will be required to see changes.
        ctk.CTkLabel(language_frame, text="Language changes require an application restart.", font=font).pack(padx=20, pady=5, anchor="w")

        # --- Font and Theme Settings ---
        display_frame = ctk.CTkFrame(self.tab_ui_settings)
        display_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(display_frame, text="Display & Theme", font=title_font).pack(pady=10, anchor="w", padx=10)

        # Theme selection
        theme_frame = ctk.CTkFrame(display_frame)
        theme_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(theme_frame, text="Theme:", font=font).pack(side="left", padx=5)
        theme_selector = ctk.CTkComboBox(
            theme_frame,
            values=self.parent_app.theme_manager.get_theme_names(),
            command=self.parent_app.on_theme_selected
        )
        theme_selector.pack(side="left", expand=True, fill="x", padx=5)
        theme_selector.set(self.parent_app.theme_manager.get_current_theme_name())
        Tooltip(theme_selector, self.parent_app.tooltips.get("theme_dropdown", ""))

        # Font size controls
        font_frame = ctk.CTkFrame(display_frame)
        font_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(font_frame, text="Font Size:", font=font).pack(side="left", padx=5)

        self.font_size_label = ctk.CTkLabel(font_frame, text=str(self.parent_app.current_font_size), font=font)
        self.font_size_label.pack(side="left", padx=5)

        font_decrease_button = ctk.CTkButton(font_frame, text="A-", width=30, height=25,
                     font=font,
                     command=self.decrease_font_in_settings)
        font_decrease_button.pack(side="left", padx=2)

        font_increase_button = ctk.CTkButton(font_frame, text="A+", width=30, height=25,
                     font=font,
                     command=self.increase_font_in_settings)
        font_increase_button.pack(side="left", padx=2)


        # --- Moved Buttons ---
        moved_buttons_frame = ctk.CTkFrame(self.tab_ui_settings)
        moved_buttons_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(moved_buttons_frame, text="Chat Controls", font=title_font).pack(pady=10, anchor="w", padx=10)

        clear_chat_button = ctk.CTkButton(moved_buttons_frame, text="🗑️ Clear Display Text",
                                             font=font, command=self.parent_app.clear_chat)
        clear_chat_button.pack(padx=10, pady=5, anchor="w")
        Tooltip(clear_chat_button, self.parent_app.tooltips.get("clear_chat_button", ""))

        # --- Terminal Settings ---
        terminal_frame = ctk.CTkFrame(self.tab_ui_settings)
        terminal_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(terminal_frame, text="Terminal", font=title_font).pack(pady=10, anchor="w", padx=10)

        path_frame = ctk.CTkFrame(terminal_frame)
        path_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(path_frame, text="Terminal Start Path:", font=font).pack(side="left", padx=5)
        self.terminal_start_path_entry = ctk.CTkEntry(path_frame, font=font)
        self.terminal_start_path_entry.pack(side="left", expand=True, fill="x", padx=5)

    def increase_font_in_settings(self):
        self.parent_app.increase_font_size()
        self.font_size_label.configure(text=str(self.parent_app.current_font_size))

    def decrease_font_in_settings(self):
        self.parent_app.decrease_font_size()
        self.font_size_label.configure(text=str(self.parent_app.current_font_size))

    def create_advanced_tab(self):
        """Create advanced settings tab"""
        try:
            font = ctk.CTkFont(family="Consolas", size=12)
            title_font = ctk.CTkFont(family="Consolas", size=14, weight="bold")
        except:
            font = ("Consolas", 12)
            title_font = ("Consolas", 14, "bold")

        ctk.CTkLabel(self.tab_advanced, text="Advanced Operations",
                    font=title_font).pack(pady=20)

        # System maintenance section
        maint_frame = ctk.CTkFrame(self.tab_advanced)
        maint_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(maint_frame, text="System Maintenance", font=title_font).pack(pady=10)

        # Clear operations
        clear_frame = ctk.CTkFrame(maint_frame)
        clear_frame.pack(fill="x", padx=10, pady=10)

        clear_chat_dir_button = ctk.CTkButton(clear_frame, text="Clear Chat Directory",
                     font=font, command=self.clear_chat_directory)
        clear_chat_dir_button.pack(side="left", padx=5, pady=5)
        Tooltip(clear_chat_dir_button, self.parent_app.tooltips.get("clear_chat_directory_button", ""))

        clear_deltas_dir_button = ctk.CTkButton(clear_frame, text="Clear Deltas Directory",
                        font=font, command=self.clear_deltas_directory)
        clear_deltas_dir_button.pack(side="left", padx=5, pady=5)
        Tooltip(clear_deltas_dir_button, self.parent_app.tooltips.get("clear_deltas_directory_button", ""))

        clear_metrics_logs_button = ctk.CTkButton(clear_frame, text="Clear Metrics Logs",
                        font=font, command=self.clear_metrics_logs)
        clear_metrics_logs_button.pack(side="left", padx=5, pady=5)
        Tooltip(clear_metrics_logs_button, self.parent_app.tooltips.get("clear_metrics_logs_button", ""))

        # Model operations
        model_frame = ctk.CTkFrame(maint_frame)
        model_frame.pack(fill="x", padx=10, pady=10)

        force_cleanup_button = ctk.CTkButton(model_frame, text="🧹 Force Memory Cleanup",
                        font=font, command=self.force_memory_cleanup)
        force_cleanup_button.pack(side="left", padx=5, pady=5)
        Tooltip(force_cleanup_button, self.parent_app.tooltips.get("force_memory_cleanup_button", ""))

        # Testing utilities
        test_frame = ctk.CTkFrame(self.tab_advanced)
        test_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(test_frame, text="Testing Utilities", font=title_font).pack(pady=10)

        util_frame = ctk.CTkFrame(test_frame)
        util_frame.pack(fill="x", padx=10, pady=10)

        export_info_button = ctk.CTkButton(util_frame, text="Export System Info",
                        font=font, command=self.export_system_info)
        export_info_button.pack(side="left", padx=5, pady=5)
        Tooltip(export_info_button, self.parent_app.tooltips.get("export_system_info_button", ""))

        test_perf_button = ctk.CTkButton(util_frame, text="Test Model Performance",
                        font=font, command=self.test_model_performance)
        test_perf_button.pack(side="left", padx=5, pady=5)
        Tooltip(test_perf_button, self.parent_app.tooltips.get("test_model_performance_button", ""))

        validate_dirs_button = ctk.CTkButton(util_frame, text="Validate Directories",
                        font=font, command=self.validate_directories)
        validate_dirs_button.pack(side="left", padx=5, pady=5)
        Tooltip(validate_dirs_button, self.parent_app.tooltips.get("validate_directories_button", ""))

        open_theme_builder_button = ctk.CTkButton(util_frame, text="Open Theme Builder",
                        font=font, command=self.open_theme_builder)
        open_theme_builder_button.pack(side="left", padx=5, pady=5)
        Tooltip(open_theme_builder_button, "Open the live theme editor popup.")

        # Add checkbox for re-enabling model selector
        # Model Loading Control Section
        model_loading_frame = ctk.CTkFrame(self.tab_advanced)
        model_loading_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(model_loading_frame, text="Model Loading Control", font=title_font).pack(pady=10)

        self.autoload_model_var = ctk.BooleanVar()
        self.show_model_selector_var = ctk.BooleanVar()
        self.llm_log_visible_var = ctk.BooleanVar()
        self.llm_log_on_top_var = ctk.BooleanVar()

        ctk.CTkCheckBox(model_loading_frame, text="Autoload model on GUI start", font=font, variable=self.autoload_model_var).pack(anchor="w", padx=10, pady=5)
        ctk.CTkCheckBox(model_loading_frame, text="Show model selector on startup", font=font, variable=self.show_model_selector_var).pack(anchor="w", padx=10, pady=5)
        ctk.CTkCheckBox(model_loading_frame, text="LLM log default visibility", font=font, variable=self.llm_log_visible_var).pack(anchor="w", padx=10, pady=5)
        ctk.CTkCheckBox(model_loading_frame, text="LLM log always on top", font=font, variable=self.llm_log_on_top_var).pack(anchor="w", padx=10, pady=5)

    def load_current_settings(self):
        """Load current settings into all tabs"""
        if not self.settings_manager.settings:
            return

        settings = self.settings_manager.settings
        active = settings.get("active", {})
        paths = settings.get("paths", {})

        # Model settings are managed in the main UI now.

        # Load paths
        for key, entry in self.path_entries.items():
            if key in paths:
                entry.insert(0, paths[key])

        # Load UI settings
        self.show_model_selector_var.set(self.settings_manager.ui_settings.get("show_model_selector", True))
        self.autoload_model_var.set(self.settings_manager.ui_settings.get("autoload_model", False))
        self.llm_log_visible_var.set(self.settings_manager.ui_settings.get("llm_log_visible", False))
        self.llm_log_on_top_var.set(self.settings_manager.ui_settings.get("llm_log_on_top", False))
        self.terminal_start_path_entry.insert(0, self.settings_manager.ui_settings.get("terminal_start_path", ""))

        # Load Chat settings
        self.save_chat_history_var.set(self.settings_manager.ui_settings.get("save_chat_history", True))
        chat_len = self.settings_manager.ui_settings.get("chat_history_length", 10)
        self.history_length_entry.delete(0, "end")
        self.history_length_entry.insert(0, str(chat_len))
        self.enable_deltas_var.set(self.settings_manager.ui_settings.get("enable_deltas", True))
        self.enable_chat_history_var.set(self.settings_manager.ui_settings.get("enable_chat_history", True))

        # Load Appearance settings
        self.show_thinking_var.set(self.settings_manager.get_setting("show_thinking_text", True))
        chat_colors = self.settings_manager.get_setting("chat_colors", {})
        for key, widgets in self.color_setting_widgets.items():
            color = chat_colors.get(key, "#FFFFFF")
            widgets['entry'].delete(0, "end")
            widgets['entry'].insert(0, color)
            self.update_color_preview(key) # Update preview from loaded color

    def clear_chat_directory(self):
        """Clear chat directory after confirmation."""
        from confirmation_dialog import ConfirmationDialog

        prefs = self.parent_app.settings_manager.ui_settings.get("confirmation_preferences", {})
        if prefs.get("clear_chat_directory"):
            confirmed = True
        else:
            confirmed, dont_ask_again = ConfirmationDialog.show(
                self,
                self.theme_manager,
                title="Confirm Clear Directory",
                message="Are you sure you want to permanently delete all files in the chat directory?"
            )
            if dont_ask_again:
                prefs["clear_chat_directory"] = True
                self.parent_app.settings_manager.ui_settings["confirmation_preferences"] = prefs
                self.parent_app.settings_manager.save_settings()

        if not confirmed:
            self.parent_app.update_status("Clear chat directory cancelled.", LYRN_INFO)
            return

        if not self.settings_manager.settings:
            return

        chat_dir = self.settings_manager.settings["paths"].get("chat", "")
        if chat_dir and os.path.exists(chat_dir):
            try:
                count = 0
                for filename in os.listdir(chat_dir):
                    file_path = os.path.join(chat_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        count += 1
                print(f"Cleared chat directory: {chat_dir}")
                self.parent_app.update_status(f"Cleared {count} files from chat directory.", LYRN_SUCCESS)
            except Exception as e:
                print(f"Error clearing chat directory: {e}")
                self.parent_app.update_status("Error clearing chat directory.", LYRN_ERROR)

    def clear_deltas_directory(self):
        """Clear deltas directory after confirmation."""
        from confirmation_dialog import ConfirmationDialog

        prefs = self.parent_app.settings_manager.ui_settings.get("confirmation_preferences", {})
        if prefs.get("clear_deltas_directory"):
            confirmed = True
        else:
            confirmed, dont_ask_again = ConfirmationDialog.show(
                self,
                self.theme_manager,
                title="Confirm Clear Directory",
                message="Are you sure you want to permanently delete all files in the deltas directory?"
            )
            if dont_ask_again:
                prefs["clear_deltas_directory"] = True
                self.parent_app.settings_manager.ui_settings["confirmation_preferences"] = prefs
                self.parent_app.settings_manager.save_settings()

        if not confirmed:
            self.parent_app.update_status("Clear deltas directory cancelled.", LYRN_INFO)
            return

        if not self.settings_manager.settings:
            return

        deltas_dir = self.settings_manager.settings["paths"].get("deltas", "")
        if deltas_dir and os.path.exists(deltas_dir):
            try:
                count = 0
                for filename in os.listdir(deltas_dir):
                    file_path = os.path.join(deltas_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        count += 1
                print(f"Cleared deltas directory: {deltas_dir}")
                self.parent_app.update_status(f"Cleared {count} files from deltas directory.", LYRN_SUCCESS)
            except Exception as e:
                print(f"Error clearing deltas directory: {e}")
                self.parent_app.update_status("Error clearing deltas directory.", LYRN_ERROR)

    def clear_metrics_logs(self):
        """Clear metrics logs directory after confirmation."""
        from confirmation_dialog import ConfirmationDialog

        prefs = self.parent_app.settings_manager.ui_settings.get("confirmation_preferences", {})
        if prefs.get("clear_metrics_logs"):
            confirmed = True
        else:
            confirmed, dont_ask_again = ConfirmationDialog.show(
                self,
                self.theme_manager,
                title="Confirm Clear Directory",
                message="Are you sure you want to permanently delete all files in the metrics_logs directory?"
            )
            if dont_ask_again:
                prefs["clear_metrics_logs"] = True
                self.parent_app.settings_manager.ui_settings["confirmation_preferences"] = prefs
                self.parent_app.settings_manager.save_settings()

        if not confirmed:
            self.parent_app.update_status("Clear metrics logs cancelled.", LYRN_INFO)
            return

        metrics_dir = os.path.join(SCRIPT_DIR, "metrics_logs")
        if os.path.exists(metrics_dir):
            try:
                count = 0
                for filename in os.listdir(metrics_dir):
                    file_path = os.path.join(metrics_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        count += 1
                print(f"Cleared metrics logs: {metrics_dir}")
                self.parent_app.update_status(f"Cleared {count} files from metrics logs.", LYRN_SUCCESS)
            except Exception as e:
                print(f"Error clearing metrics logs: {e}")
                self.parent_app.update_status("Error clearing metrics logs.", LYRN_ERROR)

    def reload_model_full(self):
        """Trigger full model reload in parent"""
        if hasattr(self.parent_app, 'reload_model_full'):
            self.parent_app.reload_model_full()

    def force_memory_cleanup(self):
        """Force memory cleanup"""
        if hasattr(self.parent_app, 'force_memory_cleanup'):
            self.parent_app.force_memory_cleanup()

    def export_system_info(self):
        """Export system information"""
        try:
            info_dir = os.path.join(SCRIPT_DIR, "system_info")
            os.makedirs(info_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            info_file = os.path.join(info_dir, f"system_info_{timestamp}.txt")

            with open(info_file, 'w', encoding='utf-8') as f:
                f.write("LYRN-AI System Information\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write("="*50 + "\n\n")
                f.write(f"Python Version: {sys.version}\n")
                f.write(f"CustomTkinter Version: {ctk.__version__}\n")
                f.write(f"Script Directory: {SCRIPT_DIR}\n")
                # Add more system info as needed

            print(f"System info exported to: {info_file}")

        except Exception as e:
            print(f"Error exporting system info: {e}")

    def test_model_performance(self):
        """Test model performance"""
        if hasattr(self.parent_app, 'test_model_performance'):
            self.parent_app.test_model_performance()

    def validate_directories(self):
        """Validate all configured directories"""
        if not self.settings_manager.settings:
            print("No settings to validate")
            return

        paths = self.settings_manager.settings.get("paths", {})
        missing_dirs = []

        for key, path in paths.items():
            if path and not os.path.exists(path):
                missing_dirs.append(f"{key}: {path}")

        if missing_dirs:
            print("Missing directories:")
            for missing in missing_dirs:
                print(f"  - {missing}")
        else:
            print("All directories validated successfully")

    def save_all_settings(self):
        """Save all settings from all tabs"""
        try:
            if not self.settings_manager.settings:
                self.settings_manager.settings = self.settings_manager.create_empty_settings_structure()

            settings = self.settings_manager.settings.copy()

            # Model settings are managed in the main UI now.

            # Save paths
            for key, entry in self.path_entries.items():
                settings["paths"][key] = entry.get()

            # Update UI setting from checkbox
            self.settings_manager.ui_settings["show_model_selector"] = self.show_model_selector_var.get()
            self.settings_manager.ui_settings["autoload_model"] = self.autoload_model_var.get()
            self.settings_manager.ui_settings["llm_log_visible"] = self.llm_log_visible_var.get()
            self.settings_manager.ui_settings["llm_log_on_top"] = self.llm_log_on_top_var.get()
            self.settings_manager.ui_settings["language"] = self.language_var.get()
            self.settings_manager.ui_settings["terminal_start_path"] = self.terminal_start_path_entry.get()


            # Save Chat settings
            self.settings_manager.ui_settings["save_chat_history"] = self.save_chat_history_var.get()
            self.settings_manager.ui_settings["chat_history_length"] = int(self.history_length_entry.get())
            self.settings_manager.ui_settings["enable_deltas"] = self.enable_deltas_var.get()
            self.settings_manager.ui_settings["enable_chat_history"] = self.enable_chat_history_var.get()

            # Save Appearance settings
            self.settings_manager.ui_settings["show_thinking_text"] = self.show_thinking_var.get()
            new_chat_colors = {key: widgets['entry'].get() for key, widgets in self.color_setting_widgets.items()}
            self.settings_manager.ui_settings["chat_colors"] = new_chat_colors


            # Save all settings
            self.settings_manager.save_settings(settings)

            print("All settings saved successfully")
            self.destroy()

        except Exception as e:
            print(f"Error saving settings: {e}")


class DeltaFormatPopup(ThemedPopup):
    """A popup to edit the format strings for personality deltas."""
    def __init__(self, parent, theme_manager: ThemeManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.parent_popup = parent
        self.title("Edit Delta Formats")
        self.geometry("600x500")
        self.grab_set()

        self.format_entries = {}
        self.personality_data = self.parent_popup.personality_data

        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(expand=True, fill="both", padx=15, pady=15)

        ctk.CTkLabel(main_frame, text="Define the format for each delta. Use *value* as a placeholder for the slider's value.", wraplength=550).pack(pady=(0, 10))

        for trait_name in self.personality_data.get("snapshot", {}).keys():
            frame = ctk.CTkFrame(main_frame)
            frame.pack(fill="x", pady=5)
            ctk.CTkLabel(frame, text=trait_name.capitalize(), width=120).pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame)
            entry.pack(side="left", expand=True, fill="x", padx=5)
            entry.insert(0, self.personality_data.get("formats", {}).get(trait_name, ""))
            self.format_entries[trait_name] = entry

        save_button = ctk.CTkButton(self, text="Save Formats", command=self.save_formats)
        save_button.pack(pady=10)

        self.apply_theme()

    def save_formats(self):
        """Saves the updated format strings back to personality.json."""
        if "formats" not in self.personality_data:
            self.personality_data["formats"] = {}

        for trait_name, entry in self.format_entries.items():
            self.personality_data["formats"][trait_name] = entry.get()

        self.parent_popup._save_personality_data()
        self.parent_popup.parent_app.update_status("Delta formats saved successfully.", LYRN_SUCCESS)
        self.destroy()

class PersonalityPopup(ThemedPopup):
    """A popup window for editing personality traits with sliders."""
    def __init__(self, parent, theme_manager: ThemeManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.parent_app = parent
        self.title("Personality Editor")
        self.geometry("500x600")

        self.personality_file = Path(SCRIPT_DIR) / "personality.json"
        self.personality_data = self._load_personality_data()
        self.current_traits = self.personality_data.get("active_traits", {}).copy()

        self.personality_sliders = {}
        self.personality_labels = {}
        self.personality_preset_var = ctk.StringVar(value="")

        self.create_widgets()
        self.populate_personality_sliders()
        self.populate_personality_presets()
        self.apply_theme()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Saves the active traits when the window is closed."""
        self.personality_data["active_traits"] = self.current_traits
        self._save_personality_data()
        self.parent_app.update_status("Active personality traits saved.", LYRN_INFO)
        self.destroy()

    def create_widgets(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        preset_frame = ctk.CTkFrame(top_frame)
        preset_frame.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(preset_frame, text="Presets:").pack(side="left", padx=5)
        self.personality_preset_menu = ctk.CTkComboBox(preset_frame, variable=self.personality_preset_var, command=self.load_personality_preset)
        self.personality_preset_menu.pack(side="left", expand=True, fill="x", padx=5)

        edit_formats_button = ctk.CTkButton(top_frame, text="Edit Formats", command=self.open_format_editor)
        edit_formats_button.pack(side="right", padx=5)

        save_preset_button = ctk.CTkButton(top_frame, text="Save Preset", width=100, command=self.save_personality_preset)
        save_preset_button.pack(side="right", padx=5)

        help_button = ctk.CTkButton(top_frame, text="?", width=28, command=lambda: self.parent_app.show_help("personality_popup.main"))
        help_button.pack(side="right", padx=5)

        self.personality_main_frame = ctk.CTkScrollableFrame(self, label_text="Personality Snapshot")
        self.personality_main_frame.pack(expand=True, fill="both", padx=10, pady=0)

    def open_format_editor(self):
        """Opens the popup to edit delta formats."""
        popup = DeltaFormatPopup(self, self.theme_manager)
        popup.focus()

    def _load_personality_data(self):
        """Loads personality data from the JSON file."""
        if self.personality_file.exists():
            try:
                with open(self.personality_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading or parsing personality.json: {e}. Using default values.")
                # Return a structure that matches the new format
                return {"snapshot": {}, "formats": {}, "presets": {}, "active_traits": {}}
        else:
            # Create a default file if it doesn't exist
            print("Warning: personality.json not found. Creating with default values.")
            default_data = {
                "snapshot": {"creativity": 500, "consistency": 800, "verbosity": 400},
                "formats": {
                    "creativity": "personality.creativity = *value*",
                    "consistency": "personality.consistency = *value*",
                    "verbosity": "personality.verbosity = *value*"
                },
                "presets": {"default": {"traits": {"creativity": 500, "consistency": 800, "verbosity": 400}}},
                "active_traits": {"creativity": 500, "consistency": 800, "verbosity": 400}
            }
            self._save_personality_data(default_data)
            return default_data

    def save_personality_preset(self):
        """Saves the current active traits as a new preset."""
        dialog = ThemedInputDialog(self, self.theme_manager, text="Enter a name for the new preset:", title="Save Preset")
        preset_name = dialog.get_input()

        if preset_name and preset_name not in ["Custom"]:
            if "presets" not in self.personality_data:
                self.personality_data["presets"] = {}

            self.personality_data["presets"][preset_name] = {
                "description": "User-saved preset.",
                "traits": self.current_traits.copy()
            }
            self._save_personality_data()
            self.populate_personality_presets()
            self.personality_preset_var.set(preset_name)

    def _save_personality_data(self, data=None):
        """Saves the current personality data to the JSON file."""
        if data is None:
            data = self.personality_data
        try:
            with open(self.personality_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving personality file: {e}")

    def populate_personality_sliders(self):
        """Creates sliders based on the 'snapshot' keys."""
        for widget in self.personality_main_frame.winfo_children():
            widget.destroy()

        snapshot_traits = self.personality_data.get("snapshot", {})
        for trait, default_value in snapshot_traits.items():
            # Use the 'active_traits' value if it exists, otherwise the snapshot's default
            current_value = self.current_traits.get(trait, default_value)

            frame = ctk.CTkFrame(self.personality_main_frame)
            frame.pack(fill="x", pady=5, padx=5)

            label_text = f"{trait.capitalize()}: {current_value}"
            label = ctk.CTkLabel(frame, text=label_text, width=150, anchor="w")
            label.pack(side="left", padx=10)
            self.personality_labels[trait] = label

            slider = ctk.CTkSlider(frame, from_=0, to=1000, number_of_steps=1000,
                                   command=lambda v, t=trait: self._on_personality_slider_change(t, v))
            slider.set(current_value)
            slider.pack(side="left", expand=True, fill="x", padx=10)
            self.personality_sliders[trait] = slider

    def populate_personality_presets(self):
        """Populates the preset dropdown menu."""
        presets = list(self.personality_data.get("presets", {}).keys())
        self.personality_preset_menu.configure(values=["Custom"] + presets)
        self.personality_preset_var.set("Custom") # Default to custom

    def _on_personality_slider_change(self, trait_name: str, new_value: float):
        """Callback when a slider value changes, updates the label and the delta manifest."""
        int_value = int(new_value)
        self.personality_labels[trait_name].configure(text=f"{trait_name.capitalize()}: {int_value}")
        self.current_traits[trait_name] = int_value

        # Get the format string and create the simple delta
        format_string = self.personality_data.get("formats", {}).get(trait_name)
        if format_string:
            delta_str = format_string.replace("*value*", str(int_value))
            self.parent_app.delta_manager.update_simple_delta(trait_name, delta_str)
        else:
            print(f"Warning: No delta format found for trait '{trait_name}'.")

    def load_personality_preset(self, preset_name: str):
        """Loads a selected preset's traits into the active sliders."""
        if preset_name == "Custom":
            return

        preset_traits = self.personality_data.get("presets", {}).get(preset_name, {}).get("traits")
        if preset_traits:
            self.current_traits = preset_traits.copy()
            # Update all sliders and their corresponding deltas
            for trait, value in self.current_traits.items():
                if trait in self.personality_sliders:
                    self.personality_sliders[trait].set(value)
                    self._on_personality_slider_change(trait, value)
            self.parent_app.update_status(f"Loaded preset '{preset_name}'.", LYRN_INFO)


class JobInstructionViewerPopup(ThemedPopup):
    """A popup to view job instructions and provide an edit button."""
    def __init__(self, parent, theme_manager: ThemeManager, automation_controller: AutomationController, job_name: str, refresh_callback):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.automation_controller = automation_controller
        self.job_name = job_name
        self.refresh_callback = refresh_callback
        self.parent_app = parent.parent_app # Main application instance

        self.title(f"Instructions: {self.job_name}")
        self.geometry("500x400")

        job_info = self.automation_controller.job_definitions.get(self.job_name, {})
        instructions = job_info.get("instructions", "No instructions found for this job.")

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(main_frame, wrap="word")
        self.textbox.grid(row=0, column=0, sticky="nsew")
        self.textbox.insert("1.0", instructions)
        self.textbox.configure(state="disabled")

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, pady=(10, 0))

        edit_button = ctk.CTkButton(button_frame, text="Edit Job", command=self.edit_job)
        edit_button.pack(side="left", padx=(0, 10))

        close_button = ctk.CTkButton(button_frame, text="Close", command=self.destroy)
        close_button.pack(side="left")

        self.apply_theme()

    def edit_job(self):
        """Opens the JobBuilderPopup for the current job."""
        # This will be fully implemented in the next step. For now, it just closes this popup.
        self.destroy()
        # The logic to open JobBuilderPopup will be added in step 4.
        popup = JobBuilderPopup(
            parent=self.parent_app.prompt_builder_popup, # The parent should be the prompt builder
            automation_controller=self.automation_controller,
            theme_manager=self.theme_manager,
            language_manager=self.parent_app.language_manager,
            refresh_callback=self.refresh_callback,
            job_name=self.job_name
        )
        popup.focus()


class ComponentBuilderPopup(ThemedPopup):
    """A popup for creating and editing prompt components."""
    def __init__(self, parent, theme_manager: ThemeManager, language_manager: LanguageManager, refresh_callback, component_name: Optional[str] = None):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.language_manager = language_manager
        self.refresh_callback = refresh_callback
        self.editing_component_name = component_name
        self.parent_app = parent.parent_app if hasattr(parent, 'parent_app') else parent # Handle different parent types

        # This will hold the widgets for each element added
        self.element_widgets = []

        self.title("Component Builder")
        self.geometry("700x600")
        self.grab_set()

        self.create_widgets()

        if self.editing_component_name:
            self.load_component_data()

        # Add default elements for a new component
        if not self.editing_component_name:
            self.add_textbox_element(name="begin_bracket", content="###_START###")
            self.add_textbox_element(name="end_bracket", content="###_END###")
            self.add_textbox_element(name="rwi_text", content="")
            self.add_textbox_element(name="main_content", content="")


        self.apply_theme()

    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=15, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Top frame for name and buttons
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0,10))
        ctk.CTkLabel(top_frame, text="Component Name:").pack(side="left", padx=(0,5))
        self.component_name_entry = ctk.CTkEntry(top_frame)
        self.component_name_entry.pack(side="left", expand=True, fill="x", pady=(0, 10))
        if self.editing_component_name:
            self.component_name_entry.insert(0, self.editing_component_name)
            self.component_name_entry.configure(state="disabled")

        # Frame to hold the elements
        self.elements_frame = ctk.CTkScrollableFrame(main_frame, label_text="Component Elements")
        self.elements_frame.grid(row=1, column=0, sticky="nsew")

        # Bottom frame for controls
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=15, pady=10)

        add_element_button = ctk.CTkButton(bottom_frame, text="Add Text Box Element", command=self.add_textbox_element)
        add_element_button.pack(side="left", padx=5)

        # Save Button
        save_button = ctk.CTkButton(bottom_frame, text="Save Component", command=self.save_component)
        save_button.pack(side="right", padx=5)

    def add_textbox_element(self, name="", content=""):
        element_frame = ctk.CTkFrame(self.elements_frame, border_width=1)
        element_frame.pack(fill="x", pady=5, padx=5)
        element_frame.grid_columnconfigure(1, weight=1)

        # Top bar with name and delete button
        top_bar = ctk.CTkFrame(element_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(top_bar, text="Element Name:").pack(side="left")
        name_entry = ctk.CTkEntry(top_bar)
        name_entry.pack(side="left", expand=True, fill="x", padx=5)
        name_entry.insert(0, name)

        delete_button = ctk.CTkButton(top_bar, text="🗑️", width=30, command=lambda: self.delete_element(element_frame))
        delete_button.pack(side="right")

        # Content textbox
        ctk.CTkLabel(element_frame, text="Content:").grid(row=1, column=0, sticky="w", padx=5)
        content_box = ctk.CTkTextbox(element_frame, height=100, wrap="word", undo=True)
        content_box.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        content_box.insert("1.0", content)

        # Store widgets for later retrieval
        widget_data = {"frame": element_frame, "name_entry": name_entry, "content_box": content_box}
        self.element_widgets.append(widget_data)
        self.apply_theme()

    def delete_element(self, element_frame):
        # Find the widget data associated with the frame
        widget_to_remove = None
        for widget_data in self.element_widgets:
            if widget_data["frame"] == element_frame:
                widget_to_remove = widget_data
                break

        if widget_to_remove:
            self.element_widgets.remove(widget_to_remove)
            element_frame.destroy()

    def load_component_data(self):
        # This will be implemented in a later step.
        build_prompt_dir = Path(SCRIPT_DIR) / "build_prompt"
        component_dir = build_prompt_dir / self.editing_component_name
        config_path = component_dir / "config.json"

        config = self.parent_app.snapshot_loader._load_json_file(str(config_path)) or {}

        # Clear any default elements
        for element in self.element_widgets.copy():
            self.delete_element(element['frame'])

        # Add elements from config
        self.add_textbox_element("begin_bracket", config.get("begin_bracket", ""))
        self.add_textbox_element("end_bracket", config.get("end_bracket", ""))
        self.add_textbox_element("rwi_text", config.get("rwi_text", ""))

        content_file = config.get("content_file", f"{self.editing_component_name}.txt")
        content_path = component_dir / content_file
        content = ""
        if content_path.exists():
            content = content_path.read_text(encoding='utf-8')
        self.add_textbox_element("main_content", content)


    def save_component(self):
        # This will be implemented in a later step.
        self.parent_app.save_component_from_builder(self)
        if self.refresh_callback:
            self.refresh_callback()
        self.destroy()

class SystemPromptBuilderPopup(ThemedPopup):
    """A popup window for building and managing the system prompt with a two-panel interface."""
    def __init__(self, parent, theme_manager: ThemeManager, language_manager: LanguageManager, snapshot_loader: SnapshotLoader):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.parent_app = parent # To call parent methods like update_status
        self.language_manager = language_manager
        self.snapshot_loader = snapshot_loader
        self.build_prompt_dir = Path(SCRIPT_DIR) / "build_prompt"
        self.config_path = self.build_prompt_dir / "builder_config.json"
        self.components_path = self.build_prompt_dir / "components.json"

        self.title("System Prompt Builder")
        self.geometry("1200x700")
        self.minsize(800, 600)

        self.on_top_var = ctk.BooleanVar(value=False)
        self.config = self._load_json(self.config_path)

        # This will hold the widgets for the currently displayed editor
        self.editor_widgets = {}
        self.editor_frames = {} # Cache for editor frames

        self.create_widgets()
        self._initialize_editor_panels() # Pre-load all editors
        self.toggle_on_top() # Set initial state
        self.apply_theme()

    def _load_json(self, path: Path) -> dict:
        """Loads a JSON file by delegating to the snapshot_loader."""
        if not path:
            return {}
        # Ensure the path is a string, as the underlying method expects it.
        return self.snapshot_loader._load_json_file(str(path)) or {}

    def _save_json(self, path: Path, data: dict):
        """Saves data to a JSON file."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving {path}: {e}")

    def _load_text(self, path: Path) -> str:
        """Loads a text file."""
        if path.exists():
            try:
                return path.read_text(encoding='utf-8')
            except IOError as e:
                print(f"Error loading {path}: {e}")
        return ""

    def _save_text(self, path: Path, content: str):
        """Saves content to a text file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        except IOError as e:
            print(f"Error saving {path}: {e}")

    def create_widgets(self):
        """Create the new two-panel interface."""
        # --- Top Bar ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 0))

        rebuild_prompt_button = ctk.CTkButton(top_frame, text="Rebuild Master Prompt", command=self.parent_app.refresh_prompt_from_mode)
        rebuild_prompt_button.pack(side="left", padx=5, pady=5)

        view_prompt_button = ctk.CTkButton(top_frame, text="View Final Prompt", command=self._view_final_prompt)
        view_prompt_button.pack(side="left", padx=5, pady=5)

        on_top_checkbox = ctk.CTkCheckBox(top_frame, text="Keep on Top", variable=self.on_top_var, command=self.toggle_on_top)
        on_top_checkbox.pack(side="right", padx=5, pady=5)

        self.master_prompt_lock_var = ctk.BooleanVar(value=self.config.get("master_prompt_locked", False))
        lock_checkbox = ctk.CTkCheckBox(top_frame, text="Lock Master Prompt", variable=self.master_prompt_lock_var, command=self.toggle_master_prompt_lock)
        lock_checkbox.pack(side="right", padx=10, pady=5)

        help_button = ctk.CTkButton(top_frame, text="?", width=30, command=lambda: self.parent_app.show_help("prompt_builder_popup.main"))
        help_button.pack(side="right", padx=(5, 10), pady=5)

        # --- Main Content Frame ---
        main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_content_frame.grid_columnconfigure(0, weight=1)  # Left panel (component list)
        main_content_frame.grid_columnconfigure(1, weight=3)  # Right panel (editor)
        main_content_frame.grid_rowconfigure(0, weight=1)

        # --- Left Panel: Component List ---
        left_panel = ctk.CTkFrame(main_content_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_panel.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=0) # For arrow buttons
        left_panel.grid_columnconfigure(1, weight=1) # For the list

        self.prompt_order_list = DraggableListbox(
            left_panel,
            command=self.save_prompt_order,
            theme_manager=self.theme_manager,
            parent_popup=self,
            toggle_command=self.toggle_component
        )
        self.prompt_order_list.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.update_prompt_order_list()

        # --- Arrow buttons for reordering ---
        arrow_button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        arrow_button_frame.grid(row=0, column=0, sticky="ns", pady=5)

        up_button = ctk.CTkButton(arrow_button_frame, text="▲", width=30, command=self.prompt_order_list.move_item_up)
        up_button.pack(padx=5, pady=5)

        down_button = ctk.CTkButton(arrow_button_frame, text="▼", width=30, command=self.prompt_order_list.move_item_down)
        down_button.pack(padx=5, pady=5)

        add_button = ctk.CTkButton(arrow_button_frame, text="+", width=30, command=lambda: self.open_component_builder())
        add_button.pack(padx=5, pady=(15,5))

        delete_button = ctk.CTkButton(arrow_button_frame, text="-", width=30, command=self._delete_selected_component)
        delete_button.pack(padx=5, pady=5)

        edit_button = ctk.CTkButton(arrow_button_frame, text="✏️", width=30, command=self._edit_selected_component)
        edit_button.pack(padx=5, pady=5)


        # --- Right Panel: Editor Area ---
        self.editor_panel = ctk.CTkFrame(main_content_frame)
        self.editor_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.editor_panel.grid_rowconfigure(0, weight=1)
        self.editor_panel.grid_columnconfigure(0, weight=1)


        # Placeholder Label
        self.editor_placeholder = ctk.CTkLabel(self.editor_panel, text="Select a component from the left to edit its properties.")
        self.editor_placeholder.grid(row=0, column=0, sticky="nsew")


    def _initialize_editor_panels(self):
        """Creates all editor panels at startup and hides them."""
        self.editor_placeholder.grid_remove()

        components = self._load_json(self.components_path) or []

        all_component_names = [c['name'] for c in components if c.get('active', True)]
        if 'RWI' not in all_component_names:
            all_component_names.insert(0, 'RWI')

        # Use a set to ensure unique component names, preserving order
        unique_component_names = list(dict.fromkeys(all_component_names))

        for comp_name in unique_component_names:
            editor_frame = ctk.CTkFrame(self.editor_panel, fg_color="transparent")

            widgets = {}
            if comp_name == "RWI":
                widgets = self._create_rwi_viewer(editor_frame)
            elif comp_name == "personality":
                widgets = self._create_personality_editor(editor_frame)
            elif comp_name == "jobs":
                widgets = self._create_jobs_editor(editor_frame)
            elif comp_name == "oss_tools":
                widgets = self._create_oss_tools_editor(editor_frame)
            else:
                # Ensure the component exists before creating an editor for it
                if any(c['name'] == comp_name for c in components):
                    widgets = self._create_generic_editor(editor_frame, comp_name)
                else:
                    continue # Skip if component is not in components.json (e.g. inactive)

            self.editor_frames[comp_name] = editor_frame
            self.editor_widgets[comp_name] = widgets

            editor_frame.grid(row=0, column=0, sticky="nsew")
            editor_frame.grid_remove()

        self.apply_theme()


    def populate_editor_panel(self, component_name: str):
        """Shows the pre-loaded editor panel for the selected component."""
        for frame in self.editor_frames.values():
            frame.grid_remove()

        if component_name in self.editor_frames:
            frame = self.editor_frames[component_name]
            frame.grid()
        else:
            self.editor_placeholder.grid()

    def _create_generic_editor(self, parent_frame, component_name: str):
        """Creates the standard editor UI for a generic component and returns its widgets."""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(1, weight=1)

        component_dir = self.build_prompt_dir / component_name
        config_path = component_dir / "config.json"
        config = self._load_json(config_path) or {}
        content_filename = config.get("content_file", f"{component_name}.txt")
        content_path = component_dir / content_filename
        content = self._load_text(content_path)

        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top_bar, text=f"Editor: {component_name}", font=ctk.CTkFont(weight="bold")).pack(side="left")
        button_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        button_frame.pack(side="right")
        view_button = ctk.CTkButton(button_frame, text="View File", command=lambda p=content_path, name=component_name, cfg=config: self._view_file_with_brackets(f"View: {name}", p, cfg))
        view_button.pack(side="left", padx=5)
        save_button = ctk.CTkButton(button_frame, text="Save", command=lambda name=component_name: self._save_generic_config(name))
        save_button.pack(side="left", padx=5)

        main_frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main_frame, text="Start Bracket:").pack(anchor="w", padx=10, pady=(5, 0))
        start_bracket_entry = ctk.CTkEntry(main_frame)
        start_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        start_bracket_entry.insert(0, config.get("begin_bracket", ""))

        ctk.CTkLabel(main_frame, text="End Bracket:").pack(anchor="w", padx=10, pady=(5, 0))
        end_bracket_entry = ctk.CTkEntry(main_frame)
        end_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        end_bracket_entry.insert(0, config.get("end_bracket", ""))

        ctk.CTkLabel(main_frame, text="RWI Info:").pack(anchor="w", padx=10, pady=(5, 0))
        rwi_info_box = ctk.CTkTextbox(main_frame, height=100, undo=True)
        rwi_info_box.pack(fill="x", padx=10, pady=(0, 10), expand=True)
        rwi_info_box.insert("1.0", config.get("rwi_text", ""))

        ctk.CTkLabel(main_frame, text="Content/Prompt:").pack(anchor="w", padx=10, pady=(5, 0))
        content_textbox = ctk.CTkTextbox(main_frame, wrap="word", undo=True)
        content_textbox.pack(fill="both", padx=10, pady=(0, 10), expand=True)
        content_textbox.insert("1.0", content)

        return {
            "start_bracket_entry": start_bracket_entry,
            "end_bracket_entry": end_bracket_entry,
            "rwi_info_box": rwi_info_box,
            "content_textbox": content_textbox,
            "config": config,
            "content_path": content_path
        }

    def _save_generic_config(self, component_name):
        """Saves the data from the generic editor."""
        if component_name not in self.editor_widgets:
            return

        w = self.editor_widgets[component_name]
        config = w["config"]
        config["begin_bracket"] = w["start_bracket_entry"].get()
        config["end_bracket"] = w["end_bracket_entry"].get()
        config["rwi_text"] = w["rwi_info_box"].get("1.0", "end-1c")

        component_dir = self.build_prompt_dir / component_name
        config_path = component_dir / "config.json"
        self._save_json(config_path, config)

        content = w["content_textbox"].get("1.0", "end-1c")
        self._save_text(w["content_path"], content)

        self.parent_app.update_status(f"Saved '{component_name}' successfully.", LYRN_SUCCESS)

    def _create_rwi_viewer(self, parent_frame):
        """Creates the editor for the RWI intro text and brackets."""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(1, weight=1)

        config_path = self.build_prompt_dir / "rwi_config.json"
        config = self._load_json(config_path) or {}
        intro_path = self.build_prompt_dir / "rwi_intro.txt"
        intro_content = self._load_text(intro_path)

        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top_bar, text="Editor: RWI", font=ctk.CTkFont(weight="bold")).pack(side="left")
        button_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        button_frame.pack(side="right")
        view_button = ctk.CTkButton(button_frame, text="View Full RWI", command=self._view_rwi_content)
        view_button.pack(side="left", padx=5)
        save_button = ctk.CTkButton(button_frame, text="Save", command=self._save_rwi_config)
        save_button.pack(side="left", padx=5)

        main_frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main_frame, text="Start Bracket:").pack(anchor="w", padx=10, pady=(5,0))
        start_bracket_entry = ctk.CTkEntry(main_frame)
        start_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        start_bracket_entry.insert(0, config.get("begin_bracket", ""))

        ctk.CTkLabel(main_frame, text="End Bracket:").pack(anchor="w", padx=10, pady=(5,0))
        end_bracket_entry = ctk.CTkEntry(main_frame)
        end_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        end_bracket_entry.insert(0, config.get("end_bracket", ""))

        ctk.CTkLabel(main_frame, text="RWI Introduction for LLM:").pack(anchor="w", padx=10, pady=(5,0))
        intro_textbox = ctk.CTkTextbox(main_frame, wrap="word", undo=True)
        intro_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        intro_textbox.insert("1.0", intro_content)

        return {
            "start_bracket_entry": start_bracket_entry,
            "end_bracket_entry": end_bracket_entry,
            "intro_textbox": intro_textbox,
            "config_path": config_path,
            "intro_path": intro_path
        }

    def _save_rwi_config(self):
        """Saves the RWI configuration."""
        if "RWI" not in self.editor_widgets:
            return

        w = self.editor_widgets["RWI"]
        config_data = { "begin_bracket": w["start_bracket_entry"].get(), "end_bracket": w["end_bracket_entry"].get() }
        self._save_json(w["config_path"], config_data)
        intro_content = w["intro_textbox"].get("1.0", "end-1c")
        self._save_text(w["intro_path"], intro_content)
        self.parent_app.update_status("RWI settings saved.", LYRN_SUCCESS)

    def _view_rwi_content(self):
        """Constructs and displays the full RWI block content."""
        components = self._load_json(self.components_path) or []
        active_components = [c for c in components if c.get('active', True)]
        rwi_parts = []
        rwi_intro = self._load_text(self.build_prompt_dir / "rwi_intro.txt")
        for component in active_components:
            component_name = component['name']
            if component_name == "RWI": continue
            config = self._load_json(self.build_prompt_dir / component_name / "config.json")
            if config and config.get("rwi_text"):
                rwi_parts.append(f"---\n{component_name.upper()}:\n{config['rwi_text']}")
        full_rwi_content = "\n\n".join([rwi_intro] + rwi_parts if rwi_intro else rwi_parts)
        config = self._load_json(self.build_prompt_dir / "rwi_config.json") or {}
        self._view_file_with_brackets("Full RWI Content Preview", full_rwi_content, config, is_content_str=True)

    def _create_personality_editor(self, parent_frame):
        """Creates the editor UI for the personality component."""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(1, weight=1)
        config_path = self.build_prompt_dir / "personality" / "config.json"
        config = self._load_json(config_path) or {}
        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top_bar, text="Editor: Personality", font=ctk.CTkFont(weight="bold")).pack(side="left")
        button_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        button_frame.pack(side="right")
        output_filename = config.get("output_file", "personality.txt")
        output_path = self.build_prompt_dir / "personality" / output_filename
        view_button = ctk.CTkButton(button_frame, text="View File", command=lambda p=output_path, cfg=config: self._view_file_with_brackets("View: personality.txt", p, cfg))
        view_button.pack(side="left", padx=5)
        save_button = ctk.CTkButton(button_frame, text="Save", command=self._save_personality_config)
        save_button.pack(side="left", padx=5)
        main_frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(main_frame, text="Begin Bracket:").pack(anchor="w", padx=10, pady=(5,0))
        begin_bracket_entry = ctk.CTkEntry(main_frame)
        begin_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        begin_bracket_entry.insert(0, config.get("begin_bracket", ""))
        ctk.CTkLabel(main_frame, text="End Bracket:").pack(anchor="w", padx=10, pady=(5,0))
        end_bracket_entry = ctk.CTkEntry(main_frame)
        end_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        end_bracket_entry.insert(0, config.get("end_bracket", ""))
        ctk.CTkLabel(main_frame, text="RWI Info:").pack(anchor="w", padx=10, pady=(5,0))
        rwi_info_box = ctk.CTkTextbox(main_frame, height=100, undo=True)
        rwi_info_box.pack(fill="x", expand=True, padx=10, pady=(0, 10))
        rwi_info_box.insert("1.0", config.get("rwi_text", ""))
        traits_frame = ctk.CTkFrame(main_frame)
        traits_frame.pack(fill="x", expand=True, pady=10, padx=10)
        traits_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(traits_frame, text="Traits", font=ctk.CTkFont(weight="bold")).pack(pady=(0,5))
        trait_widgets = []
        for trait_data in config.get("traits", []):
            trait_container = ctk.CTkFrame(traits_frame)
            trait_container.pack(fill="x", pady=5, padx=5)
            trait_container.grid_columnconfigure(0, weight=1)
            name, value, instructions = trait_data.get("name", "Unknown"), trait_data.get("value", "500"), trait_data.get("instructions", "")
            name_value_frame = ctk.CTkFrame(trait_container, fg_color="transparent")
            name_value_frame.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(name_value_frame, text=f"{name}:").pack(side="left", padx=(0,5))
            value_entry = ctk.CTkEntry(name_value_frame, width=80)
            value_entry.insert("0", str(value))
            value_entry.pack(side="left")
            ctk.CTkLabel(trait_container, text="Instructions:").pack(anchor="w")
            instructions_box = ctk.CTkTextbox(trait_container, height=60, wrap="word", undo=True)
            instructions_box.insert("1.0", instructions)
            instructions_box.pack(fill="x", expand=True)
            trait_widgets.append({"name": name, "value_entry": value_entry, "instructions_box": instructions_box})
        return {"begin_bracket_entry": begin_bracket_entry, "end_bracket_entry": end_bracket_entry, "rwi_info_box": rwi_info_box, "trait_widgets": trait_widgets, "config": config}

    def _save_personality_config(self):
        """Saves the personality configuration from the editor."""
        if "personality" not in self.editor_widgets: return
        w = self.editor_widgets["personality"]
        config = w["config"]
        config["begin_bracket"] = w["begin_bracket_entry"].get()
        config["end_bracket"] = w["end_bracket_entry"].get()
        config["rwi_text"] = w["rwi_info_box"].get("1.0", "end-1c")
        updated_traits = []
        for item in w['trait_widgets']:
            try:
                updated_traits.append({"name": item["name"], "value": int(item["value_entry"].get()), "instructions": item["instructions_box"].get("1.0", "end-1c")})
            except ValueError:
                self.parent_app.update_status(f"Invalid value for {item['name']}. Must be an integer.", LYRN_ERROR)
                return
        config["traits"] = updated_traits
        self._save_json(self.build_prompt_dir / "personality" / "config.json", config)
        output_path = self.build_prompt_dir / "personality" / config.get("output_file", "personality.txt")
        output_parts = [f'"{t["name"]} = {t["value"]:04d}"\n"{t["instructions"]}"' for t in updated_traits]
        self._save_text(output_path, "\n\n".join(output_parts))
        self.parent_app.update_status("Personality settings saved.", LYRN_SUCCESS)

    def _create_jobs_editor(self, parent_frame):
        """Creates the UI for the jobs component editor."""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(1, weight=1)

        # --- Config Path ---
        config_path = self.build_prompt_dir / "jobs" / "config.json"
        config = self._load_json(config_path) or {}

        # --- Top Bar ---
        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        ctk.CTkLabel(top_bar, text="Editor: Jobs", font=ctk.CTkFont(weight="bold")).pack(side="left")

        button_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        button_frame.pack(side="right")

        view_button = ctk.CTkButton(button_frame, text="View Merged Jobs", command=self._view_merged_jobs)
        view_button.pack(side="left", padx=5)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self._save_jobs_config)
        save_button.pack(side="left", padx=5)

        refresh_button = ctk.CTkButton(button_frame, text="Refresh", command=self._refresh_jobs_list)
        refresh_button.pack(side="left", padx=5)


        # --- Main Content ---
        main_frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)

        # --- General Settings ---
        ctk.CTkLabel(main_frame, text="Jobs Section Instructions:").pack(anchor="w", padx=10, pady=(5,0))
        instructions_textbox = ctk.CTkTextbox(main_frame, height=100, undo=True)
        instructions_textbox.pack(fill="x", padx=10, pady=(0, 10), expand=True)
        instructions_textbox.insert("1.0", config.get("instructions", ""))

        ctk.CTkLabel(main_frame, text="RWI Info:").pack(anchor="w", padx=10, pady=(5, 0))
        rwi_info_box = ctk.CTkTextbox(main_frame, height=100, undo=True)
        rwi_info_box.pack(fill="x", padx=10, pady=(0, 10), expand=True)
        rwi_info_box.insert("1.0", config.get("rwi_text", ""))

        ctk.CTkLabel(main_frame, text="Jobs Section Start Bracket:").pack(anchor="w", padx=10, pady=(5,0))
        section_start_bracket_entry = ctk.CTkEntry(main_frame)
        section_start_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        section_start_bracket_entry.insert(0, config.get("begin_bracket", ""))

        ctk.CTkLabel(main_frame, text="Jobs Section End Bracket:").pack(anchor="w", padx=10, pady=(5,0))
        section_end_bracket_entry = ctk.CTkEntry(main_frame)
        section_end_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        section_end_bracket_entry.insert(0, config.get("end_bracket", ""))

        ctk.CTkLabel(main_frame, text="Individual Job Start Bracket (*job_name*):").pack(anchor="w", padx=10, pady=(5,0))
        job_start_bracket_entry = ctk.CTkEntry(main_frame)
        job_start_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        job_start_bracket_entry.insert(0, config.get("job_begin_bracket", ""))

        ctk.CTkLabel(main_frame, text="Individual Job End Bracket (*job_name*):").pack(anchor="w", padx=10, pady=(5,0))
        job_end_bracket_entry = ctk.CTkEntry(main_frame)
        job_end_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        job_end_bracket_entry.insert(0, config.get("job_end_bracket", ""))

        # --- Job List ---
        self.jobs_list_frame = ctk.CTkScrollableFrame(main_frame, label_text="Available Jobs")
        self.jobs_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._refresh_jobs_list()

        return {
            "instructions_textbox": instructions_textbox,
            "rwi_info_box": rwi_info_box,
            "section_start_bracket_entry": section_start_bracket_entry,
            "section_end_bracket_entry": section_end_bracket_entry,
            "job_start_bracket_entry": job_start_bracket_entry,
            "job_end_bracket_entry": job_end_bracket_entry,
            "config_path": config_path,
        }

    def _save_jobs_config(self):
        """Saves the jobs configuration."""
        if "jobs" not in self.editor_widgets:
            return

        w = self.editor_widgets["jobs"]
        config_data = {
            "instructions": w["instructions_textbox"].get("1.0", "end-1c"),
            "rwi_text": w["rwi_info_box"].get("1.0", "end-1c"),
            "begin_bracket": w["section_start_bracket_entry"].get(),
            "end_bracket": w["section_end_bracket_entry"].get(),
            "job_begin_bracket": w["job_start_bracket_entry"].get(),
            "job_end_bracket": w["job_end_bracket_entry"].get(),
        }
        self._save_json(w["config_path"], config_data)
        self.parent_app.update_status("Jobs settings saved.", LYRN_SUCCESS)

    def _view_merged_jobs(self):
        """Constructs and displays the full jobs block content."""
        if "jobs" not in self.editor_widgets:
            return

        w = self.editor_widgets["jobs"]
        config_path = self.build_prompt_dir / "jobs" / "config.json"
        config = self._load_json(config_path) or {}

        all_jobs = self.parent_app.automation_controller.job_definitions
        if not all_jobs:
            self.parent_app.update_status("No jobs found to merge.", LYRN_WARNING)
            return

        job_instructions_parts = []
        job_begin_bracket = config.get("job_begin_bracket", "")
        job_end_bracket = config.get("job_end_bracket", "")

        for job_name, job_data in all_jobs.items():
            instruction = job_data.get("instructions", "")

            start_bracket = job_begin_bracket.replace("*job_name*", job_name)
            end_bracket = job_end_bracket.replace("*job_name*", job_name)

            job_instructions_parts.append(f"{start_bracket}\n{instruction}\n{end_bracket}")

        full_jobs_content = ("\n\n" + "="*20 + " JOB SEPARATOR " + "="*20 + "\n\n").join(job_instructions_parts)

        # Add the main instructions if they exist
        main_instructions = config.get("instructions", "")
        if main_instructions:
            full_jobs_content = f"{main_instructions}\n\n{full_jobs_content}"

        self._view_file_with_brackets("Merged Jobs Preview", full_jobs_content, config, is_content_str=True)

    def _refresh_jobs_list(self):
        """Clears and repopulates the list of jobs."""
        for widget in self.jobs_list_frame.winfo_children():
            widget.destroy()

        job_definitions = self.parent_app.automation_controller.job_definitions
        if not job_definitions:
            ctk.CTkLabel(self.jobs_list_frame, text="No jobs found.").pack(pady=10)
            return

        for job_name in sorted(job_definitions.keys()):
            # Using a frame for each job to potentially add more info later
            job_frame = ctk.CTkFrame(self.jobs_list_frame, fg_color="transparent")
            job_frame.pack(fill="x", pady=2, padx=5)

            job_button = ctk.CTkButton(
                job_frame,
                text=job_name,
                anchor="w",
                command=lambda name=job_name: self._view_job_instructions(name)
            )
            job_button.pack(side="left", expand=True, fill="x")

    def _save_oss_tools_config(self):
        """Saves the oss_tools configuration."""
        if "oss_tools" not in self.editor_widgets:
            return

        w = self.editor_widgets["oss_tools"]
        config_data = {
            "instructions": w["instructions_textbox"].get("1.0", "end-1c"),
            "rwi_text": w["rwi_info_box"].get("1.0", "end-1c"),
            "begin_bracket": w["section_start_bracket_entry"].get(),
            "end_bracket": w["section_end_bracket_entry"].get(),
            "tool_begin_bracket": w["tool_start_bracket_entry"].get(),
            "tool_end_bracket": w["tool_end_bracket_entry"].get(),
        }
        self._save_json(w["config_path"], config_data)
        self.parent_app.update_status("OSS Tools settings saved.", LYRN_SUCCESS)

    def _create_oss_tools_editor(self, parent_frame):
        """Creates the UI for the oss_tools component editor."""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(1, weight=1)

        config_path = self.build_prompt_dir / "oss_tools" / "config.json"
        config = self._load_json(config_path) or {}

        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        ctk.CTkLabel(top_bar, text="Editor: OSS Tools", font=ctk.CTkFont(weight="bold")).pack(side="left")

        button_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        button_frame.pack(side="right")

        view_button = ctk.CTkButton(button_frame, text="View Merged Tools", command=self._view_merged_oss_tools)
        view_button.pack(side="left", padx=5)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self._save_oss_tools_config)
        save_button.pack(side="left", padx=5)

        refresh_button = ctk.CTkButton(button_frame, text="Refresh", command=self._refresh_oss_tools_list)
        refresh_button.pack(side="left", padx=5)

        main_frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main_frame, text="Tools Section Instructions:").pack(anchor="w", padx=10, pady=(5,0))
        instructions_textbox = ctk.CTkTextbox(main_frame, height=100, undo=True)
        instructions_textbox.pack(fill="x", padx=10, pady=(0, 10), expand=True)
        instructions_textbox.insert("1.0", config.get("instructions", ""))

        ctk.CTkLabel(main_frame, text="RWI Info:").pack(anchor="w", padx=10, pady=(5, 0))
        rwi_info_box = ctk.CTkTextbox(main_frame, height=100, undo=True)
        rwi_info_box.pack(fill="x", padx=10, pady=(0, 10), expand=True)
        rwi_info_box.insert("1.0", config.get("rwi_text", ""))

        ctk.CTkLabel(main_frame, text="Tools Section Start Bracket:").pack(anchor="w", padx=10, pady=(5,0))
        section_start_bracket_entry = ctk.CTkEntry(main_frame)
        section_start_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        section_start_bracket_entry.insert(0, config.get("begin_bracket", ""))

        ctk.CTkLabel(main_frame, text="Tools Section End Bracket:").pack(anchor="w", padx=10, pady=(5,0))
        section_end_bracket_entry = ctk.CTkEntry(main_frame)
        section_end_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        section_end_bracket_entry.insert(0, config.get("end_bracket", ""))

        ctk.CTkLabel(main_frame, text="Individual Tool Start Bracket (*tool_name*):").pack(anchor="w", padx=10, pady=(5,0))
        tool_start_bracket_entry = ctk.CTkEntry(main_frame)
        tool_start_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        tool_start_bracket_entry.insert(0, config.get("tool_begin_bracket", ""))

        ctk.CTkLabel(main_frame, text="Individual Tool End Bracket (*tool_name*):").pack(anchor="w", padx=10, pady=(5,0))
        tool_end_bracket_entry = ctk.CTkEntry(main_frame)
        tool_end_bracket_entry.pack(fill="x", padx=10, pady=(0, 10))
        tool_end_bracket_entry.insert(0, config.get("tool_end_bracket", ""))

        self.oss_tools_list_frame = ctk.CTkScrollableFrame(main_frame, label_text="Available OSS Tools")
        self.oss_tools_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._refresh_oss_tools_list()

        return {
            "instructions_textbox": instructions_textbox,
            "rwi_info_box": rwi_info_box,
            "section_start_bracket_entry": section_start_bracket_entry,
            "section_end_bracket_entry": section_end_bracket_entry,
            "tool_start_bracket_entry": tool_start_bracket_entry,
            "tool_end_bracket_entry": tool_end_bracket_entry,
            "config_path": config_path,
        }

    def _refresh_oss_tools_list(self):
        """Clears and repopulates the list of tools."""
        if not hasattr(self, 'oss_tools_list_frame'): return
        for widget in self.oss_tools_list_frame.winfo_children():
            widget.destroy()

        all_tools = self.parent_app.oss_tool_manager.get_all_tools()
        if not all_tools:
            ctk.CTkLabel(self.oss_tools_list_frame, text="No tools found.").pack(pady=10)
            return

        for tool in sorted(all_tools, key=lambda a: a.name):
            tool_frame = ctk.CTkFrame(self.oss_tools_list_frame, fg_color="transparent")
            tool_frame.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(tool_frame, text=tool.name, anchor="w").pack(side="left", expand=True, fill="x")

    def _view_merged_oss_tools(self):
        """Constructs and displays the full oss_tools block content."""
        config_path = self.build_prompt_dir / "oss_tools" / "config.json"
        config = self._load_json(config_path) or {}

        all_tools = self.parent_app.oss_tool_manager.get_all_tools()
        if not all_tools:
            self.parent_app.update_status("No tools found to merge.", LYRN_WARNING)
            return

        tool_parts = []
        tool_begin_bracket = config.get("tool_begin_bracket", "")
        tool_end_bracket = config.get("tool_end_bracket", "")

        for tool in all_tools:
            definition = tool.params.get("definition", "")
            if not definition:
                continue

            start_bracket = tool_begin_bracket.replace("*tool_name*", tool.name)
            end_bracket = tool_end_bracket.replace("*tool_name*", tool.name)
            tool_parts.append(f"{start_bracket}\n{definition}\n{end_bracket}")

        full_tools_content = "\n\n".join(tool_parts)

        main_instructions = config.get("instructions", "")
        if main_instructions:
            full_tools_content = f"{main_instructions}\n\n{full_tools_content}"

        self._view_file_with_brackets("Merged OSS Tools Preview", full_tools_content, config, is_content_str=True)


    def _view_job_instructions(self, job_name: str):
        """Opens a popup to view the job's instructions."""
        job_info = self.parent_app.automation_controller.job_definitions.get(job_name)
        if not job_info:
            self.parent_app.update_status(f"Could not find job: {job_name}", LYRN_ERROR)
            return

        popup = JobInstructionViewerPopup(
            parent=self,
            theme_manager=self.theme_manager,
            automation_controller=self.parent_app.automation_controller,
            job_name=job_name,
            refresh_callback=self._refresh_jobs_list # Pass the refresh callback
        )
        popup.focus()


    def _view_file_with_brackets(self, title: str, content_source: Path or str, config: dict, is_content_str: bool = False):
        """
        Loads content and displays it wrapped in its configured brackets.
        Can accept either a filepath or a raw string as the content source.
        """
        try:
            popup = FileViewerPopup(
                parent=self,
                theme_manager=self.theme_manager,
                title=title,
                content_source=content_source,
                config=config,
                is_content_str=is_content_str
            )
            popup.focus()
        except Exception as e:
            self.parent_app.update_status(f"Error viewing file: {e}", LYRN_ERROR)
            source_info = "string content" if is_content_str else f"file {content_source}"
            print(f"Error viewing {source_info}: {e}")

    def _view_final_prompt(self):
        """Builds the current master prompt and displays it in a viewer."""
        self.parent_app.update_status("Building final prompt for preview...", LYRN_INFO)
        prompt_content = self.snapshot_loader.build_master_prompt_from_components()

        if prompt_content:
            # Correctly instantiate FileViewerPopup
            popup = FileViewerPopup(
                parent=self,
                theme_manager=self.theme_manager,
                title="Final Prompt Preview",
                content_source=prompt_content,
                config={},  # No specific brackets for the whole prompt
                is_content_str=True
            )
            popup.focus()
            self.parent_app.update_status("Final prompt preview ready.", LYRN_SUCCESS)
        else:
            self.parent_app.update_status("Failed to build prompt. Check logs.", LYRN_ERROR)

    def update_prompt_order_list(self):
        """Populates the draggable list from components.json."""
        self.prompt_order_list.clear()
        components = self._load_json(self.components_path)
        if not isinstance(components, list):
            components = []
        if not any(c['name'] == 'RWI' for c in components):
            components.insert(0, {"name": "RWI", "order": -1, "active": True})

        sorted_components = sorted(components, key=lambda x: x.get('order', 99))
        for comp in sorted_components:
            self.prompt_order_list.add_item({
                "path": comp["name"],
                "active": comp.get("active", True),
                "pinned": False # Pinning not implemented yet
            })

    def save_prompt_order(self, new_item_objects: Optional[List[dict]] = None):
        """Saves the new component order to components.json."""
        if new_item_objects is None:
            new_item_objects = self.prompt_order_list.get_item_objects()

        components = self._load_json(self.components_path)
        if not isinstance(components, list): components = []
        comp_map = {c['name']: c for c in components}

        updated_components = []
        for i, item in enumerate(new_item_objects):
            comp_name = item["path"]
            if comp_name in comp_map:
                existing_comp = comp_map[comp_name]
                existing_comp['order'] = i
                updated_components.append(existing_comp)
            else: # Add new component if not in file (e.g. RWI)
                updated_components.append({"name": comp_name, "order": i, "active": True})

        self._save_json(self.components_path, updated_components)
        self.parent_app.update_status("Component order saved.", LYRN_SUCCESS)

    def toggle_component(self, key: str, is_enabled: bool):
        """Updates a component's 'active' state in components.json."""
        components = self._load_json(self.components_path)
        if not isinstance(components, list): return
        for comp in components:
            if comp['name'] == key:
                comp['active'] = is_enabled
                break
        self._save_json(self.components_path, components)
        self.parent_app.update_status(f"{key.title()} {'enabled' if is_enabled else 'disabled'}", LYRN_INFO)
        self.parent_app.refresh_prompt_from_mode()
        self.update_prompt_order_list()
        self.apply_theme()

    def toggle_on_top(self):
        """Toggles the always-on-top status of the window."""
        self.attributes("-topmost", self.on_top_var.get())

    def toggle_master_prompt_lock(self):
        """Updates the lock status in the builder_config.json file."""
        self.config["master_prompt_locked"] = self.master_prompt_lock_var.get()
        self._save_json(self.config_path, self.config)
        status_msg = "Master Prompt is now LOCKED." if self.master_prompt_lock_var.get() else "Master Prompt is now UNLOCKED."
        color = LYRN_WARNING if self.master_prompt_lock_var.get() else LYRN_SUCCESS
        self.parent_app.update_status(status_msg, color)

    def update_personality_trait_value(self, trait_name: str, new_value: int):
        """Finds the entry for a trait and updates its value in the editor."""
        if self.editor_widgets.get("component_name") != "personality":
            return

        for trait_widget_set in self.editor_widgets.get('trait_widgets', []):
            if trait_widget_set["name"] == trait_name:
                entry = trait_widget_set["value_entry"]
                entry.delete(0, "end")
                entry.insert(0, str(new_value))
                break

    def open_component_builder(self, component_name: Optional[str] = None):
        """Opens the component builder popup, either for a new or existing component."""
        popup = ComponentBuilderPopup(
            parent=self,
            theme_manager=self.theme_manager,
            language_manager=self.language_manager,
            refresh_callback=self.update_prompt_order_list,
            component_name=component_name
        )
        popup.focus()

    def _delete_selected_component(self):
        selected_frame = self.prompt_order_list.get_selected_item()
        if not selected_frame:
            self.parent_app.update_status("No component selected to delete.", LYRN_WARNING)
            return

        item_data = self.prompt_order_list.item_map.get(selected_frame)
        if not item_data:
            return

        component_name = item_data.get("path")
        if component_name == "RWI":
            self.parent_app.update_status("The RWI component cannot be deleted.", LYRN_WARNING)
            return
        self.delete_component(component_name)

    def _edit_selected_component(self):
        selected_frame = self.prompt_order_list.get_selected_item()
        if not selected_frame:
            self.parent_app.update_status("No component selected to edit.", LYRN_WARNING)
            return

        item_data = self.prompt_order_list.item_map.get(selected_frame)
        if not item_data:
            return

        component_name = item_data.get("path")
        self.open_component_builder(component_name)

    def delete_component(self, component_name: str):
        # This will be implemented in Step 4
        from confirmation_dialog import ConfirmationDialog
        confirmed, _ = ConfirmationDialog.show(
            self,
            self.theme_manager,
            title="Confirm Deletion",
            message=f"Are you sure you want to permanently delete the component '{component_name}'?\nThis cannot be undone."
        )
        if confirmed:
            self.parent_app.delete_component_by_name(component_name)
            self.update_prompt_order_list()



class ThemeBuilderPopup(ThemedPopup):
    """A popup window for creating and editing themes."""
    def __init__(self, parent, theme_manager, language_manager):
        super().__init__(parent=parent.parent_app, theme_manager=theme_manager)
        self.language_manager = language_manager

        self.title("Theme Builder")
        self.geometry("800x750") # Increased height
        self.minsize(700, 600)   # Increased min height

        self.create_theme_builder_widgets()
        self.load_selected_theme(self.theme_manager.get_current_theme_name())
        self.preview_theme()
        self.apply_theme()

    def create_theme_builder_widgets(self):
        """Create the theme builder tab UI with a fixed layout and improved color pickers."""
        try:
            font = ctk.CTkFont(family="Consolas", size=12)
            title_font = ctk.CTkFont(family="Consolas", size=14, weight="bold")
        except:
            font = ("Consolas", 12)
            title_font = ("Consolas", 14, "bold")

        # Main frame for the builder
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1) # Left panel
        main_frame.grid_columnconfigure(1, weight=1) # Right panel
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Left Panel ---
        left_panel = ctk.CTkFrame(main_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_panel.grid_rowconfigure(2, weight=1) # Make color picker scroll area expand
        left_panel.grid_columnconfigure(0, weight=1)

        # --- Right Panel (Preview) ---
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # --- Theme Management (in left panel) ---
        manage_frame = ctk.CTkFrame(left_panel)
        manage_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        self.theme_selector_combo = ctk.CTkComboBox(manage_frame, values=self.theme_manager.get_theme_names(), command=self.load_selected_theme)
        self.theme_selector_combo.pack(side="left", expand=True, fill="x", padx=(0,5))
        delete_button = ctk.CTkButton(manage_frame, text="Delete", width=60, command=self.delete_selected_theme)
        delete_button.pack(side="left")

        # --- Theme Name (in left panel) ---
        name_frame = ctk.CTkFrame(left_panel)
        name_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(name_frame, text="Theme Name:", font=font).pack(side="left", padx=(0, 5))
        self.theme_name_entry = ctk.CTkEntry(name_frame, font=font)
        self.theme_name_entry.pack(side="left", expand=True, fill="x")

        # --- Color Pickers (Scrollable, in left panel) ---
        color_picker_frame = ctk.CTkScrollableFrame(left_panel, label_text="Color Settings")
        color_picker_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        self.color_widgets = {}
        color_labels = {
            "primary": "Primary", "accent": "Accent", "button_hover": "Button Hover",
            "frame_bg": "Frame Background", "border_color": "Border Color", "label_text": "Label Text",
            "textbox_fg": "Textbox Foreground", "display_text_color": "Display Text", "system_text": "System Text",
            "user_text": "User Text", "assistant_text": "Assistant Text", "thinking_text": "Thinking Text",
            "success": "Success", "warning": "Warning", "error": "Error", "info": "Info",
            "textbox_bg": "Textbox Background", "switch_progress": "Switch Progress (On)",
            "switch_button": "Switch Button", "switch_bg_off": "Switch Background (Off)",
            "progressbar_progress": "Progressbar Progress", "slider_progress": "Slider Progress",
            "slider_button": "Slider Button", "tab_selected": "Tab Selected", "tab_unselected": "Tab Unselected",
            "tab_selected_hover": "Tab Selected Hover", "tab_unselected_hover": "Tab Unselected Hover"
        }

        for key, label_text in color_labels.items():
            container = ctk.CTkFrame(color_picker_frame, fg_color="transparent")
            container.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(container, text=label_text, font=font, width=150, anchor="w").pack(side="left")
            hex_entry = ctk.CTkEntry(container, font=font, width=90)
            hex_entry.pack(side="left", padx=10)
            color_swatch = ctk.CTkFrame(container, width=28, height=28, border_width=1, cursor="hand2")
            color_swatch.pack(side="left", padx=5)

            hex_entry.bind("<KeyRelease>", lambda e, k=key: self.update_color_from_entry(k))
            color_swatch.bind("<Button-1>", lambda e, k=key: self.choose_color(k))
            self.color_widgets[key] = {'entry': hex_entry, 'swatch': color_swatch}

        # --- Buttons (Fixed at bottom of left panel) ---
        button_frame = ctk.CTkFrame(left_panel)
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        apply_theme_button = ctk.CTkButton(button_frame, text="Apply", font=font, command=self.apply_preview_theme)
        apply_theme_button.pack(side="left", expand=True, fill="x", padx=(0, 5))
        save_theme_button = ctk.CTkButton(button_frame, text="Save Theme", font=font, command=self.save_theme)
        save_theme_button.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # --- Preview Area (in right panel) ---
        self.preview_frame = ctk.CTkFrame(right_frame, border_width=2)
        self.preview_frame.pack(expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(self.preview_frame, text="Theme Preview", font=title_font).pack(pady=5)
        self.preview_widgets = {}
        self.preview_widgets["label"] = ctk.CTkLabel(self.preview_frame, text="This is a label.")
        self.preview_widgets["label"].pack(pady=5, padx=10)
        self.preview_widgets["button"] = ctk.CTkButton(self.preview_frame, text="Click Me")
        self.preview_widgets["button"].pack(pady=5, padx=10)
        self.preview_widgets["textbox"] = ctk.CTkTextbox(self.preview_frame, height=50)
        self.preview_widgets["textbox"].insert("0.0", "This is a textbox for longer text.\nIt can have multiple lines.")
        self.preview_widgets["textbox"].pack(pady=5, padx=10, fill="x")
        self.preview_widgets["combobox"] = ctk.CTkComboBox(self.preview_frame, values=["Option 1", "Option 2"])
        self.preview_widgets["combobox"].pack(pady=5, padx=10)
        self.preview_widgets["progressbar"] = ctk.CTkProgressBar(self.preview_frame)
        self.preview_widgets["progressbar"].set(0.7)
        self.preview_widgets["progressbar"].pack(pady=5, padx=10, fill="x")
        self.preview_widgets["switch"] = ctk.CTkSwitch(self.preview_frame, text="A switch")
        self.preview_widgets["switch"].pack(pady=5, padx=10)
        self.preview_widgets["switch"].select()

    def update_color_from_entry(self, key: str):
        """Updates the color preview swatch from the hex entry."""
        widget_set = self.color_widgets.get(key)
        if not widget_set: return
        hex_code = widget_set['entry'].get()
        if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_code):
            widget_set['swatch'].configure(fg_color=hex_code)
            self.preview_theme()
        else:
            widget_set['swatch'].configure(fg_color="gray") # Indicate invalid color

    def choose_color(self, key):
        """Opens a color chooser and updates the widgets for the given color key."""
        initial_color = self.color_widgets[key]['entry'].get()
        picker = CustomColorPickerPopup(self, initial_color=initial_color)
        new_color = picker.get_color()
        if new_color:
            self.color_widgets[key]['entry'].delete(0, "end")
            self.color_widgets[key]['entry'].insert(0, new_color)
            self.color_widgets[key]['swatch'].configure(fg_color=new_color)
            self.preview_theme()

    def apply_preview_theme(self):
        """Applies the current settings in the theme builder for a live preview across all windows."""
        theme_name = self.theme_name_entry.get()
        if not theme_name:
            self.parent_app.update_status("Please enter a theme name to apply a preview.", LYRN_WARNING)
            return

        preview_colors = {key: widgets['entry'].get() for key, widgets in self.color_widgets.items()}
        self.theme_manager.current_theme_name = f"{theme_name} (Preview)"
        self.theme_manager.current_colors = preview_colors

        self.parent_app.apply_color_theme()
        for widget in self.parent_app.winfo_children():
            if isinstance(widget, ctk.CTkToplevel) and hasattr(widget, 'apply_theme'):
                try:
                    widget.apply_theme()
                except Exception as e:
                    print(f"Could not apply theme to {widget}: {e}")
        self.apply_theme()
        self.parent_app.update_status(f"Previewing theme: {theme_name}", LYRN_INFO)

    def preview_theme(self):
        """Updates the advanced preview area with the current colors."""
        colors = {key: widgets['entry'].get() for key, widgets in self.color_widgets.items()}
        primary = colors.get("primary", "#007BFF")
        accent = colors.get("accent", "#28A745")
        frame_bg = colors.get("frame_bg", "#F8F9FA")
        textbox_bg = colors.get("textbox_bg", "#FFFFFF")
        textbox_fg = colors.get("textbox_fg", "#212529")
        label_text = colors.get("label_text", "#495057")
        border = colors.get("border_color", "#DEE2E6")
        button_text_color = colors.get("textbox_bg", "#FFFFFF")
        switch_progress = colors.get("switch_progress", accent)
        switch_button = colors.get("switch_button", primary)
        progressbar_progress = colors.get("progressbar_progress", primary)
        self.preview_frame.configure(fg_color=frame_bg, border_color=accent)
        self.preview_widgets["label"].configure(text_color=label_text)
        self.preview_widgets["button"].configure(fg_color=primary, text_color=button_text_color)
        self.preview_widgets["textbox"].configure(fg_color=textbox_bg, text_color=textbox_fg, border_color=border)
        self.preview_widgets["combobox"].configure(fg_color=textbox_bg, text_color=textbox_fg, border_color=border, button_color=primary)
        self.preview_widgets["progressbar"].configure(progress_color=progressbar_progress)
        self.preview_widgets["switch"].configure(progress_color=switch_progress, button_color=switch_button, text_color=label_text)

    def load_selected_theme(self, theme_name: str):
        """Loads a theme's properties into the editor fields."""
        if not theme_name or theme_name not in self.theme_manager.themes:
            return
        theme_data = self.theme_manager.themes[theme_name]
        self.theme_name_entry.delete(0, "end")
        self.theme_name_entry.insert(0, theme_data.get("name", ""))
        theme_colors = theme_data.get("colors", {})
        for key, widgets in self.color_widgets.items():
            color = theme_colors.get(key, "#ffffff")
            widgets['entry'].delete(0, "end")
            widgets['entry'].insert(0, color)
            widgets['swatch'].configure(fg_color=color, border_color=theme_colors.get("border_color", "#ffffff"))
        self.preview_theme()
        self.parent_app.update_status(f"Loaded '{theme_name}' for editing", LYRN_INFO)

    def delete_selected_theme(self):
        """Deletes the currently selected theme after confirmation."""
        from confirmation_dialog import ConfirmationDialog
        theme_name = self.theme_selector_combo.get()
        if not theme_name or theme_name not in self.theme_manager.themes:
            return
        prefs = self.parent_app.settings_manager.ui_settings.get("confirmation_preferences", {})
        if prefs.get("delete_theme"):
            confirmed = True
        else:
            confirmed, dont_ask_again = ConfirmationDialog.show(self, self.theme_manager, title="Confirm Deletion", message=f"Are you sure you want to permanently delete the theme '{theme_name}'?")
            if dont_ask_again:
                prefs["delete_theme"] = True
                self.parent_app.settings_manager.ui_settings["confirmation_preferences"] = prefs
                self.parent_app.settings_manager.save_settings()
        if not confirmed:
            self.parent_app.update_status("Theme deletion cancelled", LYRN_WARNING)
            return
        filename = f"{theme_name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.theme_manager.themes_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                self.theme_manager.load_available_themes()
                new_theme_names = self.theme_manager.get_theme_names()
                self.theme_selector_combo.configure(values=new_theme_names)
                self.parent_app.theme_dropdown.configure(values=new_theme_names)
                safe_theme = new_theme_names[0] if new_theme_names else "LYRN Dark"
                self.theme_selector_combo.set(safe_theme)
                self.parent_app.theme_dropdown.set(safe_theme)
                self.parent_app.on_theme_selected(safe_theme)
                self.parent_app.update_status(f"Theme '{theme_name}' deleted", LYRN_SUCCESS)
            except Exception as e:
                self.parent_app.update_status(f"Error deleting theme: {e}", LYRN_ERROR)
        else:
            self.parent_app.update_status(f"Theme file not found for '{theme_name}'", LYRN_ERROR)

    def save_theme(self):
        """Saves the current theme to a JSON file."""
        theme_name = self.theme_name_entry.get()
        if not theme_name:
            return
        theme_data = {
            "name": theme_name,
            "appearance_mode": "dark",
            "colors": {key: widgets['entry'].get() for key, widgets in self.color_widgets.items()}
        }
        themes_dir = os.path.join(self.parent_app.SCRIPT_DIR, "themes")
        os.makedirs(themes_dir, exist_ok=True)
        filename = f"{theme_name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(themes_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=4)
            self.parent_app.theme_manager.load_available_themes()
            new_theme_names = self.parent_app.theme_manager.get_theme_names()
            self.parent_app.theme_dropdown.configure(values=new_theme_names)
            self.theme_selector_combo.configure(values=new_theme_names)
            self.parent_app.theme_dropdown.set(theme_name)
            self.theme_selector_combo.set(theme_name)
            self.parent_app.update_status(f"Theme '{theme_name}' saved", LYRN_SUCCESS)
        except Exception as e:
            print(f"Error saving theme: {e}")
            self.parent_app.update_status("Error saving theme", LYRN_ERROR)


class ComingSoonPopup(ThemedPopup):
    """A simple popup to inform the user that a feature is not yet available."""
    def __init__(self, parent, theme_manager):
        super().__init__(parent=parent, theme_manager=theme_manager)

        self.title("Coming Soon")
        self.geometry("300x150")
        self.grab_set() # Make it modal

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        message_label = ctk.CTkLabel(
            main_frame,
            text="This feature is unfinished and will be coming soon.",
            wraplength=260,
            justify="center"
        )
        message_label.pack(expand=True)

        ok_button = ctk.CTkButton(main_frame, text="OK", command=self.destroy)
        ok_button.pack(pady=(10, 0))

        self.apply_theme()


class DaySchedulePopup(ThemedPopup):
    """A popup to manage schedules for a specific day."""
    def __init__(self, parent, theme_manager, language_manager, scheduler_manager, automation_controller: AutomationController, date_obj: datetime, calendar_refresh_callback):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.language_manager = language_manager
        self.scheduler_manager = scheduler_manager
        self.automation_controller = automation_controller
        self.date_obj = date_obj
        self.calendar_refresh_callback = calendar_refresh_callback
        self.selected_schedule_id = None

        self.title(f"Schedules for {self.date_obj.strftime('%Y-%m-%d')}")
        self.geometry("700x500")
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left pane for existing schedules
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        self.schedule_list_frame = ctk.CTkScrollableFrame(left_frame, label_text=f"Scheduled Jobs")
        self.schedule_list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        delete_button = ctk.CTkButton(left_frame, text="Delete Selected", command=self.delete_schedule)
        delete_button.grid(row=1, column=0, padx=5, pady=10)

        # Right pane for adding new schedules
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(right_frame, text="Add New Schedule").pack(pady=5)

        # Job selection
        ctk.CTkLabel(right_frame, text="Job:").pack(anchor="w", padx=10)
        job_names = list(self.automation_controller.job_definitions.keys())
        self.job_selector = ctk.CTkComboBox(right_frame, values=job_names if job_names else ["No jobs available"])
        if job_names:
            self.job_selector.set(job_names[0])
        self.job_selector.pack(fill="x", padx=10, pady=(0, 10))

        # Time inputs
        time_frame = ctk.CTkFrame(right_frame)
        time_frame.pack(fill="x", padx=10, pady=10)

        self.time_entries = {}
        for unit in ["Hour", "Minute", "Second"]:
            ctk.CTkLabel(time_frame, text=unit).pack(side="left", padx=5)
            entry = ctk.CTkEntry(time_frame, width=60)
            entry.pack(side="left", padx=5)
            self.time_entries[unit] = entry

        schedule_button = ctk.CTkButton(right_frame, text="Schedule Job", command=self.schedule_job)
        schedule_button.pack(pady=20)

        self.refresh_schedule_list()
        self.apply_theme()

    def refresh_schedule_list(self):
        for widget in self.schedule_list_frame.winfo_children():
            widget.destroy()

        self.selected_schedule_id = None
        all_schedules = self.scheduler_manager.get_all_schedules()
        day_schedules = [s for s in all_schedules if s.scheduled_datetime.date() == self.date_obj.date()]

        if not day_schedules:
            ctk.CTkLabel(self.schedule_list_frame, text="No jobs scheduled for this day.").pack()
            return

        for schedule in sorted(day_schedules, key=lambda s: s.scheduled_datetime):
            time_str = schedule.scheduled_datetime.strftime('%H:%M:%S.%f')[:-3]
            label_text = f"{time_str} - {schedule.job_name}"
            label = ctk.CTkLabel(self.schedule_list_frame, text=label_text, anchor="w", cursor="hand2")
            label.pack(fill="x", padx=5, pady=2)
            label.bind("<Button-1>", lambda e, s_id=schedule.id, l=label: self.on_schedule_selected(s_id, l))

    def on_schedule_selected(self, schedule_id: str, selected_label: ctk.CTkLabel):
        self.selected_schedule_id = schedule_id
        for child in self.schedule_list_frame.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(fg_color="transparent")
        selected_label.configure(fg_color=self.theme_manager.get_color("accent"))

    def schedule_job(self):
        job_name = self.job_selector.get()
        if "No jobs available" in job_name:
            # Show error
            return

        try:
            hour = int(self.time_entries["Hour"].get() or 0)
            minute = int(self.time_entries["Minute"].get() or 0)
            second = int(self.time_entries["Second"].get() or 0)

            scheduled_dt = self.date_obj.replace(hour=hour, minute=minute, second=second, microsecond=0)

            self.scheduler_manager.add_schedule(job_name, scheduled_dt)
            self.refresh_schedule_list()
            self.calendar_refresh_callback()

        except ValueError:
            # Show error popup for invalid time
            print("Invalid time format")
            pass

    def delete_schedule(self):
        if not self.selected_schedule_id:
            # Show error
            return

        self.scheduler_manager.delete_schedule(self.selected_schedule_id)
        self.refresh_schedule_list()
        self.calendar_refresh_callback()


class JobBuilderPopup(ThemedPopup):
    """A popup for creating and editing jobs."""
    def __init__(self, parent, automation_controller: AutomationController, theme_manager: ThemeManager, language_manager: LanguageManager, refresh_callback, job_name: Optional[str] = None):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.automation_controller = automation_controller
        self.language_manager = language_manager
        self.refresh_callback = refresh_callback
        self.editing_job_name = job_name

        # This needs to be fixed in the next step. It currently gets a string, but will get a dict.
        job_definition = self.automation_controller.job_definitions.get(self.editing_job_name) if self.editing_job_name else {}
        if isinstance(job_definition, str): # Temp backwards compatibility
            self.job_data = {"instructions": job_definition, "trigger": ""}
        else:
            self.job_data = job_definition or {}


        self.title("Job Editor" if self.editing_job_name else "Create New Job")
        self.geometry("700x600")
        self.grab_set()

        self.create_widgets()
        if self.job_data:
            self.load_job_data()

        self.apply_theme()

    def create_widgets(self):
        """Create the UI elements for the popup."""
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        main_frame.grid_columnconfigure(0, weight=1)

        # Job Name
        ctk.CTkLabel(main_frame, text="Job Name").pack(anchor="w")
        self.job_name_entry = ctk.CTkEntry(main_frame)
        self.job_name_entry.pack(fill="x", pady=(0, 10))
        if self.editing_job_name:
            self.job_name_entry.insert(0, self.editing_job_name)
            self.job_name_entry.configure(state="disabled")

        # Job Instructions
        ctk.CTkLabel(main_frame, text="Job Instructions (for build_prompt)").pack(anchor="w")
        self.job_instructions_text = ctk.CTkTextbox(main_frame, height=200, undo=True)
        self.job_instructions_text.pack(fill="both", pady=(0, 10), expand=True)

        # Trigger Prompt
        ctk.CTkLabel(main_frame, text="Trigger Prompt (for LLM execution)").pack(anchor="w")
        self.trigger_prompt_text = ctk.CTkTextbox(main_frame, height=100, undo=True)
        self.trigger_prompt_text.pack(fill="both", pady=(0, 10), expand=True)

        # Save Button
        save_button = ctk.CTkButton(self, text="Save Job", command=self.save_job)
        save_button.pack(pady=15, padx=15)

    def load_job_data(self):
        """Populates the fields with data from an existing job."""
        if not self.job_data:
            return
        self.job_instructions_text.insert("1.0", self.job_data.get("instructions", ""))
        self.trigger_prompt_text.insert("1.0", self.job_data.get("trigger", ""))

    def save_job(self):
        """Saves the job data to the central jobs.json file."""
        job_name = self.job_name_entry.get().strip()
        instructions = self.job_instructions_text.get("1.0", "end-1c").strip()
        trigger = self.trigger_prompt_text.get("1.0", "end-1c").strip()

        if not all([job_name, instructions, trigger]):
            self.parent.parent_app.update_status("Job Name, Instructions, and Trigger must be filled.", LYRN_ERROR)
            return

        # Call the new method in the automation controller to handle saving.
        # This was the bug: The parent of the JobBuilderPopup is the JobInstructionViewerPopup,
        # and its parent is the SystemPromptBuilder. The main app is at parent.parent_app.
        main_app = self.parent.parent_app
        self.automation_controller.save_job_definition(job_name, instructions, trigger)

        main_app.update_status(f"Job '{job_name}' saved.", LYRN_SUCCESS)

        if self.refresh_callback:
            self.refresh_callback()

        self.destroy()

class JobWatcherPopup(ThemedPopup):
    """A popup window for managing watcher jobs."""
    def __init__(self, parent, automation_controller: AutomationController, theme_manager: ThemeManager, language_manager: LanguageManager, cycle_manager: CycleManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.automation_controller = automation_controller
        self.language_manager = language_manager
        self.cycle_manager = cycle_manager
        self.selected_job_name = None
        self.job_checkboxes = {}
        self.selected_cycle_name = None
        self.selected_trigger_name = None
        self.reflection_job_output = ""

        self.active_jobs_index_path = Path(SCRIPT_DIR) / "build_prompt" / "active_jobs" / "_index.json"
        self.active_jobs_dir = self.active_jobs_index_path.parent
        self._ensure_active_jobs_index()

        self.title("Automation")
        self.geometry("900x700")

        # Main tab view
        self.tabview = ctk.CTkTabview(self, width=850, height=600)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_viewer = self.tabview.add("Job Viewer")
        self.tab_scheduler = self.tabview.add("Scheduler")
        self.tab_reflection = self.tabview.add("Prompt Training")
        self.tab_cycle_builder = self.tabview.add("Cycle Builder")

        self.add_help_to_tab(self.tab_viewer, "job_watcher_popup.job_viewer")
        self.add_help_to_tab(self.tab_scheduler, "job_watcher_popup.scheduler")
        self.add_help_to_tab(self.tab_reflection, "job_watcher_popup.prompt_training")
        self.add_help_to_tab(self.tab_cycle_builder, "job_watcher_popup.cycle_builder")

        self.create_viewer_tab()
        self.create_scheduler_tab()
        self.create_reflection_tab()
        self.create_cycle_builder_tab()

        self.refresh_job_list()
        self.tabview.set("Job Viewer")
        self.apply_theme()

    def add_help_to_tab(self, tab_frame, help_code):
        """Adds a help button to the top-right corner of a tab frame."""
        help_button = ctk.CTkButton(
            tab_frame,
            text="?",
            width=28,
            height=28,
            command=lambda: self.parent_app.show_help(help_code)
        )
        help_button.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

    def create_viewer_tab(self):
        self.tab_viewer.grid_columnconfigure(0, weight=1)
        self.tab_viewer.grid_rowconfigure(0, weight=1)

        viewer_content_frame = ctk.CTkFrame(self.tab_viewer)
        viewer_content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        viewer_content_frame.grid_columnconfigure(0, weight=1)
        viewer_content_frame.grid_rowconfigure(0, weight=1)

        self.job_list_frame = ctk.CTkScrollableFrame(viewer_content_frame, label_text="Available Jobs")
        self.job_list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        button_frame = ctk.CTkFrame(viewer_content_frame)
        button_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

        new_button = ctk.CTkButton(button_frame, text="New Job", command=self.open_new_job_popup)
        new_button.pack(padx=10, pady=10, anchor="n")

        edit_button = ctk.CTkButton(button_frame, text="Edit", command=self.edit_selected_job)
        edit_button.pack(padx=10, pady=10, anchor="n")

        run_button = ctk.CTkButton(button_frame, text="Run", command=self.run_selected_job)
        run_button.pack(padx=10, pady=10, anchor="n")

        delete_button = ctk.CTkButton(button_frame, text="Delete", command=self.delete_selected_job)
        delete_button.pack(padx=10, pady=10, anchor="n")

    def open_new_job_popup(self):
        """Opens the job builder popup for creating a new job."""
        popup = JobBuilderPopup(
            parent=self,
            automation_controller=self.automation_controller,
            theme_manager=self.theme_manager,
            language_manager=self.language_manager,
            refresh_callback=self.refresh_job_list
        )
        popup.focus()

    def edit_selected_job(self):
        """Opens the job builder popup for editing the selected job."""
        if not self.selected_job_name:
            self.parent_app.update_status("No job selected to edit.", LYRN_WARNING)
            return

        popup = JobBuilderPopup(
            parent=self,
            automation_controller=self.automation_controller,
            theme_manager=self.theme_manager,
            language_manager=self.language_manager,
            refresh_callback=self.refresh_job_list,
            job_name=self.selected_job_name
        )
        popup.focus()

    def create_cycle_builder_tab(self):
        """Creates the UI for the Cycle Builder tab."""
        self.tab_cycle_builder.grid_columnconfigure(0, weight=1)
        self.tab_cycle_builder.grid_columnconfigure(1, weight=2)
        self.tab_cycle_builder.grid_rowconfigure(1, weight=1)

        # --- Left Pane: Cycle Management and Trigger List ---
        left_pane = ctk.CTkFrame(self.tab_cycle_builder)
        left_pane.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        left_pane.grid_rowconfigure(1, weight=1)
        left_pane.grid_columnconfigure(0, weight=1)

        # Cycle selection and management
        cycle_manage_frame = ctk.CTkFrame(left_pane)
        cycle_manage_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.cycle_selector = ctk.CTkComboBox(cycle_manage_frame, values=[], command=self.on_cycle_selected)
        self.cycle_selector.pack(side="left", expand=True, fill="x", padx=(0, 5))
        new_cycle_button = ctk.CTkButton(cycle_manage_frame, text="New", width=50, command=self.new_cycle)
        new_cycle_button.pack(side="left", padx=(0, 5))
        delete_cycle_button = ctk.CTkButton(cycle_manage_frame, text="Delete", width=60, command=self.delete_cycle)
        delete_cycle_button.pack(side="left")

        # Draggable list for triggers
        self.trigger_list = DraggableListbox(left_pane, command=self.on_trigger_list_reorder)
        self.trigger_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # --- Right Pane: Trigger Editor ---
        right_pane = ctk.CTkFrame(self.tab_cycle_builder)
        right_pane.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)
        right_pane.grid_rowconfigure(1, weight=1)
        right_pane.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_pane, text="Trigger Editor").grid(row=0, column=0, pady=5)

        editor_frame = ctk.CTkFrame(right_pane)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(editor_frame, text="Trigger Name:").pack(anchor="w", padx=5)
        self.trigger_name_entry = ctk.CTkEntry(editor_frame)
        self.trigger_name_entry.pack(fill="x", padx=5, pady=(0, 10))

        ctk.CTkLabel(editor_frame, text="Trigger Prompt:").pack(anchor="w", padx=5)
        self.trigger_prompt_text = ctk.CTkTextbox(editor_frame, wrap="word", undo=True)
        self.trigger_prompt_text.pack(expand=True, fill="both", padx=5, pady=(0, 10))

        # Buttons for the editor
        button_frame = ctk.CTkFrame(right_pane)
        button_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        add_trigger_button = ctk.CTkButton(button_frame, text="Add/Update Trigger", command=self.save_trigger)
        add_trigger_button.pack(side="left", padx=5)
        delete_trigger_button = ctk.CTkButton(button_frame, text="Delete Trigger", command=self.delete_trigger)
        delete_trigger_button.pack(side="right", padx=5)

        self.refresh_cycle_list()

    def refresh_cycle_list(self):
        """Refreshes the list of available cycles in the combobox."""
        cycle_names = self.cycle_manager.get_cycle_names()
        self.cycle_selector.configure(values=cycle_names if cycle_names else [""])
        if cycle_names:
            self.cycle_selector.set(cycle_names[0])
            self.on_cycle_selected(cycle_names[0])
        else:
            self.cycle_selector.set("")
            self.on_cycle_selected(None)

    def on_cycle_selected(self, cycle_name: Optional[str]):
        """Callback when a cycle is selected from the dropdown."""
        self.selected_cycle_name = cycle_name
        self.refresh_trigger_list()
        self.clear_trigger_editor()

    def refresh_trigger_list(self):
        """Refreshes the draggable list of triggers for the selected cycle."""
        self.trigger_list.clear()
        if self.selected_cycle_name:
            cycle_data = self.cycle_manager.get_cycle(self.selected_cycle_name)
            if cycle_data:
                for trigger in cycle_data.get("triggers", []):
                    # DraggableListbox expects a dict with a "path" key for the text
                    self.trigger_list.add_item({"path": trigger["name"], "pinned": False})

    def on_trigger_list_reorder(self, new_item_objects: List[dict]):
        """Saves the new order of triggers when the list is reordered."""
        if not self.selected_cycle_name:
            return

        cycle_data = self.cycle_manager.get_cycle(self.selected_cycle_name)
        if not cycle_data:
            return

        # Create a map of trigger names to their prompts to preserve them
        prompt_map = {t["name"]: t["prompt"] for t in cycle_data.get("triggers", [])}

        new_triggers = []
        for item in new_item_objects:
            trigger_name = item["path"]
            if trigger_name in prompt_map:
                new_triggers.append({"name": trigger_name, "prompt": prompt_map[trigger_name]})

        self.cycle_manager.update_cycle_triggers(self.selected_cycle_name, new_triggers)
        self.parent_app.update_status(f"Trigger order for '{self.selected_cycle_name}' saved.", LYRN_SUCCESS)

    def new_cycle(self):
        """Prompts for a new cycle name and creates it."""
        dialog = ctk.CTkInputDialog(text="Enter name for the new cycle:", title="New Cycle")
        name = dialog.get_input()
        if name:
            if self.cycle_manager.create_cycle(name):
                self.parent_app.update_status(f"Cycle '{name}' created.", LYRN_SUCCESS)
                self.refresh_cycle_list()
                self.cycle_selector.set(name)
            else:
                self.parent_app.update_status(f"Cycle '{name}' already exists.", LYRN_ERROR)

    def delete_cycle(self):
        """Deletes the selected cycle after confirmation."""
        if not self.selected_cycle_name:
            self.parent_app.update_status("No cycle selected to delete.", LYRN_WARNING)
            return

        from confirmation_dialog import ConfirmationDialog
        confirmed, _ = ConfirmationDialog.show(
            self, self.theme_manager,
            title="Confirm Deletion",
            message=f"Are you sure you want to permanently delete the cycle '{self.selected_cycle_name}'?"
        )
        if confirmed:
            self.cycle_manager.delete_cycle(self.selected_cycle_name)
            self.parent_app.update_status(f"Cycle '{self.selected_cycle_name}' deleted.", LYRN_SUCCESS)
            self.refresh_cycle_list()

    def save_trigger(self):
        """Saves the trigger from the editor to the selected cycle."""
        if not self.selected_cycle_name:
            self.parent_app.update_status("No cycle selected to add a trigger to.", LYRN_WARNING)
            return

        trigger_name = self.trigger_name_entry.get().strip()
        trigger_prompt = self.trigger_prompt_text.get("1.0", "end-1c").strip()

        if not trigger_name or not trigger_prompt:
            self.parent_app.update_status("Trigger name and prompt cannot be empty.", LYRN_ERROR)
            return

        self.cycle_manager.add_trigger_to_cycle(self.selected_cycle_name, trigger_name, trigger_prompt)
        self.parent_app.update_status(f"Trigger '{trigger_name}' saved to cycle '{self.selected_cycle_name}'.", LYRN_SUCCESS)
        self.refresh_trigger_list()
        self.clear_trigger_editor()

    def delete_trigger(self):
        """Deletes the selected trigger from the current cycle."""
        selected_item_frame = self.trigger_list.get_selected_item()
        if not selected_item_frame:
            self.parent_app.update_status("No trigger selected to delete.", LYRN_WARNING)
            return

        # The text is on a label which is a child of the frame
        trigger_name = selected_item_frame.winfo_children()[1].cget("text")

        from confirmation_dialog import ConfirmationDialog
        confirmed, _ = ConfirmationDialog.show(
            self, self.theme_manager,
            title="Confirm Deletion",
            message=f"Are you sure you want to delete the trigger '{trigger_name}' from this cycle?"
        )
        if confirmed:
            self.cycle_manager.delete_trigger_from_cycle(self.selected_cycle_name, trigger_name)
            self.parent_app.update_status(f"Trigger '{trigger_name}' deleted.", LYRN_SUCCESS)
            self.refresh_trigger_list()


    def clear_trigger_editor(self):
        """Clears the trigger name and prompt fields."""
        self.trigger_name_entry.delete(0, "end")
        self.trigger_prompt_text.delete("1.0", "end")

    def _ensure_active_jobs_index(self):
        """Ensures the active jobs directory and index file exist."""
        self.active_jobs_dir.mkdir(parents=True, exist_ok=True)
        if not self.active_jobs_index_path.exists():
            with open(self.active_jobs_index_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_active_jobs(self) -> List[str]:
        """Loads the list of active (pinned) job names from the index file."""
        if not self.active_jobs_index_path.exists():
            return []
        try:
            with open(self.active_jobs_index_path, 'r', encoding='utf-8') as f:
                # The index contains file paths, e.g., "active_jobs/some_job/instructions.txt"
                paths = json.load(f)
            job_names = []
            if isinstance(paths, list):
                for path_str in paths:
                    # Extract the job name, which is the directory name
                    parts = Path(path_str).parts
                    if len(parts) > 1:
                        job_names.append(parts[-2])
            return job_names
        except (json.JSONDecodeError, IOError):
            return []

    def toggle_job_pin(self, job_name: str):
        """Handles the logic when a job's pin checkbox is toggled."""
        is_active = self.job_checkboxes[job_name][1].get()
        active_jobs = self._load_active_jobs()

        if is_active:
            if job_name not in active_jobs:
                active_jobs.append(job_name)
        else:
            if job_name in active_jobs:
                active_jobs.remove(job_name)

        self.update_active_job_files(active_jobs)
        self.parent_app.update_status(f"Job '{job_name}' toggled {'on' if is_active else 'off'}.", LYRN_INFO)

    def update_active_job_files(self, active_job_names: List[str]):
        """
        Synchronizes the files in the build_prompt/active_jobs directory
        with the list of active jobs.
        """
        # Ensure the active jobs directory exists
        self.active_jobs_dir.mkdir(parents=True, exist_ok=True)

        # Remove files/dirs for jobs that are no longer active
        for item in self.active_jobs_dir.iterdir():
            if item.name == "_index.json":
                continue
            if item.is_dir() and item.name not in active_job_names:
                print(f"Removing inactive job directory: {item.name}")
                shutil.rmtree(item)

        # Add files for newly activated jobs
        for job_name in active_job_names:
            job_definition = self.automation_controller.job_definitions.get(job_name)
            if not job_definition:
                print(f"Warning: Could not find definition for active job '{job_name}'.")
                continue

            # Instructions are now in a dictionary
            instructions = job_definition.get("instructions", "")
            if not instructions:
                print(f"Warning: Job '{job_name}' has no instructions to write to build_prompt.")
                continue

            job_dir = self.active_jobs_dir / job_name
            job_dir.mkdir(exist_ok=True)

            instructions_path = job_dir / "instructions.txt"
            with open(instructions_path, 'w', encoding='utf-8') as f:
                f.write(instructions) # Write verbatim instructions as requested

        # Update the local index for the active_jobs directory
        active_job_files = []
        for job_name in active_job_names:
            # We assume the file is always named instructions.txt inside the job's folder
            relative_path = Path("active_jobs") / job_name / "instructions.txt"
            active_job_files.append(str(relative_path).replace("\\", "/"))

        local_index_path = self.active_jobs_dir / "_index.json"
        try:
            with open(local_index_path, 'w', encoding='utf-8') as f:
                json.dump(sorted(active_job_files), f, indent=2)
            print("Active jobs index updated.")
        except IOError as e:
            print(f"Error writing active jobs index: {e}")

        # Trigger a rebuild of the master prompt
        if hasattr(self.parent_app, 'snapshot_loader'):
            self.parent_app.snapshot_loader.build_master_prompt_from_components()

    def create_reflection_tab(self):
        """Creates the UI for the Reflection Cycle tab."""
        reflection_frame = ctk.CTkScrollableFrame(self.tab_reflection)
        reflection_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Job selection for reflection
        job_selection_frame = ctk.CTkFrame(reflection_frame, fg_color="transparent")
        job_selection_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(job_selection_frame, text="Job to Reflect On:").pack(anchor="w")
        job_names = list(self.automation_controller.job_definitions.keys())
        self.reflection_job_selector = ctk.CTkComboBox(job_selection_frame, values=job_names if job_names else ["No jobs available"])
        if job_names:
            self.reflection_job_selector.set(job_names[0])
        self.reflection_job_selector.pack(side="left", expand=True, fill="x")

        run_job_button = ctk.CTkButton(job_selection_frame, text="Run Job", command=self.run_job_for_reflection)
        run_job_button.pack(side="left", padx=5)

        # Reflection Instructions
        ctk.CTkLabel(reflection_frame, text="Reflection Instructions").pack(anchor="w")
        self.reflection_instructions_text = ctk.CTkTextbox(reflection_frame, height=100, undo=True)
        self.reflection_instructions_text.pack(fill="x", pady=(0, 10), expand=True)

        # Gold-Standard Example
        ctk.CTkLabel(reflection_frame, text="Gold-Standard Example").pack(anchor="w")
        self.reflection_gold_standard_text = ctk.CTkTextbox(reflection_frame, height=100, undo=True)
        self.reflection_gold_standard_text.pack(fill="x", pady=(0, 10), expand=True)

        # Reflection Iterations
        iterations_frame = ctk.CTkFrame(reflection_frame, fg_color="transparent")
        iterations_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(iterations_frame, text="Reflection Iterations:").pack(side="left")
        self.reflection_iterations_entry = ctk.CTkEntry(iterations_frame, width=50)
        self.reflection_iterations_entry.pack(side="left", padx=5)

        # Reflection Batch Size
        batch_size_frame = ctk.CTkFrame(reflection_frame, fg_color="transparent")
        batch_size_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(batch_size_frame, text="Reflect after N outputs:").pack(side="left")
        self.reflection_batch_size_entry = ctk.CTkEntry(batch_size_frame, width=50)
        self.reflection_batch_size_entry.pack(side="left", padx=5)

        # Checkboxes
        self.reflection_auto_update_prompt_var = ctk.BooleanVar()
        self.reflection_auto_continue_var = ctk.BooleanVar()

        auto_update_checkbox = ctk.CTkCheckBox(reflection_frame, text="Automatically update job prompt", variable=self.reflection_auto_update_prompt_var)
        auto_update_checkbox.pack(anchor="w", pady=5)

        auto_continue_checkbox = ctk.CTkCheckBox(reflection_frame, text="Auto-continue job after prompt update", variable=self.reflection_auto_continue_var)
        auto_continue_checkbox.pack(anchor="w", pady=5)

        # Manual Trigger Button
        manual_trigger_button = ctk.CTkButton(reflection_frame, text="Run Reflection Manually", command=self.run_reflection_manually)
        manual_trigger_button.pack(pady=20)

    def run_job_for_reflection(self):
        """Runs the selected job and stores its output for reflection."""
        selected_job_name = self.reflection_job_selector.get()
        if "No jobs available" in selected_job_name:
            self.parent_app.update_status("No job selected to run.", LYRN_WARNING)
            return

        trigger_prompt = self.automation_controller.get_job_trigger(selected_job_name)
        if not trigger_prompt:
            self.parent_app.update_status(f"Could not load trigger for job '{selected_job_name}'.", LYRN_ERROR)
            return

        self.parent_app.update_status(f"Running job '{selected_job_name}' for reflection...", LYRN_INFO)

        # This will block, which is ok for this button.
        response = self.parent_app.get_response_for_job(trigger_prompt)

        self.reflection_job_output = response

        self.parent_app.update_status(f"Job '{selected_job_name}' finished. Output is ready for reflection.", LYRN_SUCCESS)

    def run_reflection_manually(self):
        """Triggers the reflection process manually based on the UI settings."""
        instructions = self.reflection_instructions_text.get("1.0", "end-1c")
        gold_standard = self.reflection_gold_standard_text.get("1.0", "end-1c")
        iterations = self.reflection_iterations_entry.get()
        auto_update = self.reflection_auto_update_prompt_var.get()
        auto_continue = self.reflection_auto_continue_var.get()
        selected_job_for_reflection = self.reflection_job_selector.get()

        if not instructions:
            self.parent_app.update_status("Reflection instructions are required.", LYRN_WARNING)
            return

        if "No jobs available" in selected_job_for_reflection:
            self.parent_app.update_status("No job selected for reflection.", LYRN_WARNING)
            return

        job_output = self.reflection_job_output
        if not job_output.strip():
            self.parent_app.update_status("Job output is empty. Run a job first.", LYRN_WARNING)
            return

        # The 'reflection_cycle_job' expects these arguments.
        job_args = {
            "instructions": instructions,
            "gold_standard": gold_standard,
            "job_output": job_output,
            "iterations": iterations,
            "auto_update": auto_update,
            "auto_continue": auto_continue,
            "original_job_name": selected_job_for_reflection or "manual" # Track which job this reflection is for
        }

        # Add the reflection job to the queue
        self.parent_app.automation_controller.add_job(
            name="reflection_cycle_job",
            args=job_args
        )

        self.parent_app.update_status(f"Reflection job for '{job_args['original_job_name']}' added to the queue.", LYRN_SUCCESS)

    def create_scheduler_tab(self):
        """Creates the UI for the Scheduler tab."""
        self.current_date = datetime.now()

        # Main frame for the calendar
        calendar_frame = ctk.CTkFrame(self.tab_scheduler)
        calendar_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header for navigation
        header_frame = ctk.CTkFrame(calendar_frame)
        header_frame.pack(fill="x", pady=5)

        prev_month_button = ctk.CTkButton(header_frame, text="<", width=30, command=self.prev_month)
        prev_month_button.pack(side="left", padx=10)

        self.month_year_label = ctk.CTkLabel(header_frame, text="", font=("", 16, "bold"))
        self.month_year_label.pack(side="left", expand=True)

        next_month_button = ctk.CTkButton(header_frame, text=">", width=30, command=self.next_month)
        next_month_button.pack(side="right", padx=10)

        # Frame for the calendar grid
        self.grid_frame = ctk.CTkFrame(calendar_frame)
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.update_calendar()

    def update_calendar(self):
        """Renders the calendar for the current month and year."""
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        self.month_year_label.configure(text=self.current_date.strftime('%B %Y'))

        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdatescalendar(self.current_date.year, self.current_date.month)

        # Get theme colors
        tm = self.theme_manager
        label_text_color = tm.get_color("label_text")
        button_color = tm.get_color("primary")
        today_color = tm.get_color("info")
        other_month_color = tm.get_color("border_color")
        schedule_border_color = tm.get_color("success")

        # Day headers
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days):
            ctk.CTkLabel(self.grid_frame, text=day, font=("", 10, "bold"), text_color=label_text_color).grid(row=0, column=i, padx=1, pady=1)
            self.grid_frame.grid_columnconfigure(i, weight=1)

        # Get all schedules to check for highlights
        all_schedules = self.parent_app.scheduler_manager.get_all_schedules()
        scheduled_dates = {s.scheduled_datetime.date() for s in all_schedules}

        for r, week in enumerate(month_days):
            self.grid_frame.grid_rowconfigure(r + 1, weight=1)
            for c, date_obj in enumerate(week):
                is_today = (date_obj == datetime.now().date())
                has_schedule = date_obj in scheduled_dates

                day_button = ctk.CTkButton(
                    self.grid_frame,
                    text=str(date_obj.day),
                    command=lambda d=date_obj: self.open_day_schedule_popup(d)
                )

                # Set default button color
                day_button.configure(fg_color=button_color)

                if date_obj.month != self.current_date.month:
                    day_button.configure(fg_color=other_month_color)
                elif is_today:
                    day_button.configure(fg_color=today_color)

                if has_schedule:
                    day_button.configure(border_width=2, border_color=schedule_border_color)

                day_button.grid(row=r + 1, column=c, sticky="nsew", padx=1, pady=1)

    def prev_month(self):
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.update_calendar()

    def next_month(self):
        _, num_days = calendar.monthrange(self.current_date.year, self.current_date.month)
        self.current_date = self.current_date.replace(day=1) + timedelta(days=num_days)
        self.update_calendar()

    def open_day_schedule_popup(self, date_obj):
        """Opens the popup for managing a specific day's schedule."""
        # We need to pass a datetime object, not just a date
        dt_obj = datetime.combine(date_obj, datetime.min.time())

        popup = DaySchedulePopup(
            parent=self,
            theme_manager=self.theme_manager,
            language_manager=self.language_manager,
            scheduler_manager=self.parent_app.scheduler_manager,
            automation_controller=self.parent_app.automation_controller,
            date_obj=dt_obj,
            calendar_refresh_callback=self.update_calendar
        )
        popup.focus()

    def refresh_job_list(self):
        for widget in self.job_list_frame.winfo_children():
            widget.destroy()

        self.job_checkboxes.clear()
        active_jobs = self._load_active_jobs()
        all_jobs = self.automation_controller.job_definitions
        self.selected_job_name = None

        if not all_jobs:
            ctk.CTkLabel(self.job_list_frame, text="No watcher jobs created yet.").pack()
            return

        for job_name in sorted(all_jobs.keys()):
            var = ctk.BooleanVar(value=(job_name in active_jobs))

            # A frame to hold the checkbox and the selection label
            job_frame = ctk.CTkFrame(self.job_list_frame, fg_color="transparent")
            job_frame.pack(fill="x", padx=5, pady=2)

            checkbox = ctk.CTkCheckBox(
                job_frame,
                text=job_name,
                variable=var,
                command=lambda name=job_name: self.toggle_job_pin(name)
            )
            checkbox.pack(side="left")

            # We bind the selection for edit/delete to the frame itself
            job_frame.bind("<Button-1>", lambda e, name=job_name: self.on_job_selected(name))

            self.job_checkboxes[job_name] = (checkbox, var, job_frame)

    def on_job_selected(self, job_name):
        self.selected_job_name = job_name
        for name, (_, _, frame) in self.job_checkboxes.items():
            # Highlight the entire frame for selection
            if name == job_name:
                frame.configure(fg_color=self.theme_manager.get_color("accent"))
            else:
                frame.configure(fg_color="transparent")

    def run_selected_job(self):
        if not self.selected_job_name:
            self.parent_app.update_status("No job selected to run.", LYRN_WARNING)
            return

        trigger_prompt = self.automation_controller.get_job_trigger(self.selected_job_name)
        if trigger_prompt:
            # Directly execute the job instead of pasting it into the input box.
            self.parent_app.execute_job_directly(self.selected_job_name, trigger_prompt)
            self.parent_app.update_status(f"Executing job: {self.selected_job_name}", LYRN_ACCENT)
        else:
            self.parent_app.update_status(f"Could not load trigger for job '{self.selected_job_name}'.", LYRN_ERROR)

    def delete_selected_job(self):
        """Deletes the selected job after confirmation."""
        from confirmation_dialog import ConfirmationDialog

        if not self.selected_job_name:
            self.parent_app.update_status("No job selected to delete.", LYRN_WARNING)
            return

        job_name = self.selected_job_name

        prefs = self.parent_app.settings_manager.ui_settings.get("confirmation_preferences", {})
        if prefs.get("delete_watcher_job"):
            confirmed = True
        else:
            confirmed, dont_ask_again = ConfirmationDialog.show(
                self,
                self.theme_manager,
                title="Confirm Deletion",
                message=f"Are you sure you want to permanently delete the job '{job_name}'?"
            )
            if dont_ask_again:
                prefs["delete_watcher_job"] = True
                self.parent_app.settings_manager.ui_settings["confirmation_preferences"] = prefs
                self.parent_app.settings_manager.save_settings()

        if confirmed:
            try:
                self.automation_controller.delete_job_definition(job_name)
                self.parent_app.update_status(f"Job '{job_name}' deleted.", LYRN_SUCCESS)
                self.refresh_job_list()
            except Exception as e:
                self.parent_app.update_status(f"Error deleting job: {e}", LYRN_ERROR)
        else:
            self.parent_app.update_status("Deletion cancelled.", LYRN_INFO)

    def select_output_path(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_path_label.configure(text=path)


class OSSToolPopup(ThemedPopup):
    """A popup window for managing internal OSS Tools with a new text-based editor."""
    def __init__(self, parent, oss_tool_manager: OSSToolManager, theme_manager: ThemeManager, language_manager: LanguageManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.oss_tool_manager = oss_tool_manager
        self.language_manager = language_manager
        self.selected_tool_name = None
        self.editing_tool_name = None

        self.title("OSS Tool Editor")
        self.geometry("800x600")

        self.tabview = ctk.CTkTabview(self, width=750, height=500)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_viewer = self.tabview.add("Tool Viewer")
        self.tab_editor = self.tabview.add("Tool Editor")

        self.add_help_to_tab(self.tab_viewer, "oss_tool_popup.viewer")
        self.add_help_to_tab(self.tab_editor, "oss_tool_popup.editor")

        self.create_viewer_tab()
        self.create_editor_tab()

        self.refresh_tool_list()
        self.tabview.set("Tool Viewer")
        self.apply_theme()

    def add_help_to_tab(self, tab_frame, help_code):
        """Adds a help button to the top-right corner of a tab frame."""
        help_button = ctk.CTkButton(
            tab_frame,
            text="?",
            width=28,
            height=28,
            command=lambda: self.parent_app.show_help(help_code)
        )
        help_button.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

    def create_viewer_tab(self):
        self.tab_viewer.grid_columnconfigure(0, weight=1)
        self.tab_viewer.grid_rowconfigure(0, weight=1)

        viewer_content_frame = ctk.CTkFrame(self.tab_viewer)
        viewer_content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        viewer_content_frame.grid_columnconfigure(0, weight=1)
        viewer_content_frame.grid_rowconfigure(0, weight=1)

        self.tool_list_frame = ctk.CTkScrollableFrame(viewer_content_frame, label_text="Available Tools")
        self.tool_list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        button_frame = ctk.CTkFrame(viewer_content_frame)
        button_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

        edit_button = ctk.CTkButton(button_frame, text="Edit", command=self.edit_selected_tool)
        edit_button.pack(padx=10, pady=10, anchor="n")

        delete_button = ctk.CTkButton(button_frame, text="Delete", command=self.delete_selected_tool)
        delete_button.pack(padx=10, pady=10, anchor="n")

        new_button = ctk.CTkButton(button_frame, text="New", command=self.new_tool)
        new_button.pack(padx=10, pady=10, anchor="n")

    def refresh_tool_list(self):
        for widget in self.tool_list_frame.winfo_children():
            widget.destroy()

        all_tools = self.oss_tool_manager.get_all_tools()
        self.selected_tool_name = None

        if not all_tools:
            ctk.CTkLabel(self.tool_list_frame, text="No tools created yet.").pack()
            return

        for tool in sorted(all_tools, key=lambda a: a.name):
            label = ctk.CTkLabel(self.tool_list_frame, text=tool.name, anchor="w", cursor="hand2")
            label.pack(fill="x", padx=10, pady=2)
            label.bind("<Button-1>", lambda e, name=tool.name: self.on_tool_selected(name))

    def on_tool_selected(self, name):
        self.selected_tool_name = name
        for child in self.tool_list_frame.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                if child.cget("text") == name:
                    child.configure(fg_color=self.theme_manager.get_color("accent"))
                else:
                    child.configure(fg_color="transparent")

    def edit_selected_tool(self):
        if not self.selected_tool_name:
            self.parent_app.update_status("No tool selected to edit.", LYRN_WARNING)
            return

        tool = self.oss_tool_manager.get_tool(self.selected_tool_name)
        if not tool:
            self.parent_app.update_status(f"Tool '{self.selected_tool_name}' not found.", LYRN_ERROR)
            return

        self.clear_builder_fields()
        self.editing_tool_name = tool.name

        self.name_entry.insert(0, tool.name)
        self.name_entry.configure(state="disabled")
        # The 'definition' is now the primary content, stored in params.
        self.definition_textbox.insert("1.0", tool.params.get("definition", ""))

        self.tabview.set("Tool Editor")

    def delete_selected_tool(self):
        from confirmation_dialog import ConfirmationDialog
        if not self.selected_tool_name:
            self.parent_app.update_status("No tool selected to delete.", LYRN_WARNING)
            return

        tool_name = self.selected_tool_name
        prefs = self.parent_app.settings_manager.ui_settings.get("confirmation_preferences", {})
        if prefs.get("delete_tool"):
            confirmed = True
        else:
            confirmed, dont_ask_again = ConfirmationDialog.show(
                self, self.theme_manager,
                title="Confirm Deletion",
                message=f"Are you sure you want to permanently delete the tool '{tool_name}'?"
            )
            if dont_ask_again:
                prefs["delete_tool"] = True
                self.parent_app.settings_manager.ui_settings["confirmation_preferences"] = prefs
                self.parent_app.settings_manager.save_settings()

        if confirmed:
            self.oss_tool_manager.delete_tool(tool_name)
            self.parent_app.update_status(f"Tool '{tool_name}' deleted.", LYRN_SUCCESS)
            self.refresh_tool_list()
        else:
            self.parent_app.update_status("Deletion cancelled.", LYRN_INFO)

    def new_tool(self):
        self.clear_builder_fields()
        self.tabview.set("Tool Editor")

    def clear_builder_fields(self):
        self.editing_tool_name = None
        self.name_entry.configure(state="normal")
        self.name_entry.delete(0, "end")
        self.definition_textbox.delete("1.0", "end")

    def create_editor_tab(self):
        editor_frame = ctk.CTkScrollableFrame(self.tab_editor)
        editor_frame.pack(fill="both", expand=True, padx=20, pady=20)
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(1, weight=1)

        # --- Name Entry ---
        ctk.CTkLabel(editor_frame, text="Tool Name").pack(anchor="w")
        self.name_entry = ctk.CTkEntry(editor_frame)
        self.name_entry.pack(fill="x", pady=(0, 10))
        Tooltip(self.name_entry, "A unique name for this tool, e.g., 'get_current_weather'.")

        # --- Definition Textbox ---
        ctk.CTkLabel(editor_frame, text="Tool Definition (TypeScript-like format)").pack(anchor="w")
        self.definition_textbox = ctk.CTkTextbox(editor_frame, wrap="word", undo=True)
        self.definition_textbox.pack(fill="both", expand=True, pady=(0, 15))
        placeholder = """// Example:
// Gets the current weather in the provided location.
type get_current_weather = (_: {
  // The city and state, e.g. San Francisco, CA
  location: string,
  format?: "celsius" | "fahrenheit", // default: celsius
}) => any;
"""
        self.definition_textbox.insert("1.0", placeholder)


        # --- Save Button ---
        save_button = ctk.CTkButton(self.tab_editor, text="Save Tool", command=self.save_tool)
        save_button.pack(pady=20)

    def save_tool(self):
        name = self.name_entry.get().strip()
        definition = self.definition_textbox.get("1.0", "end-1c").strip()

        if not name or not definition:
            self.parent_app.update_status("Tool Name and Definition are required.", LYRN_ERROR)
            return

        if self.editing_tool_name is None and name in self.oss_tool_manager.tools:
            self.parent_app.update_status(f"Tool name '{name}' already exists.", LYRN_ERROR)
            return

        # For now, we save the raw definition. Parsing will be a separate step.
        # We can use the 'type' field to mark this as a new format tool.
        params = {"definition": definition}
        tool = OSSTool(name=name, type="oss_tool", params=params)

        self.oss_tool_manager.add_tool(tool)
        self.parent_app.update_status(f"Tool '{name}' saved.", LYRN_SUCCESS)
        self.refresh_tool_list()
        self.clear_builder_fields()
        self.tabview.set("Tool Viewer")


class MemoryPopup(ThemedPopup):
    """A popup window for managing chat history."""
    def __init__(self, parent, theme_manager: ThemeManager, language_manager: LanguageManager):
        super().__init__(parent=parent, theme_manager=theme_manager)
        self.parent_app = parent
        self.language_manager = language_manager

        # Episodic Memory attributes
        self.episodic_memory_manager = parent.episodic_memory_manager
        self.selected_entries = []
        self.entry_widgets = []


        self.title("Chat History")
        self.geometry("950x750")
        self.minsize(700, 500)

        self.create_widgets()
        self.apply_theme()

    def create_widgets(self):
        """Create the chat history UI without tabs."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        help_button = ctk.CTkButton(
            main_frame,
            text="?",
            width=28,
            height=28,
            command=lambda: self.parent_app.show_help("memory_popup.main")
        )
        help_button.place(relx=1.0, rely=0.0, x=0, y=0, anchor="ne")

        self.create_episodic_memory_tab(main_frame)
        self.load_entries()

    # --- Episodic Memory Methods ---
    def create_episodic_memory_tab(self, tab):
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        top_frame = ctk.CTkFrame(tab)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="Search memories...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_entries)
        self.list_frame = ctk.CTkScrollableFrame(tab)
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=0)
        bottom_frame = ctk.CTkFrame(tab)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        add_to_context_button = ctk.CTkButton(bottom_frame, text="Add Selected to Context", command=self.add_selected_to_context)
        add_to_context_button.pack(side="right")

    def load_entries(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.entry_widgets.clear()
        all_entries = self.episodic_memory_manager.get_all_entries()
        for entry_data in all_entries:
            self.create_entry_widget(entry_data)

    def create_entry_widget(self, entry_data: dict):
        entry_frame = ctk.CTkFrame(self.list_frame, border_width=1)
        entry_frame.pack(fill="x", padx=5, pady=(2, 3))
        var = ctk.BooleanVar(value=(entry_data['filepath'] in self.selected_entries))
        checkbox = ctk.CTkCheckBox(entry_frame, text="", variable=var, width=28, command=lambda path=entry_data['filepath'], v=var: self.toggle_selection(path, v))
        checkbox.pack(side="left", padx=5)
        content_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        content_frame.pack(side="left", fill="x", expand=True, pady=4)
        summary_heading = entry_data.get('summary_heading', 'No summary heading')
        try:
            dt_obj = datetime.fromisoformat(entry_data.get('time', ''))
            timestamp = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            timestamp = entry_data.get('time', 'Invalid time')
        mode, links = entry_data.get('mode', 'N/A'), entry_data.get('links', '')
        top_line_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_line_frame.pack(fill="x")
        ctk.CTkLabel(top_line_frame, text=summary_heading, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(top_line_frame, text=timestamp, anchor="e").pack(side="right", padx=5)
        bottom_line_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        bottom_line_frame.pack(fill="x")
        ctk.CTkLabel(bottom_line_frame, text=f"Mode: {mode}", anchor="w").pack(side="left", padx=5)
        if links:
            ctk.CTkLabel(bottom_line_frame, text=f"Tags: {links}", anchor="w", text_color="gray").pack(side="left", padx=5)
        self.entry_widgets.append((entry_frame, entry_data))

    def toggle_selection(self, filepath: str, var: ctk.BooleanVar):
        if var.get():
            if filepath not in self.selected_entries: self.selected_entries.append(filepath)
        else:
            if filepath in self.selected_entries: self.selected_entries.remove(filepath)

    def add_selected_to_context(self):
        if not self.selected_entries:
            self.parent_app.update_status("No entries selected.", LYRN_WARNING)
            return
        self.episodic_memory_manager.add_to_chat_review(self.selected_entries)
        self.parent_app.update_status(f"Added {len(self.selected_entries)} entries to chat_review.txt", LYRN_SUCCESS)
        self.selected_entries.clear()
        self.filter_entries()

    def filter_entries(self, event=None):
        search_term = self.search_entry.get().lower()
        for widget, data in self.entry_widgets:
            content = (f"{data.get('summary_heading', '')} {data.get('summary', '')} "
                       f"{data.get('keywords', '')} {data.get('topics', '')} "
                       f"{data.get('input', '')} {data.get('output', '')}").lower()
            if search_term in content:
                widget.pack(fill="x", padx=5, pady=(2, 3))
            else:
                widget.pack_forget()

class LyrnAIInterface(ctk.CTkToplevel):
    """Main LYRN-AI interface with enhanced features"""

    @staticmethod
    def format_ms_to_min_sec(ms: float) -> str:
        """Converts milliseconds to a 'Xm Ys' formatted string."""
        if ms == 0:
            return "0s"
        total_seconds = ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        if minutes > 0:
            return f"{minutes}m {seconds:.1f}s"
        else:
            return f"{seconds:.1f}s"

    def __init__(self, master, log_queue: queue.Queue):
        super().__init__(master)

        self.log_queue = log_queue

        # --- Phase 1: Immediate, Non-Blocking UI Setup ---
        self.llm = None
        self.is_thinking = False
        self.stop_generation = False
        self.stream_queue = queue.Queue()

        # Initialize only the managers essential for the initial UI
        self.settings_manager = SettingsManager()
        self.theme_manager = ThemeManager()

        # Perform system checks on startup
        system_checker = SystemChecker(self.settings_manager)
        system_checker.check_and_create_folders()
        missing_files = system_checker.check_essential_files()

        self.language_manager = LanguageManager(language=self.settings_manager.ui_settings.get("language", "en"))
        self.help_manager = HelpManager()
        self.episodic_memory_manager = EpisodicMemoryManager()
        self.current_font_size = self.settings_manager.ui_settings.get("font_size", 12)

        # Initialize other managers to None. They will be loaded in the background.
        self.snapshot_loader = None
        self.delta_manager = None
        self.automation_controller = None
        self.metrics = None
        self.chat_logger = None
        self.oss_tool_manager = None
        self.scheduler_manager = None
        self.cycle_manager = None
        self.resource_monitor = None
        self.chat_manager = None
        self.master_prompt_content = ""

        # --- Role and Color Management ---
        self.role_mappings = {
            "assistant": "final_output",
            "model": "final_output",
            "thinking": "thinking_process",
            "analysis": "thinking_process",
            "qwen_thinking": "thinking_process",
            "smol_thought": "thinking_process"
        }
        # The actual colors are loaded from settings_manager in apply_color_theme
        self.role_color_tags = {
            "final_output": "assistant_text",
            "thinking_process": "thinking_text",
            "user": "user_text",
            "system": "system_text"
        }

        # Set taskbar icon
        try:
            ICON_PATH = os.path.join(SCRIPT_DIR, "favicon.ico")
            if os.path.exists(ICON_PATH):
                icon = ImageTk.PhotoImage(Image.open(ICON_PATH))
                self.iconphoto(False, icon)
        except Exception:
            pass

        # Apply saved theme or default before creating widgets
        self.theme_manager.apply_theme(self.settings_manager.ui_settings.get("theme", "LYRN Dark"))

        # Basic window setup
        self.setup_window()
        self.load_tooltips()
        self.create_widgets()
        self.apply_color_theme()

        # Load previous chat session
        try:
            active_chat_path = os.path.join(SCRIPT_DIR, "active_chat.txt")
            if os.path.exists(active_chat_path):
                with open(active_chat_path, "r", encoding="utf-8") as f:
                    chat_content = f.read()
                if chat_content:
                    self.chat_display.configure(state="normal")
                    self.chat_display.insert("1.0", chat_content)
                    self.chat_display.configure(state="disabled")
                    self.chat_display.see("end")
        except Exception as e:
            print(f"Error loading previous chat session: {e}")

        # Handle window closing and keybinds
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Control-Shift-P>", self.open_command_palette)

        # Create context menu for chat display
        self.create_chat_context_menu()
        self.chat_display.bind("<Button-3>", self.show_chat_context_menu)

        # --- Phase 2: Start Background Initialization ---
        threading.Thread(target=self._initialize_background_services, daemon=True).start()
        self.after(100, self.process_queue)

        # Show missing files popup if any
        if missing_files:
            self.after(200, lambda: system_checker.show_missing_files_popup(self, missing_files, self.theme_manager))

    def show_loading_indicator(self):
        """Shows the indeterminate loading progress bar."""
        if hasattr(self, 'loading_progressbar'):
            self.loading_progressbar.pack(fill="x", pady=5, padx=10, before=self.status_textbox)
            self.loading_progressbar.start()
            self.update_status("Loading model...", LYRN_INFO)

    def hide_loading_indicator(self):
        """Hides the indeterminate loading progress bar."""
        if hasattr(self, 'loading_progressbar'):
            self.loading_progressbar.stop()
            self.loading_progressbar.pack_forget()

    def _initialize_background_services(self):
        """
        Initializes all managers and services that involve file I/O or other
        potentially blocking operations. Runs in a background thread.
        """
        print("Starting background initialization...")
        deltas_path = self.settings_manager.settings["paths"].get("deltas", "deltas")
        self.delta_manager = DeltaManager(deltas_base_dir=deltas_path)
        self.automation_controller = AutomationController()
        self.snapshot_loader = SnapshotLoader(self, self.settings_manager, self.automation_controller)
        self.metrics = EnhancedPerformanceMetrics()
        self.chat_logger = JournalLogger(self.settings_manager.settings["paths"].get("chat", "chat"))
        self.oss_tool_manager = OSSToolManager()
        self.scheduler_manager = SchedulerManager()
        self.cycle_manager = CycleManager()
        self.chat_manager = ChatManager(self.settings_manager.settings["paths"].get("chat", "chat"), self.settings_manager, self.role_mappings)
        self.resource_monitor = SystemResourceMonitor(self.stream_queue)
        self.resource_monitor.start()

        # Start watcher scripts
        watcher_scripts = ["scheduler_watcher.py", "cycle_watcher.py", "verbatim_memory_watcher.py"]
        for script_name in watcher_scripts:
            try:
                watcher_path = os.path.join(SCRIPT_DIR, "automation", script_name)
                if os.path.exists(watcher_path):
                    subprocess.Popen([sys.executable, watcher_path])
                    print(f"{script_name} started.")
            except Exception as e:
                print(f"Failed to start {script_name}: {e}")

        # Signal the main thread that initialization is complete
        self.stream_queue.put(('initialization_complete', None))
        print("Background initialization complete.")

    def _on_initialization_complete(self):
        """
        This method is called on the main UI thread after background services
        are loaded. It populates the UI with the loaded data.
        """
        print("Finalizing UI with loaded data...")
        self.update_status("Systems loaded.", LYRN_SUCCESS)

        # Show VRAM monitor only if NVML was successfully initialized
        if self.resource_monitor and self.resource_monitor.nvml_initialized:
            self.vram_frame.pack(fill="x", padx=10, pady=2)

        # Refresh UI elements that depend on the loaded managers
        self.refresh_active_cycle_selector()
        self.update_job_dropdown()
        self.update_oss_tool_dropdown()

        # Load the master prompt into the cache for the first time
        self.reload_master_prompt()

        # Now, handle the logic that was in start_application_logic
        if self.settings_manager.ui_settings.get("autoload_model", False) and self.settings_manager.settings.get("active", {}).get("model_path"):
            self.update_status("Autoloading model...", LYRN_INFO)
            threading.Thread(target=self.setup_model, daemon=True).start()
        elif self.settings_manager.first_boot or self.settings_manager.ui_settings.get("show_model_selector", True):
            self.open_model_selector()

        if self.settings_manager.ui_settings.get("llm_log_visible", False):
            self.toggle_log_viewer()


        # Model Status Indicator
        self.model_status = "Off"
        self.status_animation_after_id = None
        self.status_pulse_state = False
        self.status_definitions = {
            "Off": {"color": "#FF0000", "blink": False},
            "Model Error": {"color": "#FF0000", "blink": True},
            "Thinking": {"color": "#3B82F6", "blink": True},
            "Reasoning": {"color": "#3B82F6", "blink": False},
            "HB CYCLE": {"color": "#10B981", "blink": True},
            "Ready": {"color": "#10B981", "blink": False},
            "Automation": {"color": "#F59E0B", "blink": True},
            "Loading": {"color": LYRN_WARNING, "blink": False},
        }

        self.set_model_status("Off") # Start in Off state
        self.update_datetime()

    def update_datetime(self):
        """Updates the time and date labels."""
        now = datetime.now()
        if hasattr(self, 'datetime_label'):
            self.datetime_label.configure(text=now.strftime("%Y-%m-%d  %H:%M:%S"))
        self.after(1000, self.update_datetime)

    def set_model_status(self, status: str):
        if status not in self.status_definitions:
            print(f"Warning: Unknown model status '{status}'")
            return

        self.model_status = status
        status_info = self.status_definitions[status]

        # Cancel any ongoing animation
        if self.status_animation_after_id:
            self.after_cancel(self.status_animation_after_id)
            self.status_animation_after_id = None

        # Set initial color
        self.model_status_progress_bar.configure(progress_color=status_info["color"])

        # Start new animation if required
        if status_info["blink"]:
            self.status_pulse_state = True # Start with the main color
            self._animate_status_indicator()

    def _animate_status_indicator(self):
        status_info = self.status_definitions.get(self.model_status)
        if not status_info or not status_info["blink"]:
            return # Stop animation if status changed or is no longer blinking

        # Determine colors for the pulse
        main_color = status_info["color"]
        # The light-off color is the same as the system resources background
        off_color = self.theme_manager.get_color("status_bg_color", "#242424")

        # Set color based on pulse state
        target_color = main_color if self.status_pulse_state else off_color
        if hasattr(self, 'model_status_progress_bar'):
             self.model_status_progress_bar.configure(progress_color=target_color)

        # Toggle state for next pulse
        self.status_pulse_state = not self.status_pulse_state

        # Schedule next animation frame
        self.status_animation_after_id = self.after(500, self._animate_status_indicator)

    def load_tooltips(self):
        """Loads tooltips from the JSON file."""
        try:
            with open(os.path.join(SCRIPT_DIR, "hover_tooltip.json"), 'r', encoding='utf-8') as f:
                self.tooltips = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load tooltips: {e}")
            self.tooltips = {}

    def on_closing(self):
        """Handle cleanup on window close."""
        # Signal verbatim memory watcher to shutdown
        try:
            verbatim_flag_path = os.path.join(SCRIPT_DIR, "global_flags", "verbatim_state.txt")
            with open(verbatim_flag_path, 'w', encoding='utf-8') as f:
                f.write("shutdown")
        except Exception as e:
            print(f"Error signaling shutdown to verbatim watcher: {e}")

        # Save chat content
        try:
            chat_content = self.chat_display.get("1.0", "end-1c")
            # To prevent saving just a newline
            if chat_content.strip():
                with open(os.path.join(SCRIPT_DIR, "active_chat.txt"), "w", encoding="utf-8") as f:
                    f.write(chat_content)
        except Exception as e:
            print(f"Error saving chat on close: {e}")

        if hasattr(self, 'resource_monitor'):
            self.resource_monitor.stop()
        self.master.destroy() # Destroy the root window to exit the app

    def _get_app_commands(self):
        commands = []
        # Add theme commands
        if hasattr(self, 'theme_manager'):
            for theme_name in self.theme_manager.get_theme_names():
                commands.append({
                    "name": f"Theme: Switch to {theme_name}",
                    "command": lambda t=theme_name: self.on_theme_selected(t)
                })

        # Add other commands
        commands.extend([
            {"name": "Model: Reload (Full)", "command": self.reload_model_full},
            {"name": "Model: Offload", "command": self.offload_model},
            {"name": "Chat: Clear Display", "command": self.clear_chat},
            {"name": "Chat: Clear Chat Folder", "command": self.clear_chat_folder},
            {"name": "System: Open Settings", "command": self.open_settings},
            {"name": "System: View Logs", "command": self.toggle_log_viewer},
            {"name": "System: Force Memory Cleanup", "command": self.force_memory_cleanup},
            {"name": "Font: Increase Size", "command": self.increase_font_size},
            {"name": "Font: Decrease Size", "command": self.decrease_font_size},
        ])
        return commands

    def open_command_palette(self, event=None):
        commands = self._get_app_commands()
        if hasattr(self, 'cmd_palette') and self.cmd_palette.winfo_exists():
            self.cmd_palette.focus()
        else:
            self.cmd_palette = CommandPalette(self, commands=commands, theme_manager=self.theme_manager)
            self.cmd_palette.focus()

    def open_model_selector(self):
        """Opens the model selector popup window."""
        if hasattr(self, 'model_selector_popup') and self.model_selector_popup.winfo_exists():
            self.model_selector_popup.lift()
            self.model_selector_popup.focus()
        else:
            self.model_selector_popup = ModelSelectorPopup(self, self.settings_manager, self.theme_manager)
            self.model_selector_popup.focus()

    def setup_window(self):
        """Configure main window with LYRN-AI branding"""
        self.title("LYRN-AI Dashboard v4.2.9")
        size = self.settings_manager.ui_settings.get("window_size", "1400x900")
        self.geometry(size)
        self.minsize(1200, 800)

    def handle_first_boot(self):
        """Handle first boot scenario"""
        print("Handling first boot...")

        def on_first_boot_complete():
            self.first_boot_complete = True
            self.initialize_application()

        # Show simplified first boot dialog (implement as needed)
        self.after(100, lambda: self.initialize_application())


    def setup_model(self):
        """Initialize LLM model with proper cleanup"""
        if not self.settings_manager.settings:
            print("No settings available for model setup")
            self.llm = None
            return

        self.stream_queue.put(('show_loading',))
        self.set_model_status("Loading")
        active = self.settings_manager.settings["active"]

        try:
            print(f"Loading LYRN-AI model: {active['model_path']}")

            # Ensure previous model is properly cleaned up
            if hasattr(self, 'llm') and self.llm is not None:
                print("Cleaning up previous model...")
                del self.llm
                gc.collect()

            self.llm = Llama(
                model_path=active["model_path"],
                n_ctx=active["n_ctx"],
                n_threads=active["n_threads"],
                n_gpu_layers=active["n_gpu_layers"],
                n_batch=active.get("n_batch", 512),
                use_mlock=True,
                use_mmap=False,
                chat_format=active.get("chat_format"),
                add_bos=True,
                add_eos=True,
                verbose=True
            )
            print("LYRN-AI model loaded successfully")
            self.stream_queue.put(('status_update', 'Model Loaded', LYRN_SUCCESS))
            self.set_model_status("Ready")
            # Update toggle button on success
            if hasattr(self, 'model_toggle_button'):
                self.model_toggle_button.configure(text="Offload Model", fg_color="#35215f")

        except Exception as e:
            print(f"Error loading model: {e}")
            self.llm = None
            # Update toggle button on failure
            if hasattr(self, 'model_toggle_button'):
                self.model_toggle_button.configure(text="Load Model", fg_color=self.theme_manager.get_color("primary"))
            self.stream_queue.put(('status_update', f'Model Load Failed', LYRN_ERROR))
            self.set_model_status("Model Error")

        finally:
            self.stream_queue.put(('hide_loading',))

    def create_widgets(self):
        """Create main interface widgets with LYRN-AI styling"""
        self.grid_rowconfigure(0, weight=0) # Top bar
        self.grid_rowconfigure(1, weight=1) # Main content
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        self.create_left_sidebar().grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        self.create_chat_area().grid(row=1, column=1, sticky="nsew", padx=(0, 5), pady=(0, 10))
        self.create_right_sidebar().grid(row=1, column=2, sticky="nsew", padx=(5, 10), pady=(0, 10))

    def create_left_sidebar(self):
        """Creates the left sidebar for controls."""
        self.left_sidebar = ctk.CTkFrame(self, width=320, corner_radius=38)
        self.left_sidebar.grid_propagate(False)

        # LYRN-AI Header with logo placeholder
        header_frame = ctk.CTkFrame(self.left_sidebar, fg_color=LYRN_PURPLE, corner_radius=38)
        header_frame.pack(fill="x", padx=10, pady=(10, 20))
        header_frame.pack_propagate(False)
        header_frame.grid_columnconfigure((0, 2), weight=1) # Give weight to side columns for centering
        header_frame.grid_columnconfigure(1, weight=0)


        try:
            title_font = ctk.CTkFont(family="Consolas", size=26, weight="bold")
            section_font = ctk.CTkFont(family="Consolas", size=14, weight="bold")
            normal_font = ctk.CTkFont(family="Consolas", size=self.current_font_size)
            datetime_font = ctk.CTkFont(family="Consolas", size=18, weight="bold")
        except:
            title_font = ("Consolas", 26, "bold")
            section_font = ("Consolas", 14, "bold")
            normal_font = ("Consolas", self.current_font_size)
            datetime_font = ("Consolas", 18, "bold")

        # Logo placeholder and title
        logo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=1, pady=10) # Place logo in the center column

        # Attempt to load and display the logo
        try:
            if Image and ImageTk:
                logo_path = os.path.join(SCRIPT_DIR, "images/lyrn_logo.png")
                if os.path.exists(logo_path):
                    logo_image = Image.open(logo_path)
                    ctk_logo_image = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(48, 48))
                    logo_label = ctk.CTkLabel(logo_frame, image=ctk_logo_image, text="")
                    logo_label.pack(side="left", padx=(0, 10))
                else:
                    # Fallback to emoji if logo not found
                    ctk.CTkLabel(logo_frame, text="🧠", font=("Arial", 48)).pack(side="left", padx=(0, 10))
            else:
                # Fallback if Pillow is not installed
                ctk.CTkLabel(logo_frame, text="🧠", font=("Arial", 48)).pack(side="left", padx=(0, 10))
        except Exception as e:
            print(f"Error loading logo: {e}")
            ctk.CTkLabel(logo_frame, text="🧠", font=("Arial", 48)).pack(side="left", padx=(0, 10))


        title_label = ctk.CTkLabel(logo_frame, text="LYRN-AI", font=title_font,
                    text_color="white")
        title_label.pack(side="left", pady=(10,0))


        # Enhanced Status Section
        self.create_enhanced_status()

        # Quick controls frame
        self.quick_frame = ctk.CTkFrame(self.left_sidebar, fg_color="transparent", border_width=0)
        self.quick_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.quick_frame, text="Quick Controls", font=section_font).pack(pady=10)

        # Reordered as per user request
        self.show_llm_log_button = ctk.CTkButton(self.quick_frame, text="📋 View Logs",
                                                 font=normal_font, command=self.toggle_log_viewer)
        self.show_llm_log_button.pack(fill="x", padx=10, pady=3)
        Tooltip(self.show_llm_log_button, self.tooltips.get("show_llm_log_button", ""))

        self.terminal_button = ctk.CTkButton(self.quick_frame, text="📟 Code Terminal", command=self.open_terminal)
        self.terminal_button.pack(fill="x", padx=10, pady=3)
        Tooltip(self.terminal_button, self.tooltips.get("terminal_button", ""))

        self.clear_chat_button = ctk.CTkButton(self.quick_frame, text="🗑️ Clear Display", command=self.clear_chat)
        self.clear_chat_button.pack(fill="x", padx=10, pady=3)
        Tooltip(self.clear_chat_button, self.tooltips.get("clear_chat_button", ""))

        self.clear_chat_folder_button = ctk.CTkButton(self.quick_frame, text="🗑️ Clear Chat Folder", command=self.clear_chat_folder)
        self.clear_chat_folder_button.pack(fill="x", padx=10, pady=3)
        Tooltip(self.clear_chat_folder_button, self.tooltips.get("clear_chat_folder_button", ""))

        self.start_new_session_button = ctk.CTkButton(self.quick_frame, text="🆕 Start New Session", command=self.start_new_session)
        self.start_new_session_button.pack(fill="x", padx=10, pady=3)
        Tooltip(self.start_new_session_button, "Archives the current chat history session and starts a new one.")


        # self.tasks_goals_button = ctk.CTkButton(self.quick_frame, text="🎯 Tasks/Goals", command=self.open_tasks_goals_popup)
        # self.tasks_goals_button.pack(fill="x", padx=10, pady=3)
        # Tooltip(self.tasks_goals_button, "Open the Tasks and Goals manager.")


        # Add a spacer to push content to the top
        spacer = ctk.CTkFrame(self.left_sidebar, fg_color="transparent")
        spacer.pack(expand=True, fill="both")

        return self.left_sidebar

    def show_help(self, help_code: str):
        """Opens the help popup for a specific component."""
        HelpPopup(self, self.theme_manager, help_code)

    def create_right_sidebar(self):
        """Creates the right sidebar for monitoring and gauges."""
        self.right_sidebar = ctk.CTkFrame(self, width=320, corner_radius=38)
        self.right_sidebar.grid_propagate(False)

        # Datetime display
        try:
            datetime_font = ctk.CTkFont(family="Consolas", size=24, weight="bold")
        except:
            datetime_font = ("Consolas", 24, "bold")

        datetime_frame = ctk.CTkFrame(self.right_sidebar, fg_color="transparent")
        datetime_frame.pack(pady=(20, 10), padx=10, anchor="n")
        datetime_frame.grid_columnconfigure(0, weight=1)

        # Combine date and time into a single label for guaranteed one-line display
        self.datetime_label = ctk.CTkLabel(datetime_frame, text="", font=datetime_font)
        self.datetime_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.settings_button = ctk.CTkButton(datetime_frame, text="⚙️", command=self.open_settings, width=40, height=40)
        self.settings_button.grid(row=0, column=1)
        Tooltip(self.settings_button, self.tooltips.get("settings_button", ""))

        # Enhanced Performance Metrics Section
        self.create_enhanced_metrics()

        # Job Automation Section
        self.job_frame = ctk.CTkFrame(self.right_sidebar, fg_color="transparent", border_width=0)
        self.job_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.job_frame, text="Job Automation", font=ctk.CTkFont(family="Consolas", size=14, weight="bold")).pack(pady=10)

        # Cycle Control
        cycle_frame = ctk.CTkFrame(self.job_frame)
        cycle_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(cycle_frame, text="Active Cycle:").pack(side="left", padx=(0, 5))
        self.active_cycle_selector = ctk.CTkComboBox(cycle_frame, values=[], command=None)
        self.active_cycle_selector.pack(side="left", expand=True, fill="x")
        self.cycle_toggle_button = ctk.CTkButton(cycle_frame, text="Start", width=60, command=self.toggle_cycle)
        self.cycle_toggle_button.pack(side="left", padx=5)

        # Job Runner
        job_runner_frame = ctk.CTkFrame(self.job_frame)
        job_runner_frame.pack(fill="x", padx=10, pady=5)
        self.job_dropdown = ctk.CTkComboBox(job_runner_frame, values=["No jobs loaded"])
        self.job_dropdown.pack(side="left", expand=True, fill="x")
        run_job_button = ctk.CTkButton(job_runner_frame, text="Run", width=60, command=self.run_selected_job_from_dropdown)
        run_job_button.pack(side="left", padx=5)

        # OSS Tool Runner
        oss_tool_runner_frame = ctk.CTkFrame(self.job_frame)
        oss_tool_runner_frame.pack(fill="x", padx=10, pady=5)
        self.oss_tool_dropdown = ctk.CTkComboBox(oss_tool_runner_frame, values=["No tools loaded"])
        self.oss_tool_dropdown.pack(side="left", expand=True, fill="x")
        run_oss_tool_button = ctk.CTkButton(oss_tool_runner_frame, text="Run", width=60, command=self.run_selected_oss_tool)
        run_oss_tool_button.pack(side="left", padx=5)

        self.job_watcher_button = ctk.CTkButton(self.job_frame, text="Job Manager", command=self.open_job_watcher_popup)
        self.job_watcher_button.pack(fill="x", padx=10, pady=5)
        Tooltip(self.job_watcher_button, self.tooltips.get("job_manager_button", ""))

        self.oss_tool_button = ctk.CTkButton(self.job_frame, text="OSS Tools", command=self.open_oss_tool_popup)
        self.oss_tool_button.pack(fill="x", padx=10, pady=5)
        Tooltip(self.oss_tool_button, self.tooltips.get("oss_tool_button", ""))

        # self.memory_button = ctk.CTkButton(self.job_frame, text="Memory", command=self.open_memory_popup)
        # self.memory_button.pack(fill="x", padx=10, pady=5)
        # Tooltip(self.memory_button, "Open the Memory management popup.")

        return self.right_sidebar

    def create_enhanced_metrics(self):
        """Create enhanced performance metrics with gauges"""
        self.metrics_frame = ctk.CTkFrame(self.right_sidebar, fg_color="transparent", border_width=0, corner_radius=38)
        self.metrics_frame.pack(fill="x", padx=10, pady=10)

        try:
            section_font = ctk.CTkFont(family="Consolas", size=14, weight="bold")
            normal_font = ctk.CTkFont(family="Consolas", size=self.current_font_size)
        except:
            section_font = ("Consolas", 14, "bold")
            normal_font = ("Consolas", self.current_font_size)

        ctk.CTkLabel(self.metrics_frame, text="Performance Metrics", font=section_font).pack(pady=10)

        # KV Cache with progress bar
        kv_frame = ctk.CTkFrame(self.metrics_frame)
        kv_frame.pack(fill="x", padx=10, pady=2)
        self.kv_label = ctk.CTkLabel(kv_frame, text="KV Cache: 0 tokens", font=normal_font)
        self.kv_label.pack(pady=(0,2))
        self.kv_progress = ctk.CTkProgressBar(kv_frame, height=8)
        self.kv_progress.pack(fill="x", padx=5, pady=(0,5))
        self.kv_progress.set(0)

        # Prompt and Response tokens
        token_frame = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
        token_frame.pack(fill="x", padx=10, pady=2)
        token_frame.grid_columnconfigure((0, 1), weight=1)
        self.prompt_label = ctk.CTkLabel(token_frame, text="Prompt: 0 tokens", font=normal_font)
        self.prompt_label.grid(row=0, column=0, sticky="w")
        self.response_label = ctk.CTkLabel(token_frame, text="Response: 0 tokens", font=normal_font)
        self.response_label.grid(row=0, column=1, sticky="w")

        # Generation speed
        self.eval_label = ctk.CTkLabel(self.metrics_frame, text="Generation: 0.0 tok/s", font=normal_font)
        self.eval_label.pack(pady=2)

        # Time Metrics
        time_metrics_frame = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
        time_metrics_frame.pack(fill="x", padx=10, pady=2)
        time_metrics_frame.grid_columnconfigure((0, 1), weight=1)

        self.generation_time_label = ctk.CTkLabel(time_metrics_frame, text="Gen Time: 0.0s", font=normal_font)
        self.generation_time_label.grid(row=0, column=0, sticky="w")
        self.tokenization_time_label = ctk.CTkLabel(time_metrics_frame, text="Token Time: 0.0s", font=normal_font)
        self.tokenization_time_label.grid(row=0, column=1, sticky="w")

        # Total tokens
        total_frame = ctk.CTkFrame(self.metrics_frame)
        total_frame.pack(fill="x", padx=10, pady=2)
        self.total_label = ctk.CTkLabel(total_frame, text="Total: 0 tokens", font=normal_font)
        self.total_label.pack(pady=(0,2))
        self.total_progress = ctk.CTkProgressBar(total_frame, height=8)
        self.total_progress.pack(fill="x", padx=5, pady=(0,5))
        self.total_progress.set(0)

        # Save metrics button
        ctk.CTkButton(self.metrics_frame, text="💾 Save Metrics",
                     font=normal_font, height=25, command=self.save_metrics_log).pack(
                         padx=10, pady=(10, 10), fill="x")

        # System Resource Gauges
        ctk.CTkLabel(self.metrics_frame, text="System Resources", font=section_font).pack(pady=(10,5))

        # CPU
        cpu_frame = ctk.CTkFrame(self.metrics_frame)
        cpu_frame.pack(fill="x", padx=10, pady=2)
        self.cpu_label = ctk.CTkLabel(cpu_frame, text="CPU: 0.0% (N/A)", font=normal_font)
        self.cpu_label.pack(pady=(0,2))
        self.cpu_progress = ctk.CTkProgressBar(cpu_frame, height=8, progress_color="#F59E0B")
        self.cpu_progress.pack(fill="x", padx=5, pady=(0,5))
        self.cpu_progress.set(0)

        # RAM
        ram_frame = ctk.CTkFrame(self.metrics_frame)
        ram_frame.pack(fill="x", padx=10, pady=2)
        self.ram_label = ctk.CTkLabel(ram_frame, text="RAM: 0.0%", font=normal_font)
        self.ram_label.pack(pady=(0,2))
        self.ram_progress = ctk.CTkProgressBar(ram_frame, height=8, progress_color="#3B82F6")
        self.ram_progress.pack(fill="x", padx=5, pady=(0,5))
        self.ram_progress.set(0)

        # Disk
        disk_frame = ctk.CTkFrame(self.metrics_frame)
        disk_frame.pack(fill="x", padx=10, pady=2)
        self.disk_label = ctk.CTkLabel(disk_frame, text="Disk: 0.0%", font=normal_font)
        self.disk_label.pack(pady=(0,2))
        self.disk_progress = ctk.CTkProgressBar(disk_frame, height=8, progress_color=LYRN_SUCCESS)
        self.disk_progress.pack(fill="x", padx=5, pady=(0,5))
        self.disk_progress.set(0)

        # VRAM (only if NVIDIA GPU is detected)
        # Create the widgets but keep them hidden. They will be shown in _on_initialization_complete if needed.
        self.vram_frame = ctk.CTkFrame(self.metrics_frame)
        self.vram_label = ctk.CTkLabel(self.vram_frame, text="VRAM: 0.0%", font=normal_font)
        self.vram_label.pack(pady=(0,2))
        self.vram_progress = ctk.CTkProgressBar(self.vram_frame, height=8, progress_color="#EF4444")
        self.vram_progress.pack(fill="x", padx=5, pady=(0,5))
        self.vram_progress.set(0)

    def update_system_gauges(self, stats: Dict[str, any]):
        """Update system resource gauges with new data."""
        if not hasattr(self, 'cpu_label'): return # Widgets not ready

        # CPU
        self.cpu_label.configure(text=f"CPU: {stats['cpu']:.1f}% ({stats['cpu_temp']})")
        self.cpu_progress.set(stats['cpu'] / 100)

        # RAM
        ram_text = f"RAM: {stats['ram_used_gb']:.1f}/{stats['ram_total_gb']:.1f} GB ({stats['ram_percent']:.1f}%)"
        self.ram_label.configure(text=ram_text)
        self.ram_progress.set(stats['ram_percent'] / 100)

        # Disk
        disk_text = f"Disk: {stats['disk_used_gb']:.1f}/{stats['disk_total_gb']:.1f} GB ({stats['disk_percent']:.1f}%)"
        if hasattr(self, 'disk_label'):
            self.disk_label.configure(text=disk_text)
            self.disk_progress.set(stats['disk_percent'] / 100)

        # VRAM
        if self.resource_monitor and self.resource_monitor.nvml_initialized:
            vram_text = f"VRAM: {stats['vram_used_gb']:.1f}/{stats['vram_total_gb']:.1f} GB ({stats['vram_percent']:.1f}%)"
            self.vram_label.configure(text=vram_text)
            self.vram_progress.set(stats['vram_percent'] / 100)

    def create_enhanced_status(self):
        """Create enhanced status display with better organization."""
        self.status_frame = ctk.CTkFrame(self.left_sidebar, fg_color="transparent", border_width=0)
        self.status_frame.pack(fill="x", padx=10, pady=(0, 10))

        try:
            section_font = ctk.CTkFont(family="Consolas", size=14, weight="bold")
            status_font = ctk.CTkFont(family="Consolas", size=12, weight="bold")
            normal_font = ctk.CTkFont(family="Consolas", size=self.current_font_size)
        except:
            section_font = ("Consolas", 14, "bold")
            status_font = ("Consolas", 12, "bold")
            normal_font = ("Consolas", self.current_font_size)

        # Frame for title and status light
        title_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        title_frame.pack(pady=(10, 5))

        ctk.CTkLabel(title_frame, text="System Status", font=section_font).pack(side="left", padx=(0, 10))

        self.model_status_progress_bar = ctk.CTkProgressBar(title_frame, width=80, height=15)
        self.model_status_progress_bar.set(1) # Set to 100%
        self.model_status_progress_bar.pack(side="left")

        # Restored textbox for general status messages
        self.status_textbox = ctk.CTkTextbox(self.status_frame, height=50, wrap="char", font=status_font)
        self.status_textbox.pack(fill="x", padx=10, pady=5)
        self.status_textbox.insert("end", "System ready.")
        self.status_textbox.configure(state="disabled")

        # Loading Progress Bar (hidden by default)
        self.loading_progressbar = ctk.CTkProgressBar(self.status_frame, mode='indeterminate')

        # Model Control Buttons
        self.model_toggle_button = ctk.CTkButton(self.status_frame, text="Load Model", font=normal_font, command=self.toggle_model_load)
        self.model_toggle_button.pack(fill="x", padx=10, pady=(5, 2))
        Tooltip(self.model_toggle_button, self.tooltips.get("model_toggle_button", ""))

        # --- Relocated Controls ---
        self.change_model_button = ctk.CTkButton(self.status_frame, text="⚙️ Model Settings", command=self.open_model_selector)
        self.change_model_button.pack(fill="x", padx=10, pady=(10, 5))
        Tooltip(self.change_model_button, self.tooltips.get("change_model_button", ""))


        self.prompt_builder_button = ctk.CTkButton(self.status_frame, text="📝 System Prompt", command=self.open_prompt_builder)
        self.prompt_builder_button.pack(fill="x", padx=10, pady=3)
        Tooltip(self.prompt_builder_button, self.tooltips.get("prompt_builder_button", ""))

        self.personality_button = ctk.CTkButton(self.status_frame, text="🎭 Personality", command=self.open_personality_popup)
        self.personality_button.pack(fill="x", padx=10, pady=3)
        Tooltip(self.personality_button, self.tooltips.get("personality_button", ""))



        # --- End Relocated Controls ---

    def create_chat_area(self):
        """Create enhanced chat interface with colored text support"""
        chat_frame = ctk.CTkFrame(self, corner_radius=38)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        try:
            chat_font = ctk.CTkFont(family="Consolas", size=self.current_font_size)
        except:
            chat_font = ("Consolas", self.current_font_size)

        self.chat_display = ctk.CTkTextbox(chat_frame, font=chat_font, wrap="word", border_width=2, border_color=self.theme_manager.get_color("secondary_border_color"), text_color=self.theme_manager.get_color("display_text_color"))
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

        chat_colors = self.settings_manager.get_setting("chat_colors", {})
        self.chat_display.tag_config("system_text", foreground=chat_colors.get("system_text", "#B0B0B0"))
        self.chat_display.tag_config("user_text", foreground=chat_colors.get("user_text", "#00C0A0"))
        self.chat_display.tag_config("assistant_text", foreground=chat_colors.get("assistant_text", "#FFFFFF"))
        self.chat_display.tag_config("thinking_text", foreground=chat_colors.get("thinking_text", "#FFD700"))
        self.chat_display.tag_config("error", foreground=self.theme_manager.get_color("error"))
        self.chat_display.tag_config("success", foreground=self.theme_manager.get_color("success"))

        input_frame = ctk.CTkFrame(chat_frame)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        input_frame.grid_columnconfigure(0, weight=1)

        hint_label = ctk.CTkLabel(input_frame, text="Use Ctrl+Enter to send", font=("Consolas", 10))
        hint_label.grid(row=0, column=0, sticky="nw", padx=5, pady=2)

        self.input_box = ctk.CTkTextbox(input_frame, height=100, font=chat_font, border_width=2, undo=True, border_color=self.theme_manager.get_color("secondary_border_color"))
        self.input_box.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        input_frame.grid_rowconfigure(1, weight=1)

        button_vframe = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_vframe.grid(row=1, column=1, padx=(5,0))

        self.send_btn = ctk.CTkButton(button_vframe, text="Send", width=80,
                                     font=chat_font,
                                     command=self.send_message)
        self.send_btn.pack(pady=(0, 5), fill="x")
        Tooltip(self.send_btn, self.tooltips.get("send_button", ""))

        self.copy_btn = ctk.CTkButton(button_vframe, text="Copy", width=80,
                                     font=chat_font,
                                     command=self.copy_last_response)
        self.copy_btn.pack(pady=(5, 0), fill="x")
        Tooltip(self.copy_btn, self.tooltips.get("copy_button", ""))

        self.stop_btn = ctk.CTkButton(button_vframe, text="Stop", width=80,
                                     font=chat_font,
                                     command=self.stop_generation_process,
                                     state="disabled")
        self.stop_btn.pack(pady=(5, 0), fill="x")
        Tooltip(self.stop_btn, self.tooltips.get("stop_button", ""))

        self.input_box.bind("<Control-Return>", self.send_message_from_event)
        return chat_frame

    def execute_job_directly(self, job_name: str, job_trigger: str):
        """Executes a job by sending its trigger directly to the backend without user interaction."""
        if not self.llm:
            self.update_status("No model loaded", LYRN_ERROR)
            return

        self.display_colored_message(f"--- Running Job: {job_name} ---\n", "system_text")

        history_messages = self.chat_manager.get_chat_history_messages() if self.chat_manager else []

        self.chat_logger.start_log()
        self.chat_logger.append_log("USER", f"--- JOB TRIGGER: {job_name} ---\n{job_trigger}")

        self.send_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.stop_generation = False
        self._write_llm_status("busy")

        self.display_colored_message("Assistant: Thinking...\n", "thinking_text")
        self.is_thinking = True

        self.set_model_status("Thinking")
        threading.Thread(target=self.generate_response, args=(job_trigger, history_messages), daemon=True).start()
        self.update_status(f"Executing job '{job_name}'...", LYRN_INFO)


    def display_colored_message(self, message: str, tag: str):
        """Appends a message to the chat display with a specific color tag."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", message, tag)
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def on_theme_selected(self, theme_name: str):
        """Callback for when a new theme is selected from the dropdown."""
        self.theme_manager.apply_theme(theme_name)

        # Save the new theme setting
        self.settings_manager.ui_settings["theme"] = theme_name
        self.settings_manager.save_settings()

        # Re-apply colors to all relevant widgets
        self.apply_color_theme()

        # Also re-apply to settings dialog if it's open
        if hasattr(self, 'settings_dialog') and self.settings_dialog.winfo_exists():
            self.settings_dialog.apply_theme()

        self.update_status(f"Theme changed to {theme_name}", self.theme_manager.get_color("info"))

    def increase_font_size(self):
        """Increase font size"""
        if self.current_font_size < 20:
            self.current_font_size += 1
            self.settings_manager.ui_settings["font_size"] = self.current_font_size
            self.settings_manager.save_settings()
            self.apply_font_changes()

    def decrease_font_size(self):
        """Decrease font size"""
        if self.current_font_size > 8:
            self.current_font_size -= 1
            self.settings_manager.ui_settings["font_size"] = self.current_font_size
            self.settings_manager.save_settings()
            self.apply_font_changes()

    def apply_font_changes(self):
        """Apply font size changes to relevant widgets"""
        try:
            new_font = ctk.CTkFont(family="Consolas", size=self.current_font_size)

            # Update chat display and input
            self.chat_display.configure(font=new_font)
            self.input_box.configure(font=new_font)

            # Update other elements as needed
            self.update_status(f"Font size: {self.current_font_size}", LYRN_INFO)

        except Exception as e:
            print(f"Error applying font changes: {e}")


    def apply_color_theme(self):
        """Apply colors from the current theme to all relevant widgets."""
        try:
            tm = self.theme_manager
            primary_color = tm.get_color("primary")
            accent_color = tm.get_color("accent")
            frame_bg = tm.get_color("frame_bg")
            textbox_bg = tm.get_color("textbox_bg")
            textbox_fg = tm.get_color("textbox_fg")
            label_text = tm.get_color("label_text")
            button_hover_color = tm.get_color("button_hover", fallback=accent_color)
            border_color = tm.get_color("border_color")

            # Theme background
            self.configure(fg_color=frame_bg)

            # --- Update all widgets recursively ---
            for widget_type, config in [
                (ctk.CTkButton, {"fg_color": primary_color, "hover_color": button_hover_color}),
                (ctk.CTkComboBox, {"button_color": primary_color, "button_hover_color": button_hover_color}),
                (ctk.CTkFrame, {"fg_color": frame_bg, "border_color": border_color}),
                (ctk.CTkLabel, {"text_color": label_text}),
                (ctk.CTkTextbox, {"fg_color": textbox_bg, "text_color": textbox_fg, "border_color": border_color}),
                (ctk.CTkScrollableFrame, {"fg_color": frame_bg, "label_fg_color": primary_color}),
                (ctk.CTkCheckBox, {"fg_color": primary_color, "hover_color": button_hover_color}),
                (ctk.CTkSlider, {"progress_color": primary_color, "button_color": primary_color, "button_hover_color": button_hover_color}),
                (ctk.CTkSwitch, {
                    "progress_color": tm.get_color("switch_progress", fallback=primary_color),
                    "button_color": tm.get_color("switch_button", fallback=accent_color),
                    "button_hover_color": tm.get_color("button_hover", fallback=button_hover_color),
                    "fg_color": tm.get_color("switch_bg_off", fallback="#555555") # fg_color is the 'off' state
                }),
                (ctk.CTkTabview, {"segmented_button_selected_color": primary_color, "segmented_button_selected_hover_color": button_hover_color})
            ]:
                for widget in self.find_widgets_recursively(self, widget_type):
                    try:
                        widget.configure(**config)
                    except Exception:
                        # Ignore if a widget doesn't support a property, e.g. a specific button
                        pass

            # --- Update specific labels ---
            if hasattr(self, 'chat_display'):
                self.chat_display.configure(text_color=tm.get_color("display_text_color"))
            if hasattr(self, 'kv_label'):
                self.kv_label.configure(text_color=tm.get_color("info"))
            if hasattr(self, 'prompt_label'):
                self.prompt_label.configure(text_color=tm.get_color("system_text"))
            if hasattr(self, 'eval_label'):
                self.eval_label.configure(text_color=tm.get_color("generation_speed_text", fallback=accent_color))
            if hasattr(self, 'total_label'):
                self.total_label.configure(text_color=tm.get_color("success"))

            # Update border colors
            border_color = tm.get_color("border_color")
            if hasattr(self, 'job_frame'):
                self.job_frame.configure(border_color=border_color)
            if hasattr(self, 'system_frame'):
                self.system_frame.configure(border_color=border_color)
            if hasattr(self, 'quick_frame'):
                self.quick_frame.configure(border_color=border_color)
            if hasattr(self, 'metrics_frame'):
                self.metrics_frame.configure(border_color=border_color)
            if hasattr(self, 'hwinfo_frame'):
                self.hwinfo_frame.configure(border_color=border_color)
            if hasattr(self, 'status_frame'):
                self.status_frame.configure(border_color=border_color)

            # --- Apply secondary button color ---
            secondary_button_color = tm.get_color("secondary_button", fallback="#555555")
            if hasattr(self, 'show_llm_log_button'):
                self.show_llm_log_button.configure(fg_color=secondary_button_color)
            if hasattr(self, 'terminal_button'):
                self.terminal_button.configure(fg_color=secondary_button_color)
            if hasattr(self, 'clear_chat_button'):
                self.clear_chat_button.configure(fg_color=secondary_button_color)
            if hasattr(self, 'clear_chat_folder_button'):
                self.clear_chat_folder_button.configure(fg_color=secondary_button_color)
            if hasattr(self, 'settings_button'):
                self.settings_button.configure(fg_color=secondary_button_color)

            print("Color theme re-applied to main window widgets.")

            # --- Re-apply chat-specific colors ---
            if hasattr(self, 'chat_display'):
                chat_colors = self.settings_manager.get_setting("chat_colors", {})
                self.chat_display.tag_config("system_text", foreground=chat_colors.get("system_text", "#B0B0B0"))
                self.chat_display.tag_config("user_text", foreground=chat_colors.get("user_text", "#00C0A0"))
                self.chat_display.tag_config("assistant_text", foreground=chat_colors.get("assistant_text", "#FFFFFF"))
                self.chat_display.tag_config("thinking_text", foreground=chat_colors.get("thinking_text", "#FFD700"))


        except Exception as e:
            print(f"Error applying color theme: {e}")

    def find_widgets_recursively(self, widget, widget_type):
        widgets = []
        if isinstance(widget, widget_type):
            widgets.append(widget)
        for child in widget.winfo_children():
            widgets.extend(self.find_widgets_recursively(child, widget_type))
        return widgets

    def save_metrics_log(self):
        """Save current metrics to log file"""
        if hasattr(self, 'metrics'):
            log_file = self.metrics.save_metrics_log(self.settings_manager)
            if log_file:
                self.update_status(f"Metrics saved to log", LYRN_SUCCESS)
            else:
                self.update_status("Failed to save metrics", LYRN_ERROR)

    # open_personality_popup removed, functionality moved to settings dialog

    def open_terminal(self):
        """Opens a new terminal window in the specified path."""
        start_path = self.settings_manager.ui_settings.get("terminal_start_path", SCRIPT_DIR)
        if not os.path.isdir(start_path):
            start_path = SCRIPT_DIR
            self.update_status(f"Terminal path not found, defaulting to script dir.", LYRN_WARNING)

        try:
            if sys.platform == "win32":
                subprocess.Popen(f'start cmd', shell=True, cwd=start_path)
            elif sys.platform == "darwin":
                # For macOS, 'open -a Terminal .' works well from a specific directory
                subprocess.Popen(['open', '-a', 'Terminal', start_path])
            else:  # Assuming Linux
                try:
                    # Tries to open gnome-terminal, common on many Linux distros
                    subprocess.Popen(['gnome-terminal', '--working-directory', start_path])
                except FileNotFoundError:
                    try:
                        # Fallback to xterm, which is more likely to be installed
                        subprocess.Popen(['xterm', '-e', f'cd "{start_path}" && bash'])
                    except FileNotFoundError:
                        self.update_status("Could not find a terminal to open.", LYRN_ERROR)
        except Exception as e:
            self.update_status(f"Failed to open terminal: {e}", LYRN_ERROR)
            print(f"Failed to open terminal: {e}")

    def open_settings(self):
        """Open enhanced tabbed settings dialog"""
        if not hasattr(self, 'settings_dialog') or not self.settings_dialog.winfo_exists():
            self.settings_dialog = TabbedSettingsDialog(self, self.settings_manager, self.theme_manager, self.language_manager)
            self.settings_dialog.focus()
        else:
            self.settings_dialog.lift()
            self.settings_dialog.focus()

    def open_prompt_builder(self):
        """Opens the prompt builder popup window."""
        if not hasattr(self, 'prompt_builder_popup') or not self.prompt_builder_popup.winfo_exists():
            self.prompt_builder_popup = SystemPromptBuilderPopup(self, self.theme_manager, self.language_manager, self.snapshot_loader)
            self.prompt_builder_popup.focus()
        else:
            self.prompt_builder_popup.lift()
            self.prompt_builder_popup.focus()

    def save_component_from_builder(self, builder_popup: 'ComponentBuilderPopup'):
        component_name = builder_popup.component_name_entry.get().strip()
        if not component_name:
            self.update_status("Component name cannot be empty.", LYRN_ERROR)
            return

        build_prompt_dir = Path(SCRIPT_DIR) / "build_prompt"
        component_dir = build_prompt_dir / component_name
        component_dir.mkdir(parents=True, exist_ok=True)

        config = {}

        element_data = {}
        for widget_set in builder_popup.element_widgets:
            name = widget_set["name_entry"].get().strip()
            content = widget_set["content_box"].get("1.0", "end-1c")
            element_data[name] = content

        config["begin_bracket"] = element_data.get("begin_bracket", "")
        config["end_bracket"] = element_data.get("end_bracket", "")
        config["rwi_text"] = element_data.get("rwi_text", "")

        main_content = element_data.get("main_content", "")
        content_filename = f"{component_name}.txt"
        config["content_file"] = content_filename

        config_path = component_dir / "config.json"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            self.update_status(f"Error saving config for {component_name}: {e}", LYRN_ERROR)
            return

        content_path = component_dir / content_filename
        try:
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(main_content)
        except IOError as e:
            self.update_status(f"Error saving content for {component_name}: {e}", LYRN_ERROR)
            return

        components_path = build_prompt_dir / "components.json"
        components = self.snapshot_loader._load_json_file(str(components_path)) or []

        component_exists = False
        for comp in components:
            if comp["name"] == component_name:
                component_exists = True
                break

        if not component_exists:
            new_order = max([c.get('order', 0) for c in components] + [0]) + 1
            components.append({
                "name": component_name,
                "order": new_order,
                "active": True
            })

        try:
            with open(components_path, 'w', encoding='utf-8') as f:
                json.dump(components, f, indent=2)
        except IOError as e:
            self.update_status(f"Error updating components.json: {e}", LYRN_ERROR)
            return

        self.update_status(f"Component '{component_name}' saved successfully.", LYRN_SUCCESS)

    def delete_component_by_name(self, component_name: str):
        build_prompt_dir = Path(SCRIPT_DIR) / "build_prompt"

        components_path = build_prompt_dir / "components.json"
        components = self.snapshot_loader._load_json_file(str(components_path)) or []

        updated_components = [comp for comp in components if comp.get("name") != component_name]

        try:
            with open(components_path, 'w', encoding='utf-8') as f:
                json.dump(updated_components, f, indent=2)
        except IOError as e:
            self.update_status(f"Error updating components.json: {e}", LYRN_ERROR)
            return

        component_dir = build_prompt_dir / component_name
        if component_dir.exists() and component_dir.is_dir():
            try:
                shutil.rmtree(component_dir)
            except OSError as e:
                self.update_status(f"Error deleting directory {component_dir}: {e}", LYRN_ERROR)
                return

        self.update_status(f"Component '{component_name}' deleted successfully.", LYRN_SUCCESS)

    def open_personality_popup(self):
        """Opens the personality editor popup window."""
        if not hasattr(self, 'personality_popup') or not self.personality_popup.winfo_exists():
            self.personality_popup = PersonalityPopup(self, self.theme_manager)
            self.personality_popup.focus()
        else:
            self.personality_popup.lift()
            self.personality_popup.focus()

    def reload_master_prompt(self):
        """
        Loads the master prompt using the snapshot loader and caches it.
        This respects the lock file status.
        """
        if self.snapshot_loader:
            self.master_prompt_content = self.snapshot_loader.load_base_prompt()
            print("Master prompt reloaded and cached.")
            self.update_status("Master prompt loaded into memory.", LYRN_INFO)
        else:
            self.update_status("Snapshot loader not ready, cannot load prompt.", LYRN_ERROR)

    def refresh_prompt_from_mode(self):
        """Rebuilds the master prompt from components and reloads it."""
        if self.snapshot_loader:
            self.snapshot_loader.build_master_prompt_from_components()
            self.update_status("Master prompt rebuilt from current components.", LYRN_SUCCESS)
            # Immediately reload the newly built prompt into the cache
            self.reload_master_prompt()
        else:
            self.update_status("Snapshot loader not initialized.", LYRN_ERROR)

    def open_job_watcher_popup(self):
        """Opens the job watcher popup window."""
        if not hasattr(self, 'job_watcher_popup') or not self.job_watcher_popup.winfo_exists():
            self.job_watcher_popup = JobWatcherPopup(self, self.automation_controller, self.theme_manager, self.language_manager, self.cycle_manager)
            # Refresh the cycle list in the main UI when opening the popup
            self.refresh_active_cycle_selector()
            self.job_watcher_popup.focus()
        else:
            self.refresh_active_cycle_selector()
            self.job_watcher_popup.lift()
            self.job_watcher_popup.focus()

    def open_oss_tool_popup(self):
        """Opens the tool editor popup window."""
        if not hasattr(self, 'oss_tool_popup') or not self.oss_tool_popup.winfo_exists():
            self.oss_tool_popup = OSSToolPopup(self, self.oss_tool_manager, self.theme_manager, self.language_manager)
            self.oss_tool_popup.focus()
        else:
            self.oss_tool_popup.lift()
            self.oss_tool_popup.focus()

    def open_memory_popup(self):
        """Opens the memory manager popup window."""
        if not hasattr(self, 'memory_popup') or not self.memory_popup.winfo_exists():
            self.memory_popup = MemoryPopup(self, self.theme_manager, self.language_manager)
            self.memory_popup.focus()
        else:
            self.memory_popup.lift()
            self.memory_popup.focus()

    def toggle_log_viewer(self):
        """Creates, shows, or focuses the LLM log viewer window."""
        # If the popup doesn't exist or has been destroyed, create it.
        if not hasattr(self, 'log_viewer_popup') or not self.log_viewer_popup.winfo_exists():
            self.log_viewer_popup = LogViewerPopup(self, self.log_queue, self.settings_manager, self.theme_manager)
            self.log_viewer_popup.focus()
        else:
            # If it exists, bring it to the front and show it if it was withdrawn.
            self.log_viewer_popup.deiconify()
            self.log_viewer_popup.lift()
            self.log_viewer_popup.focus()

    def toggle_model_load(self):
        """Toggles between loading and offloading the model."""
        if self.llm is None:
            self.reload_model_full()
        else:
            self.offload_model()

    def reload_model_full(self):
        """Full model reload with proper memory cleanup"""
        self.update_status("Reloading model (full cleanup)...", LYRN_WARNING)
        threading.Thread(target=self._reload_model_full_thread, daemon=True).start()

    def offload_model(self):
        """Offloads the model to free up system resources."""
        if self.llm is None:
            self.update_status("Model is already offloaded.", LYRN_INFO)
            return

        self.update_status("Offloading model...", LYRN_WARNING)
        self.set_model_status("Off")

        del self.llm
        self.llm = None
        gc.collect() # Force garbage collection

        # Update toggle button
        if hasattr(self, 'model_toggle_button'):
            self.model_toggle_button.configure(text="Load Model", fg_color=self.theme_manager.get_color("primary"))

        self.stream_queue.put(('status_update', 'Model Offloaded', LYRN_SUCCESS))

    def _reload_model_full_thread(self):
        """Full model reload in separate thread with cleanup"""
        try:
            # Force cleanup of existing model
            if hasattr(self, 'llm') and self.llm is not None:
                print("Performing full model cleanup...")
                del self.llm
                self.llm = None

                # Force garbage collection and memory cleanup
                gc.collect()

                # Additional cleanup for llama-cpp-python
                import ctypes
                libc = ctypes.CDLL("libc.so.6")
                libc.malloc_trim(0)

                # Wait a moment for cleanup
                time.sleep(2)

            # Reset metrics
            if hasattr(self, 'metrics'):
                self.metrics.reset_metrics()

            # Reload model
            self.setup_model()

            # Update UI
            self.stream_queue.put(('status_update', 'Model reloaded successfully', LYRN_SUCCESS))
            self.stream_queue.put(('metrics_reset', ''))

        except Exception as e:
            self.stream_queue.put(('status_update', f'Model reload failed: {e}', LYRN_ERROR))

    def force_memory_cleanup(self):
        """Force memory cleanup"""
        try:
            gc.collect()

            # Additional system-specific cleanup
            try:
                import ctypes
                if sys.platform == "linux":
                    libc = ctypes.CDLL("libc.so.6")
                    libc.malloc_trim(0)
                elif sys.platform == "win32":
                    kernel32 = ctypes.windll.kernel32
                    kernel32.SetProcessWorkingSetSize(-1, -1, -1)
            except:
                pass

            self.update_status("Memory cleanup completed", LYRN_SUCCESS)

        except Exception as e:
            print(f"Memory cleanup error: {e}")
            self.update_status("Memory cleanup failed", LYRN_ERROR)

    def test_model_performance(self):
        """
        Test model performance.
        NOTE: This function is temporarily disabled pending a refactor to support the new IPC model.
        """
        if True:
            self.update_status("Performance test is temporarily disabled.", LYRN_WARNING)
            return

    def run_selected_job_from_dropdown(self):
        """Runs the job selected in the right-sidebar dropdown."""
        job_name = self.job_dropdown.get()
        if not job_name or "No jobs" in job_name:
            self.update_status("No job selected to run.", LYRN_WARNING)
            return

        trigger_prompt = self.automation_controller.get_job_trigger(job_name)
        if trigger_prompt:
            self.execute_job_directly(job_name, trigger_prompt)
            self.update_status(f"Executing job: {job_name}", LYRN_ACCENT)
        else:
            self.update_status(f"Could not load trigger for job '{job_name}'.", LYRN_ERROR)

    def on_job_selected(self, job_name: str):
        """Handle manual job selection for testing."""
        if hasattr(self, 'automation_controller'):
            # Get the full job prompt with headers
            job_prompt = self.automation_controller.get_job_prompt(job_name, args={})
            if job_prompt:
                self.insert_job_text(job_prompt)
                self.update_status(f"Manual job loaded: {job_name}", LYRN_ACCENT)

    def _execute_reflection_job(self, job: Job):
        """Executes the reflection job, handling file saving and versioning."""
        args = job.args
        original_job_name = args.get("original_job_name", "unknown_job")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Create the reflections directory
        reflections_dir = Path(SCRIPT_DIR) / "reflections" / f"{original_job_name}_{timestamp}"
        reflections_dir.mkdir(parents=True, exist_ok=True)

        # 2. Save original outputs and reflection notes
        try:
            # Save the original job output that was reflected upon
            with open(reflections_dir / "original_output.txt", "w", encoding="utf-8") as f:
                f.write(args.get("job_output", ""))

            # The 'reflection_cycle_job' itself is run by the main generation logic.
            # We need to get the *result* of that job here. For now, we'll simulate this
            # by running the LLM again. In a future refactor, this should be more integrated.
            self.display_colored_message(f"\n--- Running Reflection For: {original_job_name} ---\n", "system_text")

            # This is where we call the LLM to perform the reflection.
            # We'll construct a prompt similar to how the main chat works.
            reflection_prompt = self.automation_controller.get_job_prompt("reflection_cycle_job", args)

            messages = [
                {"role": "system", "content": self.snapshot_loader.load_base_prompt()},
                {"role": "user", "content": reflection_prompt}
            ]

            active = self.settings_manager.settings["active"]
            handler = StreamHandler(self.stream_queue, self.metrics)

            stream = self.llm.create_chat_completion(
                prompt=your_prompt,
                max_tokens=active["max_tokens"],
                temperature=active["temperature"],
                top_p=active["top_p"],
                stream=True
            )

            response_parts = []
            for token_data in stream:
                if 'choices' in token_data and len(token_data['choices']) > 0:
                    delta = token_data['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        response_parts.append(content)

            reflection_result = ''.join(response_parts)

            with open(reflections_dir / "reflection_notes.txt", "w", encoding="utf-8") as f:
                f.write(reflection_result)

            self.display_colored_message(f"Reflection complete. Notes saved to {reflections_dir}\n", "system_text")

        except Exception as e:
            print(f"Error during reflection file saving: {e}")
            self.update_status("Error saving reflection files.", LYRN_ERROR)

        # 3. Handle automatic prompt updates
        if args.get("auto_update", False):
            self.display_colored_message("Attempting to automatically update prompt...\n", "system_text")

            # This would be another LLM call to generate a new prompt.
            # For now, we'll simulate it.
            new_prompt_content = f"# Prompt for {original_job_name} v2\n" + self.automation_controller.job_definitions.get(original_job_name, "") + "\n# Updated by reflection."

            # Save new prompt with versioning
            jobs_dir = Path(SCRIPT_DIR) / "automation" / "jobs"
            new_prompt_path = jobs_dir / f"{original_job_name}_v2.txt" # Simplified versioning

            try:
                with open(new_prompt_path, "w", encoding="utf-8") as f:
                    f.write(new_prompt_content)

                # Save changelog
                changelog_path = Path(SCRIPT_DIR) / "reflections" / "reflection_changelog.txt"
                with open(changelog_path, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] Job '{original_job_name}' updated to v2. See folder: {reflections_dir.name}\n")

                self.display_colored_message(f"Prompt updated and saved to {new_prompt_path.name}\n", "success")

                # 4. Handle auto-continuation
                if args.get("auto_continue", False):
                    self.display_colored_message("Auto-continuing job with updated prompt...\n", "system_text")
                    # Re-add the original job to the queue, which will now use the new prompt if named correctly.
                    # This part needs careful implementation to ensure the right version is picked up.
                    # For now, we assume the system will just use the latest file for a given job name.
                    self.automation_controller.add_job(name=original_job_name)


            except Exception as e:
                print(f"Error updating prompt: {e}")
                self.update_status("Error updating prompt.", LYRN_ERROR)


    def _maybe_run_automated_job(self):
        """Checks for and runs the next job in the queue if the system is idle."""
        if self.is_thinking: # Don't run a job if the model is already running
            return

        if self.automation_controller.has_pending_jobs():
            next_job = self.automation_controller.get_next_job()
            if next_job:
                print(f"Executing automated job: {next_job.name}")

                if next_job.name == "reflection_cycle_job":
                    self._execute_reflection_job(next_job)
                else:
                    # For now, this just displays the job prompt for verification.
                    # Later, this will trigger a full LLM cycle for the job.
                    self.display_colored_message(f"\n--- Running Automated Job: {next_job.name} ---\n", "system_text")
                    self.display_colored_message(next_job.prompt, "system_text")
                    self.display_colored_message(f"\n--- Job Complete: {next_job.name} ---\n", "system_text")
                    self._handle_job_completion(next_job.name)

                # Check if more jobs are pending and run them if so
                self.after(100, self._maybe_run_automated_job)

    def _get_job_run_counts(self) -> Dict[str, int]:
        """Reads the job run counts from the JSON file."""
        counts_path = Path(SCRIPT_DIR) / "automation" / "job_run_counts.json"
        if not counts_path.exists():
            return {}
        try:
            with open(counts_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_job_run_counts(self, counts: Dict[str, int]):
        """Saves the job run counts to the JSON file."""
        counts_path = Path(SCRIPT_DIR) / "automation" / "job_run_counts.json"
        try:
            with open(counts_path, 'w', encoding='utf-8') as f:
                json.dump(counts, f, indent=2)
        except IOError as e:
            print(f"Error saving job run counts: {e}")

    def _handle_job_completion(self, job_name: str):
        """Increments the run count for a job and triggers reflection if the batch size is met."""
        # This function should only be called for non-reflection jobs.
        if job_name == "reflection_cycle_job":
            return

        counts = self._get_job_run_counts()
        new_count = counts.get(job_name, 0) + 1
        counts[job_name] = new_count
        self._save_job_run_counts(counts)

        try:
            batch_size_str = self.job_watcher_popup.reflection_batch_size_entry.get()
            batch_size = int(batch_size_str)
        except (ValueError, AttributeError):
            # If the entry is invalid or the popup isn't open, don't trigger reflection.
            return

        if batch_size > 0 and new_count >= batch_size:
            print(f"Job '{job_name}' has reached its batch size of {batch_size}. Triggering reflection.")
            # Reset the counter
            counts[job_name] = 0
            self._save_job_run_counts(counts)

            # Queue the reflection job
            # We need to gather the necessary data from the UI again.
            if hasattr(self, 'job_watcher_popup') and self.job_watcher_popup.winfo_exists():
                self.job_watcher_popup.run_reflection_manually()
            else:
                print("Warning: Job watcher popup is not open. Cannot trigger automated reflection.")

    def insert_job_text(self, text: str):
        """Insert job text into input box"""
        self.input_box.delete("0.0", "end")
        self.input_box.insert("0.0", text)

    def copy_last_response(self):
        """Copies the last assistant response to the clipboard."""
        if hasattr(self, 'last_assistant_response') and self.last_assistant_response:
            self.clipboard_clear()
            self.clipboard_append(self.last_assistant_response)
            self.update_status("Last response copied to clipboard", LYRN_SUCCESS)
        else:
            self.update_status("No response to copy yet", LYRN_WARNING)

    def create_chat_context_menu(self):
        """Creates the right-click context menu for the chat display."""
        self.chat_context_menu = tk.Menu(self, tearoff=0)
        self.chat_context_menu.add_command(label="Quote to Context", command=self.quote_selected_text)

    def show_chat_context_menu(self, event):
        """Shows the chat context menu if text is selected."""
        if self.chat_display.tag_ranges("sel"):
            self.chat_context_menu.tk_popup(event.x_root, event.y_root)

    def quote_selected_text(self):
        """Gets the selected text and saves it to quotes.txt."""
        try:
            selected_text = self.chat_display.get("sel.first", "sel.last")
            if selected_text:
                self.episodic_memory_manager.add_to_quotes(selected_text)
                self.update_status("Text quoted to quotes.txt", LYRN_SUCCESS)
        except tk.TclError:
            self.update_status("No text selected to quote.", LYRN_WARNING)

    def send_message_from_event(self, event=None):
        """Wrapper to send message from a binding and prevent event propagation."""
        self.send_message()
        return "break"

    def send_message(self):
        """Send user message and generate response"""
        user_text = self.input_box.get("0.0", "end").strip()
        if not user_text:
            return

        self.last_user_input = user_text

        if not self.llm:
            self.update_status("No model loaded", LYRN_ERROR)
            return

        # Get chat history BEFORE logging the new message
        history_messages = self.chat_manager.get_chat_history_messages() if self.chat_manager else []

        # Start a new structured log for this interaction
        self.chat_logger.start_log()
        self.chat_logger.append_log("USER", user_text)

        # Verbatim Memory: Write input and signal watcher
        try:
            formatted_input = f"#Active_Chat_Pair_Start#\n{user_text}\n#Active_Chat_Pair_End#"
            with open(os.path.join(SCRIPT_DIR, "temp_chat_turn.txt"), 'w', encoding='utf-8') as f:
                f.write(formatted_input)

            # Clear temp job responses
            with open(os.path.join(SCRIPT_DIR, "temp_job_responses.txt"), 'w', encoding='utf-8') as f:
                f.write("")

            if self.settings_manager.get_setting("save_chat_history", True):
                verbatim_flag_path = os.path.join(SCRIPT_DIR, "global_flags", "verbatim_state.txt")
                with open(verbatim_flag_path, 'w', encoding='utf-8') as f:
                    f.write("input_ready")
        except Exception as e:
            print(f"Error updating verbatim memory input: {e}")

        # Display user message
        self.display_colored_message(f"You: {user_text}\n", "user_text")

        # Clear input and disable send
        self.input_box.delete("0.0", "end")
        self.send_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.stop_generation = False # Reset flag at the start of a new generation
        self._write_llm_status("busy")

        # The old save_chat_message is now deprecated.
        if self.chat_manager:
            self.chat_manager.manage_chat_history_files()

        # Display thinking message and start response generation
        self.display_colored_message("Assistant: Thinking...\n", "thinking_text")
        self.is_thinking = True

        self.set_model_status("Automation") # Orange for automation
        threading.Thread(target=self.run_automation_loop, args=(user_text, history_messages), daemon=True).start()
        self.update_status("Running automation...", LYRN_INFO)

    def run_automation_loop(self, user_text: str, history_messages: List[Dict[str, str]]):
        """Executes the defined sequence of jobs and then the final output."""
        try:
            # 1. Read Job Sequence
            sequence_path = os.path.join(SCRIPT_DIR, "automation", "job_sequence.txt")
            triggers = []
            if os.path.exists(sequence_path):
                with open(sequence_path, 'r', encoding='utf-8') as f:
                    triggers = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            # 2. Execute Sequence
            for trigger in triggers:
                if self.stop_generation:
                    break
                self.update_status(f"Running automation job: {trigger}", LYRN_ACCENT)

                # Passing the trigger as the "user_text" effectively makes it the last instruction the LLM sees.
                job_response = self.get_response_for_job(trigger)

                # Append to temp_job_responses.txt
                with open(os.path.join(SCRIPT_DIR, "temp_job_responses.txt"), 'a', encoding='utf-8') as f:
                    f.write(f"\n{job_response}\n")

            if not self.stop_generation:
                # 3. Final Output
                self.update_status("Generating final response...", LYRN_INFO)
                final_trigger = "##RUN_JOB: final_output##"
                final_response = self.get_response_for_job(final_trigger)

                # 4. Handle Final Output
                formatted_output = f"#final_output_start#\n{final_response}\n#final_output_end#"
                with open(os.path.join(SCRIPT_DIR, "temp_chat_turn.txt"), 'a', encoding='utf-8') as f:
                    f.write("\n" + formatted_output)

                # Signal Watcher
                verbatim_flag_path = os.path.join(SCRIPT_DIR, "global_flags", "verbatim_state.txt")
                with open(verbatim_flag_path, 'w', encoding='utf-8') as f:
                    f.write("output_ready")

                # Display
                self.remove_thinking_message()
                self.display_colored_message(final_response, "assistant_text")

                # Logging
                self.chat_logger.append_log("RESPONSE", final_response)

            # Cleanup
            # Clear temp_job_responses.txt
            with open(os.path.join(SCRIPT_DIR, "temp_job_responses.txt"), 'w', encoding='utf-8') as f:
                f.write("")

            self.is_thinking = False
            if not self.stop_generation:
                self.update_status("Response complete", LYRN_SUCCESS)
            else:
                self.update_status("Generation stopped", LYRN_WARNING)

            self.set_model_status("Ready")
            self.stream_queue.put(('enable_send', ''))

        except Exception as e:
            print(f"Error in automation loop: {e}")
            self.stream_queue.put(('error', str(e)))

    def get_response_for_job(self, user_text: str) -> str:
        """Generate AI response for a job and return it as a string."""
        try:
            # Use the cached prompt
            full_prompt = self.master_prompt_content

            messages = [{"role": "system", "content": full_prompt}]

            # Inject Deltas (if enabled)
            if self.settings_manager.get_setting("enable_deltas", True):
                delta_content = self.delta_manager.get_delta_content()
                if delta_content:
                    messages.append({"role": "system", "content": delta_content})

            # Add Chat History (if enabled)
            if self.settings_manager.get_setting("enable_chat_history", True):
                history_messages = self.chat_manager.get_chat_history_messages() if self.chat_manager else []
                messages.extend(history_messages)

            # Inject Temp Input
            try:
                with open(os.path.join(SCRIPT_DIR, "temp_chat_turn.txt"), 'r', encoding='utf-8') as f:
                    input_content = f.read()
                if input_content:
                    messages.append({"role": "system", "content": input_content})
            except Exception:
                pass

            # Inject Temp Job Responses
            try:
                with open(os.path.join(SCRIPT_DIR, "temp_job_responses.txt"), 'r', encoding='utf-8') as f:
                    responses_content = f.read()
                if responses_content:
                    messages.append({"role": "system", "content": responses_content})
            except Exception:
                pass

            # Append the Job Trigger
            messages.append({"role": "user", "content": user_text})

            active = self.settings_manager.settings["active"]

            # Start streaming with enhanced metrics capture
            stream = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=active.get("max_tokens", 2048),
                temperature=active["temperature"],
                top_p=active["top_p"],
                top_k=active.get("top_k", 40),
                stream=True
            )

            response_parts = []
            for token_data in stream:
                if 'choices' in token_data and len(token_data['choices']) > 0:
                    delta = token_data['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        response_parts.append(content)

            # Save complete response
            complete_response = ''.join(response_parts)
            return complete_response

        except Exception as e:
            self.stream_queue.put(('error', str(e)))
            return f"Error generating response: {e}"

    def stop_generation_process(self):
        """Sets the flag to stop the generation thread."""
        self.stop_generation = True
        self.update_status("Stopping generation...", LYRN_WARNING)

    def remove_thinking_message(self):
        """Finds and removes the 'Thinking...' message from the chat display."""
        self.chat_display.configure(state="normal")
        # Search for the "Thinking..." message starting from the end.
        pos = self.chat_display.search("Assistant: Thinking...", "end", backwards=True, stopindex="1.0")
        if pos:
            # If found, delete from that position to the end of the textbox.
            # This is robust enough to clear the message even if other text arrived.
            self.chat_display.delete(pos, "end")
        self.chat_display.configure(state="disabled")

    def generate_response(self, user_text: str, history_messages: List[Dict[str, str]]):
        """Generate AI response with enhanced handling and metrics capture."""
        try:
            # Use the cached prompt
            full_prompt = self.master_prompt_content

            messages = [{"role": "system", "content": full_prompt}]

            # Inject Deltas (if enabled)
            if self.settings_manager.get_setting("enable_deltas", True):
                delta_content = self.delta_manager.get_delta_content()
                if delta_content:
                    messages.append({"role": "system", "content": delta_content})

            # Add Chat History (if enabled)
            if self.settings_manager.get_setting("enable_chat_history", True):
                if history_messages:
                    messages.extend(history_messages)

            # Inject Temp Input
            try:
                with open(os.path.join(SCRIPT_DIR, "temp_chat_turn.txt"), 'r', encoding='utf-8') as f:
                    input_content = f.read()
                if input_content:
                    messages.append({"role": "system", "content": input_content})
            except Exception:
                pass

            # Inject Temp Job Responses
            try:
                with open(os.path.join(SCRIPT_DIR, "temp_job_responses.txt"), 'r', encoding='utf-8') as f:
                    responses_content = f.read()
                if responses_content:
                    messages.append({"role": "system", "content": responses_content})
            except Exception:
                pass

            # Append the User Input / Trigger
            messages.append({"role": "user", "content": user_text})

            active = self.settings_manager.settings["active"]
            handler = StreamHandler(self.stream_queue, self.metrics, self.role_mappings, self.role_color_tags)

            # Setup stderr capture
            log_capture_buffer = io.StringIO()

            with contextlib.redirect_stderr(log_capture_buffer):
                # Start streaming with enhanced metrics capture
                stream = self.llm.create_chat_completion(
                    messages=messages,
                    max_tokens=active.get("max_tokens", 2048),
                    temperature=active["temperature"],
                    top_p=active["top_p"],
                    top_k=active.get("top_k", 40),
                    stream=True
                )

                response_parts = []
                for token_data in stream:
                    if self.stop_generation:
                        print("Generation stopped by user.")
                        break
                    handler.handle_token(token_data)
                    if 'choices' in token_data and len(token_data['choices']) > 0:
                        delta = token_data['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            response_parts.append(content)

            # After stream, parse the captured logs
            log_output = log_capture_buffer.getvalue()
            if log_output:
                # Print the raw log to stderr so it appears in the log viewer
                print(log_output, file=sys.stderr)
                self.metrics.parse_llama_logs(log_output)
                self.stream_queue.put(('metrics_update', ''))

                # Send token count info to the queue
                prompt_tokens = self.metrics.prompt_tokens
                response_tokens = self.metrics.eval_tokens
                token_info = f"\n(Prompt: {prompt_tokens} tokens, Response: {response_tokens} tokens)\n\n"
                self.stream_queue.put(('token_count_info', token_info))

            # Save complete response
            complete_response = ''.join(response_parts)
            self.last_assistant_response = complete_response
            # The old save_chat_message is now deprecated.
            # self.save_chat_message("assistant", complete_response)

        except Exception as e:
            self.stream_queue.put(('error', str(e)))
        finally:
            self.stream_queue.put(('enable_send', ''))

    # def save_chat_message(self, role: str, content: str) -> Optional[str]:
    #     """
    #     Saves a chat message to a file in the format expected by the system
    #     and returns the full path to the file.
    #     """
    #     if not self.settings_manager.settings:
    #         return None

    #     chat_dir = self.settings_manager.settings["paths"].get("chat", "")
    #     if not chat_dir:
    #         print("Chat directory not configured in settings.")
    #         return None

    #     os.makedirs(chat_dir, exist_ok=True)
    #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    #     filename = f"chat_{timestamp}.txt"
    #     filepath = os.path.join(chat_dir, filename)

    #     try:
    #         with open(filepath, 'w', encoding='utf-8') as f:
    #             if role == "user":
    #                 # The 'model' header acts as a marker for where the response begins
    #                 f.write(f"user\n{content}\n\nmodel\n")
    #             else:
    #                 # Assistant messages are just saved directly for logging
    #                 f.write(f"assistant\n{content}\n")
    #         return filepath
    #     except Exception as e:
    #         print(f"Error saving chat message: {e}")
    #         return None

    def process_queue(self):
        """Process messages from stream queue with enhanced handling"""
        try:
            while True:
                try:
                    message = self.stream_queue.get_nowait()

                    if message[0] == 'token':
                        if self.is_thinking:
                            self.remove_thinking_message()
                            self.is_thinking = False

                        _, content, internal_role = message

                        if internal_role == "final_output":
                            tag = self.role_color_tags.get("final_output", "assistant_text")
                            if not hasattr(self, '_assistant_started'):
                                self.display_colored_message("\n\nAssistant: ", tag)
                                self._assistant_started = True
                            self.display_colored_message(content, tag)

                        elif internal_role == "thinking_process":
                            if self.settings_manager.get_setting("show_thinking_text", True):
                                tag = self.role_color_tags.get("thinking_process", "thinking_text")
                                if not hasattr(self, '_thinking_started'):
                                    self.display_colored_message("\n\nThinking: ", tag)
                                    self._thinking_started = True
                                self.display_colored_message(content, tag)

                    elif message[0] == 'finished':
                        if self.is_thinking: # Handles empty responses
                            self.remove_thinking_message()
                            self.is_thinking = False

                        self.update_status("Response complete", LYRN_SUCCESS)
                        self.set_model_status("Ready")
                        if hasattr(self, '_assistant_started'):
                            delattr(self, '_assistant_started')
                        if hasattr(self, '_thinking_started'):
                            delattr(self, '_thinking_started')

                        # Save the complete response to the structured journal log
                        self.chat_logger.append_log("RESPONSE", message[1])

                        # Verbatim Memory: Write output and signal watcher
                        try:
                            formatted_output = f"###OUTPUT_START###\n{message[1]}\n###_END###"
                            with open(os.path.join(SCRIPT_DIR, "temp_chat_turn.txt"), 'w', encoding='utf-8') as f:
                                f.write(formatted_output)

                            if self.settings_manager.get_setting("save_chat_history", True):
                                verbatim_flag_path = os.path.join(SCRIPT_DIR, "global_flags", "verbatim_state.txt")
                                with open(verbatim_flag_path, 'w', encoding='utf-8') as f:
                                    f.write("output_ready")
                        except Exception as e:
                            print(f"Error updating verbatim memory output: {e}")

                        # Episodic memory saving has been replaced by Verbatim Chat system

                        # Check for pending jobs now that the model is idle
                        self._maybe_run_automated_job()

                    elif message[0] == 'show_loading':
                        self.show_loading_indicator()

                    elif message[0] == 'hide_loading':
                        self.hide_loading_indicator()

                    elif message[0] == 'token_count_info':
                        _, info_text = message
                        self.display_colored_message(info_text, "system_text")

                    elif message[0] == 'metrics_update':
                        self.update_enhanced_metrics()

                    elif message[0] == 'metrics_reset':
                        self.reset_metrics_display()

                    elif message[0] == 'error':
                        if self.is_thinking:
                            self.remove_thinking_message()
                            self.is_thinking = False
                        self.display_colored_message(f"Error: {message[1]}\n\n", "error")
                        self.update_status("Error occurred", LYRN_ERROR)

                    elif message[0] == 'enable_send':
                        self.send_btn.configure(state="normal")
                        self.stop_btn.configure(state="disabled")
                        if self.stop_generation:
                             self.update_status("Generation stopped.", LYRN_WARNING)
                             self.set_model_status("Ready")
                        self._write_llm_status("idle")
                        # Also check for jobs when the send button is re-enabled
                        self._maybe_run_automated_job()

                    elif message[0] == 'inject_trigger':
                        _, content = message
                        self.input_box.delete("1.0", "end")
                        self.input_box.insert("1.0", content)
                        self.send_message()

                    elif message[0] == 'status_update':
                        self.update_status(message[1], message[2])

                    elif message[0] == 'system_stats':
                        if hasattr(self, 'update_system_gauges'):
                            self.update_system_gauges(message[1])

                    elif message[0] == 'initialization_complete':
                        self._on_initialization_complete()

                except queue.Empty:
                    break

        except Exception as e:
            print(f"Error processing queue: {e}")

        self.after(50, self.process_queue)

    def update_job_dropdown(self):
        """Populates the manual job selection dropdown."""
        if hasattr(self, 'job_dropdown') and self.automation_controller:
            job_names = list(self.automation_controller.job_definitions.keys())
            self.job_dropdown.configure(values=job_names if job_names else ["No jobs loaded"])
            if not job_names:
                self.job_dropdown.set("No jobs loaded")
            else:
                self.job_dropdown.set(job_names[0])
        elif hasattr(self, 'job_dropdown'):
            self.job_dropdown.configure(values=["Loading..."])
            self.job_dropdown.set("Loading...")

    def update_oss_tool_dropdown(self):
        """Populates the manual oss tool selection dropdown."""
        if hasattr(self, 'oss_tool_dropdown') and self.oss_tool_manager:
            tool_names = [tool.name for tool in self.oss_tool_manager.get_all_tools()]
            self.oss_tool_dropdown.configure(values=tool_names if tool_names else ["No tools loaded"])
            if not tool_names:
                self.oss_tool_dropdown.set("No tools loaded")
            else:
                self.oss_tool_dropdown.set(tool_names[0])
        elif hasattr(self, 'oss_tool_dropdown'):
            self.oss_tool_dropdown.configure(values=["Loading..."])
            self.oss_tool_dropdown.set("Loading...")

    def run_selected_oss_tool(self):
        """Runs the oss tool selected in the right-sidebar dropdown."""
        tool_name = self.oss_tool_dropdown.get()
        if not tool_name or "No tools" in tool_name:
            self.update_status("No tool selected to run.", LYRN_WARNING)
            return

        tool_prompt = f"Please use the '{tool_name}' tool."
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", tool_prompt)
        self.send_message()
        self.update_status(f"Executing tool: {tool_name}", LYRN_ACCENT)



    def update_enhanced_metrics(self):
        """Update enhanced metrics display with visual indicators"""
        if not hasattr(self, 'metrics'):
            return

        try:
            # Update labels
            self.kv_label.configure(text=f"KV Cache: {self.metrics.kv_cache_reused:,} tokens")
            self.prompt_label.configure(text=f"Prompt: {self.metrics.prompt_tokens:,} tokens")
            self.response_label.configure(text=f"Response: {self.metrics.eval_tokens:,} tokens")
            self.eval_label.configure(text=f"Generation: {self.metrics.eval_speed:.1f} tok/s")
            n_ctx = self.settings_manager.settings.get("active", {}).get("n_ctx", 1)
            self.total_label.configure(text=f"Total: {self.metrics.total_tokens:,} / {n_ctx:,} tokens")

            # Update progress bar for KV cache and Total Tokens
            if n_ctx > 0:
                kv_ratio = min(self.metrics.kv_cache_reused / n_ctx, 1.0)
                self.kv_progress.set(kv_ratio)

                total_ratio = min(self.metrics.total_tokens / n_ctx, 1.0)
                self.total_progress.set(total_ratio)

            # Update time labels
            self.generation_time_label.configure(text=f"Gen Time: {self.format_ms_to_min_sec(self.metrics.generation_time_ms)}")
            self.tokenization_time_label.configure(text=f"Token Time: {self.format_ms_to_min_sec(self.metrics.tokenization_time_ms)}")

        except Exception as e:
            print(f"Error updating metrics: {e}")

    def reset_metrics_display(self):
        """Reset metrics display"""
        try:
            self.kv_label.configure(text="KV Cache: 0 tokens")
            self.prompt_label.configure(text="Prompt: 0 tokens")
            self.eval_label.configure(text="Generation: 0 tok/s")
            self.total_label.configure(text="Total: 0 tokens")
            self.kv_progress.set(0)
        except Exception as e:
            print(f"Error resetting metrics: {e}")

    def update_status(self, message: str, color: str = None):
        """Update enhanced status display"""
        if not hasattr(self, 'status_textbox'):
            return

        try:
            color = color or LYRN_SUCCESS

            self.status_textbox.configure(state="normal")
            self.status_textbox.delete("1.0", "end")
            self.status_textbox.insert("1.0", message)
            self.status_textbox.configure(state="disabled", text_color=color)

        except Exception as e:
            print(f"Error updating status: {e}")

    def clear_chat(self):
        """Clear chat display and the saved chat file."""
        try:
            self.chat_display.configure(state="normal")
            self.chat_display.delete("0.0", "end")
            self.chat_display.configure(state="disabled")

            # Also clear the saved chat file
            active_chat_path = os.path.join(SCRIPT_DIR, "active_chat.txt")
            if os.path.exists(active_chat_path):
                os.remove(active_chat_path)

            self.update_status("Chat display cleared", LYRN_INFO)
        except Exception as e:
            print(f"Error clearing chat: {e}")

    def open_chat_folder(self):
        """Opens the Chat_History directory in the system's file explorer."""
        chat_dir = os.path.join(SCRIPT_DIR, "Chat_History")
        if not os.path.exists(chat_dir):
            os.makedirs(chat_dir, exist_ok=True)

        try:
            if sys.platform == "win32":
                os.startfile(os.path.realpath(chat_dir))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", chat_dir])
            else:
                subprocess.Popen(["xdg-open", chat_dir])
            self.update_status("Opened Chat History folder.", LYRN_INFO)
        except Exception as e:
            self.update_status(f"Error opening folder: {e}", LYRN_ERROR)
            print(f"Error opening folder: {e}")

    def start_new_session(self):
        """Signals the verbatim memory watcher to start a new session."""
        from confirmation_dialog import ConfirmationDialog
        confirmed, _ = ConfirmationDialog.show(
            self, self.theme_manager,
            title="Confirm New Session",
            message="Are you sure you want to archive the current session and start a new one?"
        )
        if confirmed:
            try:
                verbatim_flag_path = os.path.join(SCRIPT_DIR, "global_flags", "verbatim_state.txt")
                with open(verbatim_flag_path, 'w', encoding='utf-8') as f:
                    f.write("force_new_session")
                self.update_status("New session signaled.", LYRN_SUCCESS)
            except Exception as e:
                self.update_status(f"Error signaling new session: {e}", LYRN_ERROR)

    def clear_chat_folder(self):
        """Deletes all files in the chat directory after confirmation."""
        from confirmation_dialog import ConfirmationDialog

        prefs = self.settings_manager.ui_settings.get("confirmation_preferences", {})
        if prefs.get("clear_chat_folder"):
            confirmed = True
        else:
            confirmed, dont_ask_again = ConfirmationDialog.show(
                self,
                self.theme_manager,
                title="Confirm Clear Directory",
                message="Are you sure you want to permanently delete all saved chat logs?"
            )
            if dont_ask_again:
                prefs["clear_chat_folder"] = True
                self.settings_manager.ui_settings["confirmation_preferences"] = prefs
                self.settings_manager.save_settings()

        if not confirmed:
            self.update_status("Clear chat folder cancelled.", LYRN_INFO)
            return

        if not self.settings_manager.settings:
            self.update_status("Settings not loaded.", LYRN_ERROR)
            return

        chat_dir = self.settings_manager.settings["paths"].get("chat", "")
        if not chat_dir or not os.path.exists(chat_dir):
            self.update_status("Chat directory not configured or found.", LYRN_WARNING)
            return

        try:
            file_count = 0
            for filename in os.listdir(chat_dir):
                file_path = os.path.join(chat_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    file_count += 1
            self.update_status(f"Cleared {file_count} files from chat folder.", LYRN_SUCCESS)
            print(f"Cleared chat directory: {chat_dir}")
        except Exception as e:
            self.update_status("Error clearing chat folder.", LYRN_ERROR)
            print(f"Error clearing chat directory: {e}")

    def _watch_cycle_trigger_file(self):
        """Watches for the cycle trigger file and injects its content."""
        trigger_path = Path(SCRIPT_DIR) / "global_flags" / "cycle_trigger.txt"
        while True:
            try:
                if trigger_path.exists():
                    content = trigger_path.read_text(encoding='utf-8')
                    trigger_path.unlink()
                    self.stream_queue.put(('inject_trigger', content))
            except Exception as e:
                print(f"Error in cycle trigger watcher: {e}")
            time.sleep(0.2)

    def _write_llm_status(self, status: str):
        """Writes the LLM's current status to the flag file."""
        path = Path(SCRIPT_DIR) / "global_flags" / "llm_status.txt"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(status)
        except IOError:
            pass

    def refresh_active_cycle_selector(self):
        """Refreshes the active cycle selector dropdown in the main UI."""
        if hasattr(self, 'active_cycle_selector'):
            cycle_names = self.cycle_manager.get_cycle_names()
            self.active_cycle_selector.configure(values=cycle_names if cycle_names else [""])
            if not cycle_names:
                self.active_cycle_selector.set("")

    def toggle_cycle(self):
        """Starts or stops the selected cycle."""
        selected_cycle = self.active_cycle_selector.get()
        if not selected_cycle:
            self.update_status("No cycle selected to start.", LYRN_WARNING)
            return

        flag_path = Path(SCRIPT_DIR) / "global_flags" / "active_cycle.json"

        # Read current state
        current_state = {}
        if flag_path.exists():
            try:
                with open(flag_path, 'r', encoding='utf-8') as f:
                    current_state = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # If the selected cycle is running, stop it. Otherwise, start it.
        if current_state.get("name") == selected_cycle and current_state.get("status") == "running":
            # Stop the cycle
            new_state = {"name": selected_cycle, "status": "stopped"}
            self.cycle_toggle_button.configure(text="Start")
            self.update_status(f"Cycle '{selected_cycle}' stopped.", LYRN_INFO)
        else:
            # Start the cycle
            new_state = {"name": selected_cycle, "status": "running", "current_step": 0}
            self.cycle_toggle_button.configure(text="Stop")
            self.update_status(f"Cycle '{selected_cycle}' started.", LYRN_SUCCESS)

        # Write the new state
        try:
            with open(flag_path, 'w', encoding='utf-8') as f:
                json.dump(new_state, f, indent=2)
        except IOError as e:
            self.update_status(f"Error updating cycle state: {e}", LYRN_ERROR)


def main():
    """Main entry point for LYRN-AI v7.0"""
    log_queue = queue.Queue()
    redirector = ConsoleRedirector(log_queue)
    redirector.start()

    try:
        print("Starting LYRN-AI Interface v7.0...")
        print("Enhanced features: Multi-colored text, Live theming, Advanced metrics")
        print(f"CustomTkinter version: {ctk.__version__}")

        root = ctk.CTk()
        root.withdraw()

        app = LyrnAIInterface(master=root, log_queue=log_queue)
        root.mainloop()

    except ImportError as e:
        # Stop redirection to print to the actual console
        redirector.stop()
        print(f"Import error: {e}")
        print("Please install required packages:")
        print("pip install customtkinter llama-cpp-python pillow psutil pynvml")
        input("Press Enter to exit...")

    except Exception as e:
        # Stop redirection to print to the actual console
        redirector.stop()
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

    finally:
        redirector.stop()
        print("Application closed.")

if __name__ == "__main__":
    main()
