import sys
import os
import json
import time
from pathlib import Path

# Add the root directory to the Python path
# This is necessary so the script can import modules from the root, like CycleManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cycle_manager import CycleManager
from file_lock import SimpleFileLock

class CycleWatcher:
    """
    Watches for an active cycle and injects triggers when the LLM is idle.
    """
    def __init__(self):
        self.cycle_manager = CycleManager()
        self.root_dir = Path(__file__).parent.parent
        self.active_cycle_flag_path = self.root_dir / "global_flags" / "active_cycle.json"
        self.llm_status_flag_path = self.root_dir / "global_flags" / "llm_status.txt"
        self.cycle_trigger_path = self.root_dir / "global_flags" / "cycle_trigger.txt"

        # Ensure directories exist
        self.active_cycle_flag_path.parent.mkdir(exist_ok=True)
        self.cycle_trigger_path.parent.mkdir(exist_ok=True)

    def _read_flag_file(self, path: Path, is_json: bool = False):
        """Reads a flag file."""
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if is_json:
                    return json.loads(content) if content else None
                return content
        except (IOError, json.JSONDecodeError):
            return None

    def _write_flag_file(self, path: Path, content, is_json: bool = False):
        """Writes to a flag file."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if is_json:
                    json.dump(content, f, indent=2)
                else:
                    f.write(str(content))
        except IOError:
            pass # Fail silently

    def run(self):
        """Main loop for the watcher."""
        print("Cycle Watcher started...")
        while True:
            try:
                # 1. Check for an active cycle
                active_cycle_data = self._read_flag_file(self.active_cycle_flag_path, is_json=True)
                if not active_cycle_data or active_cycle_data.get("status") != "running":
                    time.sleep(1)
                    continue

                # 2. Check if LLM is idle
                llm_status = self._read_flag_file(self.llm_status_flag_path)
                if llm_status != "idle":
                    time.sleep(0.5)
                    continue

                # 3. If idle, process the next trigger
                cycle_name = active_cycle_data.get("name")
                current_step = active_cycle_data.get("current_step", 0)

                cycle = self.cycle_manager.get_cycle(cycle_name)
                if not cycle or not cycle.get("triggers"):
                    # Cycle is invalid or empty, stop it
                    active_cycle_data["status"] = "stopped"
                    self._write_flag_file(self.active_cycle_flag_path, active_cycle_data, is_json=True)
                    continue

                triggers = cycle["triggers"]
                if current_step >= len(triggers):
                    # End of cycle, stop it
                    print(f"Cycle '{cycle_name}' finished.")
                    active_cycle_data["status"] = "stopped"
                    self._write_flag_file(self.active_cycle_flag_path, active_cycle_data, is_json=True)
                    continue

                # 4. Get the next trigger and inject it
                next_trigger = triggers[current_step]
                print(f"Injecting trigger: '{next_trigger['name']}' from cycle '{cycle_name}' (Step {current_step + 1}/{len(triggers)})")

                # Set LLM to busy and inject trigger
                self._write_flag_file(self.llm_status_flag_path, "busy")
                self._write_flag_file(self.cycle_trigger_path, next_trigger['prompt'])

                # 5. Update the cycle state
                active_cycle_data["current_step"] = current_step + 1
                self._write_flag_file(self.active_cycle_flag_path, active_cycle_data, is_json=True)

            except Exception as e:
                print(f"Error in Cycle Watcher loop: {e}")

            time.sleep(1)


if __name__ == "__main__":
    watcher = CycleWatcher()
    watcher.run()
