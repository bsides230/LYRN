import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, List, Any

@dataclass
class OSSTool:
    """Represents a single executable action or trigger in the OSS Tool format."""
    name: str
    type: str  # e.g., 'text_parser', 'system_action'
    params: Dict[str, Any]

class OSSToolManager:
    """Manages OSS Tools that can be triggered by the Heartbeat's reasoning."""
    def __init__(self, tools_path: str = "automation/oss_tools.json"):
        self.tools_path = Path(tools_path)
        self.tools: Dict[str, OSSTool] = {}
        self.tools_path.parent.mkdir(parents=True, exist_ok=True)
        self.load_tools()

    def load_tools(self):
        """
        Loads tools from the JSON file.
        Includes backward compatibility for the old format.
        """
        if not self.tools_path.exists():
            self.tools = {}
            return

        needs_resave = False
        try:
            with open(self.tools_path, 'r', encoding='utf-8') as f:
                # Handle empty file case
                content = f.read()
                if not content:
                    tools_data = {}
                else:
                    tools_data = json.loads(content)

            migrated_tools = {}
            for name, data in tools_data.items():
                if "type" not in data: # Old format detection
                    needs_resave = True
                    params = {
                        "start_trigger": data.get("start_trigger", ""),
                        "end_trigger": data.get("end_trigger", ""),
                        "output_path": data.get("output_path", ""),
                        "output_filename": data.get("output_filename", "")
                    }
                    migrated_tools[name] = OSSTool(
                        name=data.get("name", name),
                        type="text_parser",
                        params=params
                    )
                else: # New format
                     migrated_tools[name] = OSSTool(**data)

            self.tools = migrated_tools

            if needs_resave:
                print("Old tool format detected, migrating and resaving.")
                self.save_tools()

        except (json.JSONDecodeError, IOError, TypeError) as e:
            print(f"Error loading or migrating tools: {e}")
            self.tools = {}

    def save_tools(self):
        """Saves all current tools to the JSON file in the new format."""
        try:
            # Use asdict to properly serialize the dataclass, including nested dicts
            tools_data = {name: asdict(tool) for name, tool in self.tools.items()}
            with open(self.tools_path, 'w', encoding='utf-8') as f:
                json.dump(tools_data, f, indent=2)
        except IOError as e:
            print(f"Error saving tools: {e}")

    def add_tool(self, tool: OSSTool):
        """Adds or updates a tool."""
        self.tools[tool.name] = tool
        self.save_tools()

    def delete_tool(self, tool_name: str):
        """Deletes a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.save_tools()

    def get_tool(self, tool_name: str) -> Optional[OSSTool]:
        """Retrieves a single tool by name."""
        return self.tools.get(tool_name)

    def get_all_tools(self) -> List[OSSTool]:
        """Returns a list of all tools."""
        return list(self.tools.values())
