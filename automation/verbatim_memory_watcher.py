import time
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

class VerbatimMemoryWatcher:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.absolute()
        self.temp_file = self.root_dir / "temp_chat_turn.txt"
        self.status_file = self.root_dir / "global_flags" / "verbatim_state.txt"
        self.history_dir = self.root_dir / "Chat_History"

        # Ensure global flags directory exists
        self.status_file.parent.mkdir(parents=True, exist_ok=True)

        self.current_session_dir = None
        self.current_block_dir = None
        self.current_file = None
        self.session_start_time = None
        self.block_number = 1
        self.message_count_in_block = 0

    def run(self):
        print("Verbatim Memory Watcher started.")
        self.start_new_session()

        while True:
            try:
                status = self.read_status()

                if status == "input_ready":
                    print("Detected input...")
                    self.handle_input()
                    self.write_status("waiting_for_response")

                elif status == "output_ready":
                    print("Detected output...")
                    self.handle_output()
                    self.write_status("idle")

                elif status == "shutdown":
                    print("Shutting down...")
                    self.end_session()
                    break

                elif status == "force_new_session":
                    print("Forcing new session...")
                    self.end_session()
                    self.start_new_session(force=True)
                    self.write_status("idle")

                time.sleep(0.1)
            except Exception as e:
                print(f"Error in Verbatim Memory Watcher: {e}")
                time.sleep(1)

    def start_new_session(self, force=False):
        self.history_dir.mkdir(parents=True, exist_ok=True)

        if not force:
            # Try to resume an existing open session
            sessions = sorted([d for d in self.history_dir.iterdir() if d.is_dir() and d.name.startswith("Session_")])
            if sessions:
                last_session = sessions[-1]
                parts = last_session.name.split('_')
                # Session_YYYYMMDD_HHMMSS is 3 parts. Closed sessions have 5 parts (start + end timestamp)
                if len(parts) == 3:
                    print(f"Resuming session: {last_session}")
                    self.current_session_dir = last_session

                    # Find the last block
                    blocks = sorted([d for d in self.current_session_dir.iterdir() if d.is_dir() and d.name.startswith("Block_")])
                    if blocks:
                        self.current_block_dir = blocks[-1]
                        self.block_number = int(self.current_block_dir.name.split('_')[1])
                        self.message_count_in_block = len(list(self.current_block_dir.glob("*.txt")))
                        print(f"Resuming block: {self.current_block_dir} (Count: {self.message_count_in_block})")
                    else:
                        self.block_number = 1
                        self.start_new_block()
                    return

        self.session_start_time = datetime.now()
        # Session Folder: filename is timestamp session start
        timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        self.current_session_dir = self.history_dir / f"Session_{timestamp}"
        self.current_session_dir.mkdir(exist_ok=True)
        print(f"Started new session: {self.current_session_dir}")

        self.block_number = 1
        self.start_new_block()

    def start_new_block(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Block Folder: filename is block number and timestamp
        block_name = f"Block_{self.block_number}_{timestamp}"
        self.current_block_dir = self.current_session_dir / block_name
        self.current_block_dir.mkdir(exist_ok=True)
        self.message_count_in_block = 0
        print(f"Started new block: {self.current_block_dir}")

    def handle_input(self):
        # Check if block is full BEFORE creating new file?
        # "The old folder auto ends at 50 chat pairs so its ready for a new input"
        # So if we are at 50, we must start a new block now.
        if self.message_count_in_block >= 50:
            self.block_number += 1
            self.start_new_block()

        content = self.read_temp_file()

        # filename is the initial write timestamp for the file creation on input
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.current_file = self.current_block_dir / f"{timestamp}.txt"

        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved input to {self.current_file}")

    def handle_output(self):
        if not self.current_file:
            print("Warning: Output received without current file.")
            return

        content = self.read_temp_file()

        # Append to current file
        with open(self.current_file, 'a', encoding='utf-8') as f:
            # Append the output block (which now includes brackets from the GUI)
            f.write("\n\n" + content)

        self.message_count_in_block += 1
        print(f"Saved output to {self.current_file}. Count: {self.message_count_in_block}")

        # Reset current file to prevent appending to the wrong file if input is skipped
        self.current_file = None

    def end_session(self):
        if self.current_session_dir and self.current_session_dir.exists():
            # "name it with the start timestamp and then append the end timestamp"
            end_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Current name is Session_START
            new_name = f"{self.current_session_dir.name}_{end_time}"
            try:
                self.current_session_dir.rename(self.current_session_dir.parent / new_name)
                print(f"Renamed session to {new_name}")
            except Exception as e:
                print(f"Error renaming session folder: {e}")

    def read_status(self):
        if self.status_file.exists():
            try:
                return self.status_file.read_text(encoding='utf-8').strip()
            except:
                return None
        return None

    def write_status(self, status):
        try:
            self.status_file.write_text(status, encoding='utf-8')
        except Exception as e:
            print(f"Error writing status: {e}")

    def read_temp_file(self):
        if self.temp_file.exists():
            try:
                return self.temp_file.read_text(encoding='utf-8')
            except:
                return ""
        return ""

if __name__ == "__main__":
    VerbatimMemoryWatcher().run()
