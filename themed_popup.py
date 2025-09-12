import os
import json
import customtkinter as ctk
from typing import List
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class ThemeManager:
    """Discovers, loads, and applies themes from the 'themes' directory."""
    def __init__(self):
        self.themes_dir = os.path.join(SCRIPT_DIR, "themes")
        self.themes = {}
        self.current_theme_name = "LYRN Dark"  # Fallback default
        self.current_colors = {}
        self.load_available_themes()

    def load_available_themes(self):
        """Scans the themes directory and loads all valid .json theme files."""
        if not os.path.exists(self.themes_dir):
            print(f"Warning: Themes directory not found at {self.themes_dir}. Creating it.")
            os.makedirs(self.themes_dir)
            return

        for filename in os.listdir(self.themes_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.themes_dir, filename), 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        if "name" in theme_data and "appearance_mode" in theme_data and "colors" in theme_data:
                            self.themes[theme_data["name"]] = theme_data
                            print(f"Loaded theme: {theme_data['name']}")
                        else:
                            print(f"Warning: Invalid theme file format in {filename}")
                except Exception as e:
                    print(f"Error loading theme file {filename}: {e}")

        if not self.themes:
            print("FATAL: No themes found in the 'themes' directory. The application cannot start without a theme.")
            return

    def get_theme_names(self) -> List[str]:
        """Returns a list of available theme names."""
        return sorted(list(self.themes.keys()))

    def get_current_theme_name(self) -> str:
        return self.current_theme_name

    def get_color(self, color_name: str, fallback: str = "#FF00FF") -> str:
        """Gets a color from the current theme, with a bright pink fallback for easy debugging."""
        return self.current_colors.get(color_name, fallback)

    def apply_theme(self, theme_name: str):
        """Applies a theme by name, setting appearance mode and updating colors."""
        if theme_name not in self.themes:
            print(f"Error: Theme '{theme_name}' not found. Applying default.")
            if not self.get_theme_names():
                print("FATAL: No themes available to apply.")
                return
            theme_name = self.get_theme_names()[0]

        theme_data = self.themes[theme_name]
        self.current_theme_name = theme_name
        self.current_colors = theme_data.get("colors", {})

        appearance_mode = theme_data.get("appearance_mode", "dark")
        ctk.set_appearance_mode(appearance_mode)

        print(f"Theme '{theme_name}' applied with {appearance_mode} mode.")


class ThemedPopup(ctk.CTkToplevel):
    """A base class for popups that handles automatic theming."""
    def __init__(self, parent, theme_manager, **kwargs):
        self.parent_app = parent
        self.theme_manager = theme_manager
        frame_bg = self.theme_manager.get_color("frame_bg")
        super().__init__(parent, fg_color=frame_bg, **kwargs)

        # Lift the window to the top after a short delay.
        # This is more robust than a direct call to self.lift(), as it gives
        # the window manager time to draw the window first.
        self.after(10, self.lift)

        try:
            ICON_PATH = os.path.join(SCRIPT_DIR, "images", "favicon.ico")
            if os.path.exists(ICON_PATH) and Image and ImageTk:
                icon = ImageTk.PhotoImage(Image.open(ICON_PATH))
                self.iconphoto(False, icon)
        except Exception as e:
            print(f"Error setting popup icon: {e}")

    def apply_theme(self):
        """Applies the current theme colors to all widgets in this popup."""
        tm = self.theme_manager
        primary_color = tm.get_color("primary")
        accent_color = tm.get_color("accent")
        frame_bg = tm.get_color("frame_bg")
        textbox_bg = tm.get_color("textbox_bg")
        textbox_fg = tm.get_color("textbox_fg")
        label_text = tm.get_color("label_text")
        border_color = tm.get_color("border_color")
        button_hover_color = tm.get_color("button_hover", fallback=accent_color)

        self.configure(fg_color=frame_bg)

        widget_configs = [
            (ctk.CTkButton, {"fg_color": primary_color, "hover_color": button_hover_color}),
            (ctk.CTkComboBox, {"button_color": primary_color, "button_hover_color": button_hover_color, "border_color": tm.get_color("secondary_border_color", border_color)}),
            (ctk.CTkFrame, {"fg_color": frame_bg, "border_color": border_color}),
            (ctk.CTkLabel, {"text_color": label_text}),
            (ctk.CTkEntry, {"fg_color": textbox_bg, "text_color": textbox_fg, "border_color": tm.get_color("secondary_border_color", border_color)}),
            (ctk.CTkTextbox, {"fg_color": textbox_bg, "text_color": textbox_fg, "border_color": tm.get_color("secondary_border_color", border_color)}),
            (ctk.CTkScrollableFrame, {"fg_color": frame_bg, "label_fg_color": primary_color}),
            (ctk.CTkCheckBox, {"fg_color": primary_color, "hover_color": button_hover_color}),
            (ctk.CTkSwitch, {
                "fg_color": tm.get_color("switch_bg_off", border_color),
                "progress_color": tm.get_color("switch_progress", accent_color),
                "button_color": tm.get_color("switch_button", primary_color),
                "button_hover_color": tm.get_color("button_hover", button_hover_color)
            }),
            (ctk.CTkProgressBar, {"progress_color": tm.get_color("progressbar_progress", primary_color)}),
            (ctk.CTkSlider, {
                "button_color": tm.get_color("slider_button", primary_color),
                "progress_color": tm.get_color("slider_progress", accent_color),
                "button_hover_color": tm.get_color("button_hover", button_hover_color)
            }),
            (ctk.CTkTabview, {
                "segmented_button_selected_color": tm.get_color("tab_selected", primary_color),
                "segmented_button_unselected_color": tm.get_color("tab_unselected", frame_bg),
                "segmented_button_selected_hover_color": tm.get_color("tab_selected_hover", button_hover_color),
                "segmented_button_unselected_hover_color": tm.get_color("tab_unselected_hover", accent_color),
                "fg_color": frame_bg
            })
        ]

        for widget_type, config in widget_configs:
            for widget in self.find_widgets_recursively(self, widget_type):
                try:
                    if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") == "transparent":
                        continue
                    widget.configure(**config)
                except Exception:
                    pass

    def find_widgets_recursively(self, widget, widget_type):
        widgets = []
        if isinstance(widget, widget_type):
            widgets.append(widget)
        for child in widget.winfo_children():
            widgets.extend(self.find_widgets_recursively(child, widget_type))
        return widgets
