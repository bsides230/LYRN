import customtkinter as ctk
import json
import os

class CustomColorPickerPopup(ctk.CTkToplevel):
    def __init__(self, parent, initial_color="#ffffff"):
        super().__init__(parent)
        self.parent = parent
        self.initial_color = initial_color
        self.selected_color = None

        self.title("Custom Color Picker")
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.load_colors()

    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Color grid
        self.color_grid_frame = ctk.CTkScrollableFrame(main_frame, label_text="Color Palette")
        self.color_grid_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # Custom color input
        custom_color_frame = ctk.CTkFrame(main_frame)
        custom_color_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(custom_color_frame, text="Custom Color (Hex):").pack(side="left", padx=5)
        self.hex_entry = ctk.CTkEntry(custom_color_frame)
        self.hex_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.hex_entry.insert(0, self.initial_color)

        save_custom_button = ctk.CTkButton(custom_color_frame, text="Save Custom", command=self.save_custom_color)
        save_custom_button.pack(side="left", padx=5)

        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        ok_button = ctk.CTkButton(button_frame, text="OK", command=self.on_ok)
        ok_button.pack(side="left", padx=5)

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side="right", padx=5)

    def load_colors(self):
        # Load colors from color_grid.json
        try:
            with open("color_grid.json", 'r') as f:
                color_data = json.load(f)

            for section in color_data.get("sections", []):
                section_label = ctk.CTkLabel(self.color_grid_frame, text=section.get("label", ""), font=("Arial", 12, "bold"))
                section_label.pack(fill="x", pady=(10, 5))

                swatch_frame = ctk.CTkFrame(self.color_grid_frame)
                swatch_frame.pack(fill="x")

                for i, swatch in enumerate(section.get("swatches", [])):
                    hex_color = swatch.get("hex")
                    if hex_color:
                        color_button = ctk.CTkButton(swatch_frame, text="", fg_color=hex_color, width=30, height=30, command=lambda c=hex_color: self.select_color(c))
                        color_button.grid(row=0, column=i, padx=2, pady=2)

        except Exception as e:
            print(f"Error loading color_grid.json: {e}")

        # Load custom colors
        self.load_custom_colors()

    def load_custom_colors(self):
        # Create a frame for custom colors if it doesn't exist
        if not hasattr(self, 'custom_color_frame'):
            self.custom_color_frame = ctk.CTkFrame(self.color_grid_frame)
            self.custom_color_frame.pack(fill="x", pady=(10, 5))
            ctk.CTkLabel(self.custom_color_frame, text="Custom Colors", font=("Arial", 12, "bold")).pack(fill="x")

        # Clear existing custom colors
        for widget in self.custom_color_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.destroy()

        # Load from custom_colors.json
        if os.path.exists("custom_colors.json"):
            try:
                with open("custom_colors.json", 'r') as f:
                    custom_colors = json.load(f)

                for i, color in enumerate(custom_colors):
                    color_button = ctk.CTkButton(self.custom_color_frame, text="", fg_color=color, width=30, height=30, command=lambda c=color: self.select_color(c))
                    color_button.grid(row=0, column=i, padx=2, pady=2)
            except Exception as e:
                print(f"Error loading custom_colors.json: {e}")

    def save_custom_color(self):
        color = self.hex_entry.get()
        if not color.startswith("#") or len(color) != 7:
            # Basic validation
            return

        custom_colors = []
        if os.path.exists("custom_colors.json"):
            with open("custom_colors.json", 'r') as f:
                custom_colors = json.load(f)

        if color not in custom_colors:
            custom_colors.append(color)
            with open("custom_colors.json", 'w') as f:
                json.dump(custom_colors, f)

            self.load_custom_colors()

    def select_color(self, color):
        self.hex_entry.delete(0, "end")
        self.hex_entry.insert(0, color)

    def on_ok(self):
        self.selected_color = self.hex_entry.get()
        self.destroy()

    def on_cancel(self):
        self.destroy()

    def get_color(self):
        self.wait_window()
        return self.selected_color
