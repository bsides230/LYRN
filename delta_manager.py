import os
import json
import time
from datetime import datetime
from pathlib import Path
import uuid
from file_lock import SimpleFileLock

class DeltaManager:
    """
    Manages the creation and storage of delta files for non-destructive updates.
    """
    def __init__(self, deltas_base_dir: str = "deltas"):
        self.base_dir = Path(deltas_base_dir)
        self.manifest_path = self.base_dir / "_manifest.json"
        self.manifest_lock = SimpleFileLock(self.base_dir / "_manifest.lock")
        self._ensure_base_dir()
        self._load_manifest()

    def _ensure_base_dir(self):
        """Ensures the base deltas directory exists."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _load_manifest(self):
        """Loads the manifest file or creates a new one."""
        with self.manifest_lock:
            if self.manifest_path.exists():
                try:
                    with open(self.manifest_path, 'r', encoding='utf-8') as f:
                        self.manifest = json.load(f)
                except json.JSONDecodeError:
                    print("Warning: Manifest file is corrupted. Creating a new one.")
                    self.manifest = {"deltas": []}
                    # Immediately save the newly created empty manifest
                    with open(self.manifest_path, 'w', encoding='utf-8') as f:
                        json.dump(self.manifest, f, indent=2)
            else:
                self.manifest = {"deltas": []}
                # Immediately save the newly created empty manifest
                with open(self.manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(self.manifest, f, indent=2)

    def _save_manifest(self):
        """Saves the manifest file with crash-safe writing."""
        with self.manifest_lock:
            temp_path = self.manifest_path.with_suffix(f".tmp.{uuid.uuid4().hex}")
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(self.manifest, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_path, self.manifest_path)
            except Exception as e:
                print(f"Error saving manifest: {e}")
                if temp_path.exists():
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

    def create_delta(self, key: str, scope: str, target: str, op: str, path: str, value: str, value_mode: str = "RAW"):
        """
        Creates, writes, and registers a new delta file.

        Args:
            key (str): The delta key from delta_key.md (e.g., 'P-001').
            scope (str): The high-level category (e.g., 'memory', 'conversation').
            target (str): The specific file or object (e.g., 'user_profile').
            op (str): The operation ('append', 'set', 'upsert', 'remove').
            path (str): The dot-notation path within the target.
            value (str): The value to apply.
            value_mode (str): How the value is encoded ('RAW' or 'EOF').
        """
        now = datetime.utcnow()
        date_path = self.base_dir / now.strftime("%Y/%m/%d")
        date_path.mkdir(parents=True, exist_ok=True)

        delta_id = f"delta_{now.strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4().hex[:8]}"
        delta_filename = f"{delta_id}.txt"
        delta_filepath = date_path / delta_filename

        delta_content = f"DELTA|{key}|{scope}|{target}|{op}|{path}|{value_mode}|{value}"

        temp_filepath = delta_filepath.with_suffix(f".tmp.{uuid.uuid4().hex}")
        try:
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                f.write(delta_content)
                f.flush()
                os.fsync(f.fileno())
            os.rename(temp_filepath, delta_filepath)

            print(f"Successfully created delta: {delta_filepath}")

            # Update and save manifest
            # Use forward slashes for cross-platform compatibility in the manifest
            relative_path = delta_filepath.relative_to(self.base_dir).as_posix()
            self.manifest["deltas"].append(relative_path)
            self._save_manifest()

            return str(delta_filepath)

        except Exception as e:
            print(f"Error creating delta file: {e}")
            if temp_filepath.exists():
                os.remove(temp_filepath)
            return None

    def update_simple_delta(self, trait_name: str, formatted_string: str):
        """
        Updates a simple key-value delta in the manifest.
        This is used for things like personality sliders where only the latest value matters.
        """
        self._load_manifest()
        if "simple_deltas" not in self.manifest:
            self.manifest["simple_deltas"] = {}

        self.manifest["simple_deltas"][trait_name] = formatted_string
        self._save_manifest()
        print(f"Updated simple delta for '{trait_name}'.")

    def get_delta_content(self) -> str:
        """
        Reads the manifest, then reads each delta file and concatenates
        their content into a single string for prompt injection.
        Also includes simple deltas.
        """
        self._load_manifest() # Ensure we have the latest manifest

        all_delta_contents = []

        # Process structured deltas from files
        for relative_path_str in self.manifest.get("deltas", []):
            delta_file_path = self.base_dir / relative_path_str
            if delta_file_path.exists():
                try:
                    content = delta_file_path.read_text(encoding='utf-8')
                    all_delta_contents.append(content)
                except Exception as e:
                    print(f"Error reading delta file {delta_file_path}: {e}")
            else:
                print(f"Warning: Delta file listed in manifest not found: {delta_file_path}")

        # Process simple deltas from the manifest itself
        simple_deltas = self.manifest.get("simple_deltas", {})
        for trait_name, formatted_string in simple_deltas.items():
            all_delta_contents.append(formatted_string)

        if not all_delta_contents:
            return ""

        # Join all individual delta file contents into one block
        full_delta_block = "\n".join(all_delta_contents)

        # Wrap the entire block in clear markers for the LLM
        return f"###DELTAS_START###\n{full_delta_block}\n###DELTAS_END###"
