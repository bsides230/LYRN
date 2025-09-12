import subprocess
import pyautogui
import pygetwindow as gw
import time
from typing import Dict, Any

def focus_window(title: str) -> bool:
    """
    Brings a window with a matching title to the foreground.
    Returns True if a window was found and activated, False otherwise.
    """
    if not title:
        print("SystemInteraction: No target window title provided for focus.")
        return False

    matches = gw.getWindowsWithTitle(title)
    if matches:
        try:
            window = matches[0]
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
        except gw.PyGetWindowException as e:
            print(f"SystemInteraction: Error focusing window '{title}': {e}")
            return False
    else:
        print(f"SystemInteraction: No window with title '{title}' found.")
        return False

def run_system_affordance(aff: Dict[str, Any]):
    """
    Executes a system-level action based on an affordance dictionary.
    """
    action = aff.get("action")
    target = aff.get("target")
    params = aff.get("params", {})

    print(f"SystemInteraction: Running action '{action}' on target '{target}' with params {params}")

    if action == "open_app":
        if not target:
            print("SystemInteraction: 'open_app' action requires a 'target' application path.")
            return
        try:
            subprocess.Popen([target])
        except FileNotFoundError:
            print(f"SystemInteraction: Application not found at '{target}'")
        except Exception as e:
            print(f"SystemInteraction: Error opening application '{target}': {e}")

    elif action == "send_keys":
        if not target:
            print("SystemInteraction: 'send_keys' action requires a 'target' window title.")
            return
        if "keys" not in params:
            print("SystemInteraction: 'send_keys' action requires 'keys' in params.")
            return

        if focus_window(target):
            time.sleep(0.1) # Small delay to ensure focus is set
            pyautogui.write(params["keys"], interval=params.get("delay", 0.0))

    elif action == "click":
        # Clicks at given coordinates or current position if not provided
        x = params.get("x")
        y = params.get("y")
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y)
        else:
            pyautogui.click()

    elif action == "move_mouse":
        if "x" not in params or "y" not in params:
            print("SystemInteraction: 'move_mouse' action requires 'x' and 'y' in params.")
            return
        pyautogui.moveTo(params["x"], params["y"], duration=params.get("duration", 0.25))

    elif action == "window_focus":
        if not target:
            print("SystemInteraction: 'window_focus' action requires a 'target' window title.")
            return
        focus_window(target)

    elif action == "window_resize":
        if not target:
            print("SystemInteraction: 'window_resize' action requires a 'target' window title.")
            return

        matches = gw.getWindowsWithTitle(target)
        if not matches:
            print(f"SystemInteraction: No window with title '{target}' found for resizing.")
            return

        window = matches[0]
        try:
            if "width" in params and "height" in params:
                window.resizeTo(params["width"], params["height"])
            if "x" in params and "y" in params:
                window.moveTo(params["x"], params["y"])
        except gw.PyGetWindowException as e:
            print(f"SystemInteraction: Error resizing/moving window '{target}': {e}")

    else:
        print(f"SystemInteraction: Unknown action '{action}'")
