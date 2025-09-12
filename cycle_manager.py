import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from file_lock import SimpleFileLock

class CycleManager:
    """Manages the creation, modification, and storage of automation cycles."""

    def __init__(self, cycles_path: str = "automation/cycles.json"):
        self.cycles_path = Path(cycles_path)
        self.lock_path = self.cycles_path.with_suffix('.json.lock')
        self.cycles = self._load_cycles()

    def _load_cycles(self) -> Dict[str, Dict[str, Any]]:
        """Loads the cycles from the JSON file in a process-safe way."""
        if not self.cycles_path.exists():
            return {}
        try:
            with SimpleFileLock(self.lock_path):
                with open(self.cycles_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
        except (json.JSONDecodeError, IOError, TimeoutError) as e:
            print(f"Error loading cycles file: {e}. Starting with an empty set.")
            return {}
        return {}

    def _save_cycles(self):
        """Saves the current cycles to the JSON file in a process-safe way."""
        try:
            with SimpleFileLock(self.lock_path):
                with open(self.cycles_path, 'w', encoding='utf-8') as f:
                    json.dump(self.cycles, f, indent=2)
        except (IOError, TimeoutError) as e:
            print(f"Error saving cycles file: {e}")

    def get_cycle_names(self) -> List[str]:
        """Returns a sorted list of all cycle names."""
        return sorted(list(self.cycles.keys()))

    def get_cycle(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns the data for a specific cycle."""
        return self.cycles.get(name)

    def create_cycle(self, name: str, cycle_type: str = "prompt", description: str = "") -> bool:
        """Creates a new, empty cycle. Returns False if it already exists."""
        if name in self.cycles:
            return False
        self.cycles[name] = {
            "name": name,
            "type": cycle_type,
            "description": description,
            "triggers": []
        }
        self._save_cycles()
        return True

    def delete_cycle(self, name: str):
        """Deletes a cycle."""
        if name in self.cycles:
            del self.cycles[name]
            self._save_cycles()

    def update_cycle_triggers(self, cycle_name: str, triggers: List[Dict[str, str]]):
        """Updates the entire list of triggers for a cycle."""
        if cycle_name in self.cycles:
            self.cycles[cycle_name]["triggers"] = triggers
            self._save_cycles()

    def add_trigger_to_cycle(self, cycle_name: str, trigger_name: str, trigger_prompt: str):
        """Adds a new trigger to a cycle."""
        if cycle_name in self.cycles:
            # Check if a trigger with the same name already exists
            for trigger in self.cycles[cycle_name]["triggers"]:
                if trigger.get("name") == trigger_name:
                    # Overwrite existing trigger
                    trigger["prompt"] = trigger_prompt
                    self._save_cycles()
                    return

            # If not found, append a new one
            new_trigger = {"name": trigger_name, "prompt": trigger_prompt}
            self.cycles[cycle_name]["triggers"].append(new_trigger)
            self._save_cycles()

    def delete_trigger_from_cycle(self, cycle_name: str, trigger_name: str):
        """Deletes a trigger from a cycle by name."""
        if cycle_name in self.cycles:
            initial_len = len(self.cycles[cycle_name]["triggers"])
            self.cycles[cycle_name]["triggers"] = [
                t for t in self.cycles[cycle_name]["triggers"] if t.get("name") != trigger_name
            ]
            if len(self.cycles[cycle_name]["triggers"]) < initial_len:
                self._save_cycles()
