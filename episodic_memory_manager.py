import os
import json
from datetime import datetime
import random
import string
from pathlib import Path

class EpisodicMemoryManager:
    """
    Manages the creation, reading, and writing of episodic memory entries.
    """
    def __init__(self, memory_dir="episodic_memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.chat_review_file = Path("chat_review.txt")
        self.quotes_file = Path("quotes.txt")

    def _generate_id(self) -> str:
        """Generates a unique ID for a chat entry."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{timestamp}_{random_part}"

    def create_chat_entry(self, mode: str, user_input: str, model_output: str,
                          summary_heading: str, summary: str, links: list = None,
                          think_content: str = None, thinking_cycle: str = None,
                          deltas: list = None, keywords: list = None, topics: list = None) -> Path:
        """
        Creates a new verbatim chat entry file with the specified format.
        """
        entry_id = self._generate_id()
        filepath = self.memory_dir / f"{entry_id}.txt"

        content = "/entry\n"
        content += f"/id: {entry_id}\n"
        content += f"/time: {datetime.now().isoformat()}\n"
        content += f"/mode: {mode}\n"
        if links:
            content += f"/links: {','.join(links)}\n"

        content += "\n/input\n"
        content += f"{user_input}\n"
        content += "/end_input\n"

        if think_content:
            content += "\n/think\n"
            content += f"{think_content}\n"
            content += "/end_think\n"

        content += "\n/output\n"
        content += f"{model_output}\n"
        content += "/end_output\n"

        content += "\n/summary_heading\n"
        content += f"{summary_heading}\n"
        content += "/end_summary\n"

        content += "\n/summary\n"
        content += f"{summary}\n"
        content += "/end_summary\n"

        if thinking_cycle:
            content += "\n/thinking_cycle\n"
            content += f"{thinking_cycle}\n"
            content += "/thinking_cycle_end\n"

        if deltas:
            content += "\n/deltas\n"
            content += "\n".join(deltas) + "\n"
            content += "/end_deltas\n"

        if keywords:
            content += "\n/keywords\n"
            content += "\n".join(keywords) + "\n"
            content += "/end_keywords\n"

        if topics:
            content += "\n/topics\n"
            content += "\n".join(topics) + "\n"
            content += "/end_topic\n"

        content += "\n/end_entry\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def get_all_entries(self) -> list:
        """
        Scans the memory directory and returns a list of dictionaries,
        each representing a chat entry.
        """
        entries = []
        for filepath in self.memory_dir.glob("*.txt"):
            try:
                entry_data = self.parse_entry_file(filepath)
                if entry_data:
                    entries.append(entry_data)
            except Exception as e:
                print(f"Error parsing entry file {filepath}: {e}")

        # Sort entries by time, descending
        entries.sort(key=lambda x: x.get('time', ''), reverse=True)
        return entries

    def get_recent_entries(self, num_entries: int) -> list:
        """
        Retrieves the specified number of most recent chat entries.
        """
        if num_entries <= 0:
            return []

        all_entries = self.get_all_entries() # Already sorted newest to oldest
        return all_entries[:num_entries]

    def parse_entry_file(self, filepath: Path) -> dict:
        """
        Parses a single entry file and extracts key information for the index view.
        This parser is designed to be robust to the specific (and sometimes inconsistent)
        tags defined in the user specification.
        """
        data = {"filepath": str(filepath)}
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]

        i = 0
        while i < len(lines):
            line = lines[i]
            if not line:
                i += 1
                continue

            if line.startswith('/id:'):
                data['id'] = line.split(':', 1)[1].strip()
            elif line.startswith('/time:'):
                data['time'] = line.split(':', 1)[1].strip()
            elif line.startswith('/mode:'):
                data['mode'] = line.split(':', 1)[1].strip()
            elif line.startswith('/links:'):
                data['links'] = line.split(':', 1)[1].strip()

            elif line == '/input':
                i, block_content = self._parse_block(lines, i, '/end_input')
                data['input'] = block_content
            elif line == '/think':
                i, block_content = self._parse_block(lines, i, '/end_think')
                data['think'] = block_content
            elif line == '/output':
                i, block_content = self._parse_block(lines, i, '/end_output')
                data['output'] = block_content
            elif line == '/summary_heading':
                i, block_content = self._parse_block(lines, i, '/end_summary')
                data['summary_heading'] = block_content
            elif line == '/summary':
                i, block_content = self._parse_block(lines, i, '/end_summary')
                data['summary'] = block_content
            elif line == '/thinking_cycle':
                i, block_content = self._parse_block(lines, i, '/thinking_cycle_end')
                data['thinking_cycle'] = block_content
            elif line == '/deltas':
                i, block_content = self._parse_block(lines, i, '/end_deltas')
                data['deltas'] = block_content
            elif line == '/keywords':
                i, block_content = self._parse_block(lines, i, '/end_keywords')
                data['keywords'] = block_content
            elif line == '/topics':
                i, block_content = self._parse_block(lines, i, '/end_topic')
                data['topics'] = block_content

            i += 1
        return data

    def _parse_block(self, lines: list, start_index: int, end_tag: str) -> tuple[int, str]:
        """Helper function to parse content between a start tag and an end tag."""
        content = []
        i = start_index + 1
        while i < len(lines):
            line = lines[i]
            if line == end_tag:
                return i, "\n".join(content)
            content.append(line)
            i += 1
        # Return if end tag is not found (e.g., end of file)
        return i, "\n".join(content)

    def add_to_chat_review(self, entry_filepaths: list):
        """
        Appends the full content of selected chat entries to chat_review.txt.
        """
        with open(self.chat_review_file, 'a', encoding='utf-8') as review_file:
            for filepath_str in entry_filepaths:
                filepath = Path(filepath_str)
                if filepath.exists():
                    review_file.write(f"\n--- Appending content from {filepath.name} ---\n\n")
                    review_file.write(filepath.read_text(encoding='utf-8'))
                    review_file.write("\n\n--- End of content ---\n")

    def add_to_quotes(self, quote_text: str):
        """
        Appends a specific piece of quoted text to quotes.txt.
        """
        with open(self.quotes_file, 'a', encoding='utf-8') as quotes_file:
            timestamp = datetime.now().isoformat()
            quotes_file.write(f"\n--- Quote from {timestamp} ---\n")
            quotes_file.write(quote_text)
            quotes_file.write("\n--- End of Quote ---\n\n")
