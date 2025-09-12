import customtkinter as ctk
from typing import Tuple

from themed_popup import ThemedPopup

class ConfirmationDialog(ThemedPopup):
    """A modal confirmation dialog with a 'don't ask again' option."""

    def __init__(self, parent, theme_manager, title: str, message: str):
        super().__init__(parent=parent, theme_manager=theme_manager)

        self.title(title)
        self.geometry("400x180")
        self.grab_set()  # Make the dialog modal

        self.result = False
        self.dont_ask_again = ctk.BooleanVar(value=False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        message_label = ctk.CTkLabel(main_frame, text=message, wraplength=360, justify="center")
        message_label.pack(pady=(0, 20), expand=True, fill="x")

        checkbox = ctk.CTkCheckBox(main_frame, text="Don't ask me again for this action", variable=self.dont_ask_again)
        checkbox.pack(pady=10)

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(10, 0))

        self.yes_button = ctk.CTkButton(button_frame, text="Yes", command=self._on_yes, width=100)
        self.yes_button.pack(side="left", padx=10)

        self.no_button = ctk.CTkButton(button_frame, text="No", command=self._on_no, width=100)
        self.no_button.pack(side="right", padx=10)

        self.protocol("WM_DELETE_WINDOW", self._on_no)  # Treat closing the window as "No"
        self.apply_theme()

        # This is a blocking call that waits until the window is destroyed
        self.wait_window()

    def _on_yes(self):
        self.result = True
        self.grab_release()
        self.destroy()

    def _on_no(self):
        self.result = False
        self.grab_release()
        self.destroy()

    @staticmethod
    def show(parent, theme_manager, title: str, message: str) -> Tuple[bool, bool]:
        """
        Creates, shows the dialog, and returns the result.
        This is the intended factory method for using the dialog.

        Returns:
            A tuple of (bool, bool) representing (user_confirmed, dont_ask_again).
        """
        dialog = ConfirmationDialog(parent, theme_manager, title, message)
        return dialog.result, dialog.dont_ask_again.get()
