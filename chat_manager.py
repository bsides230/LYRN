import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class ChatManager:
    """
    Manages the chat history files in the `chat/` directory.
    This includes enforcing a maximum number of files and preparing
    a structured list of messages for prompt injection.
    """
    def __init__(self, chat_dir: str, settings_manager, role_mappings: dict):
        self.chat_dir = Path(chat_dir)
        self.settings_manager = settings_manager
        self.role_mappings = role_mappings
        self.chat_dir.mkdir(parents=True, exist_ok=True)

    def manage_chat_history_files(self):
        """
        Ensures the number of chat files in the chat directory does not
        exceed the user-defined limit. Deletes the oldest files if necessary.
        """
        history_limit = self.settings_manager.get_setting("chat_history_length", 10)
        if history_limit <= 0:
            for f in self.chat_dir.glob("*.txt"):
                try:
                    f.unlink()
                except OSError as e:
                    print(f"Error deleting chat file {f}: {e}")
            return

        try:
            files = sorted(self.chat_dir.glob("*.txt"), key=os.path.getmtime)
            if len(files) > history_limit:
                num_to_delete = len(files) - history_limit
                for i in range(num_to_delete):
                    files[i].unlink()
        except Exception as e:
            print(f"Error managing chat history files: {e}")

    def get_chat_history_messages(self) -> List[Dict[str, str]]:
        """
        Reads chat journal files, parses them, and returns a structured list
        of messages suitable for the LLM, ensuring roles alternate correctly.
        """
        if not self.settings_manager.get_setting("enable_chat_history", True):
            return []

        self.manage_chat_history_files()
        messages = []

        try:
            files = sorted(self.chat_dir.glob("*.txt"), key=os.path.getmtime)
            if not files:
                return []

            for file_path in files:
                content = file_path.read_text(encoding='utf-8').strip()

                # Use regex to find all role blocks
                role_blocks = re.findall(r"#(\w+)_START#\n(.*?)\n#\w+_END#", content, re.DOTALL)

                for role, text in role_blocks:
                    role_lower = role.lower()

                    # For the purpose of history, any role that isn't 'user' is treated as 'assistant'
                    if role_lower == "user":
                        messages.append({"role": "user", "content": text.strip()})
                    else:
                        # Treat all other roles (assistant, model, thinking, etc.) as the assistant's turn
                        messages.append({"role": "assistant", "content": text.strip()})

            # Ensure the conversation ends with a user message if possible,
            # but llama-cpp can handle assistant as the last message.
            # Most importantly, ensure roles alternate correctly.
            return self._ensure_alternating_roles(messages)

        except Exception as e:
            print(f"Error getting structured chat history: {e}")
            return []

    def _ensure_alternating_roles(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Validates and corrects the message list to ensure roles alternate
        between 'user' and 'assistant'. It prioritizes keeping the latest messages.
        """
        if not messages:
            return []

        # Start with the first message's role and build a new valid list
        valid_messages = [messages[0]]
        last_role = messages[0]['role']

        for i in range(1, len(messages)):
            current_message = messages[i]
            current_role = current_message['role']

            if current_role != last_role:
                valid_messages.append(current_message)
                last_role = current_role
            else:
                # If we have two consecutive roles, merge the content into the previous one.
                # This handles cases where a log might have two user inputs back-to-back.
                print(f"Warning: Found consecutive role '{current_role}'. Merging content.")
                valid_messages[-1]['content'] += "\n\n" + current_message['content']

        return valid_messages
