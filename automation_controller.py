import os
import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
from file_lock import SimpleFileLock

@dataclass
class Job:
    """Represents a single job to be executed by the Automation Controller."""
    name: str
    priority: int = 100
    when: str = "now"
    args: Dict[str, Any] = field(default_factory=dict)
    prompt: str = ""

class AutomationController:
    """
    Manages the definition, queuing, and execution of automated jobs by
    reading from and writing to a shared job_queue.json file.
    """
    def __init__(self, job_definitions_path: str = "automation/jobs", queue_path: str = "automation/job_queue.json"):
        self.job_definitions_path = Path(job_definitions_path)
        self.queue_path = Path(queue_path)
        self.queue_lock_path = self.queue_path.with_suffix(f"{self.queue_path.suffix}.lock")
        self.job_definitions = {}
        self._load_job_definitions()
        # Ensure the queue file exists
        if not self.queue_path.exists():
            self._write_queue_unsafe([])

    def _load_job_definitions(self):
        """
        Loads job definitions from the jobs.json file.
        """
        jobs_json_path = self.job_definitions_path / "jobs.json"
        if not jobs_json_path.exists():
            print("No jobs.json found. Creating default examples.")
            self._create_default_jobs()
            return

        try:
            with open(jobs_json_path, 'r', encoding='utf-8') as f:
                self.job_definitions = json.load(f)
            print(f"Loaded {len(self.job_definitions)} job definitions from jobs.json: {list(self.job_definitions.keys())}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading job definitions from {jobs_json_path}: {e}")
            self.job_definitions = {}

    def _create_default_jobs(self):
        """Creates a default jobs.json file if none is found."""
        default_jobs = {
            "summary_job": {
                "instructions": "Create a concise, factual summary of the provided text. Focus on key decisions, outcomes, and open items.",
                "trigger": "Summarize the previous text."
            },
            "keyword_job": {
                "instructions": "Extract the main keywords from the provided text as a JSON-formatted list. Example: [\"keyword1\", \"keyword2\"]",
                "trigger": "Extract keywords from the previous text."
            },
            "reflection_job": {
                "instructions": "Reflect on the conversation so far. Identify key insights, contradictions, or areas for future exploration. Propose next steps if applicable.",
                "trigger": "Reflect on the conversation."
            }
        }
        self.job_definitions = default_jobs
        jobs_json_path = self.job_definitions_path / "jobs.json"
        try:
            with open(jobs_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.job_definitions, f, indent=2)
            print(f"Created default jobs file at {jobs_json_path}")
        except IOError as e:
            print(f"Could not create default jobs file: {e}")

    def _read_queue_unsafe(self) -> List[Dict]:
        """Unsafely reads the job queue from the JSON file. Assumes lock is held."""
        try:
            if self.queue_path.exists() and self.queue_path.stat().st_size > 0:
                with open(self.queue_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read job queue file, starting fresh. Error: {e}")
        return []

    def _write_queue_unsafe(self, queue_data: List[Dict]):
        """Unsafely writes the job queue to the JSON file using an atomic operation. Assumes lock is held."""
        try:
            temp_path = self.queue_path.with_suffix(f"{self.queue_path.suffix}.tmp")
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, indent=2)
            shutil.move(temp_path, self.queue_path)
        except (IOError, OSError) as e:
            print(f"Error writing job queue file: {e}")

    def save_job_definition(self, job_name: str, instructions: str, trigger: str):
        """Saves a job's instructions and trigger to the jobs.json file."""
        job_data = {
            "instructions": instructions,
            "trigger": trigger
        }

        jobs_json_path = self.job_definitions_path / "jobs.json"
        jobs_lock_path = jobs_json_path.with_suffix('.json.lock')

        try:
            with SimpleFileLock(jobs_lock_path):
                # Read existing jobs
                if jobs_json_path.exists():
                    with open(jobs_json_path, 'r', encoding='utf-8') as f:
                        all_jobs = json.load(f)
                else:
                    all_jobs = {}

                # Update or add the new job
                all_jobs[job_name] = job_data

                # Write back to the file
                with open(jobs_json_path, 'w', encoding='utf-8') as f:
                    json.dump(all_jobs, f, indent=2)

            # Update the in-memory dictionary as well
            self.job_definitions[job_name] = job_data
            print(f"Job definition for '{job_name}' saved successfully.")

        except (IOError, TimeoutError, json.JSONDecodeError) as e:
            print(f"Error saving job definition for '{job_name}': {e}")

    def delete_job_definition(self, job_name: str):
        """Deletes a job's definition from the jobs.json file."""
        jobs_json_path = self.job_definitions_path / "jobs.json"
        jobs_lock_path = jobs_json_path.with_suffix('.json.lock')

        try:
            with SimpleFileLock(jobs_lock_path):
                if jobs_json_path.exists():
                    with open(jobs_json_path, 'r', encoding='utf-8') as f:
                        all_jobs = json.load(f)
                else:
                    all_jobs = {}

                if job_name in all_jobs:
                    del all_jobs[job_name]

                with open(jobs_json_path, 'w', encoding='utf-8') as f:
                    json.dump(all_jobs, f, indent=2)

            if job_name in self.job_definitions:
                del self.job_definitions[job_name]
            print(f"Job definition for '{job_name}' deleted successfully.")

        except (IOError, TimeoutError, json.JSONDecodeError) as e:
            print(f"Error deleting job definition for '{job_name}': {e}")

    def add_job(self, name: str, priority: int = 100, when: str = "now", args: Optional[Dict[str, Any]] = None):
        """Adds a new job to the file-based execution queue in a thread-safe manner."""
        if name not in self.job_definitions:
            print(f"Warning: Job '{name}' not defined. Cannot add to queue.")
            return

        new_job_dict = { "name": name, "priority": priority, "when": when, "args": args or {} }

        try:
            with SimpleFileLock(self.queue_lock_path):
                queue_data = self._read_queue_unsafe()
                queue_data.append(new_job_dict)
                self._write_queue_unsafe(queue_data)
            print(f"Job '{name}' added to the queue file. Queue size: {len(queue_data)}")
        except TimeoutError as e:
            print(f"Error adding job: {e}")

    def get_next_job(self) -> Optional[Job]:
        """Retrieves and consumes the next job from the queue file in a thread-safe manner."""
        try:
            with SimpleFileLock(self.queue_lock_path):
                queue_data = self._read_queue_unsafe()
                if not queue_data:
                    return None

                next_job_dict = queue_data.pop(0)
                self._write_queue_unsafe(queue_data)
        except TimeoutError as e:
            print(f"Error getting next job: {e}")
            return None

        instruction_prompt = self.get_job_instructions_prompt(next_job_dict["name"], next_job_dict.get("args", {}))
        if not instruction_prompt:
            print(f"Warning: Could not get instruction prompt for job '{next_job_dict['name']}'. Skipping.")
            return None

        return Job(
            name=next_job_dict["name"],
            priority=next_job_dict.get("priority", 100),
            when=next_job_dict.get("when", "now"),
            args=next_job_dict.get("args", {}),
            prompt=instruction_prompt
        )

    def has_pending_jobs(self) -> bool:
        """
        Checks if there are any jobs in the queue file.
        This is a non-locking read, a small chance of a race condition is acceptable
        for this status check.
        """
        queue_data = self._read_queue_unsafe()
        return len(queue_data) > 0

    def get_job_trigger(self, job_name: str) -> Optional[str]:
        """
        Gets the trigger prompt for a given job.
        """
        if job_name not in self.job_definitions:
            print(f"Error: Cannot get trigger for undefined job '{job_name}'.")
            return None
        return self.job_definitions[job_name].get("trigger")

    def get_job_instructions_prompt(self, job_name: str, args: Dict[str, Any]) -> Optional[str]:
        """
        Constructs the full instruction prompt for a given job, including the standardized header.
        """
        if job_name not in self.job_definitions:
            print(f"Error: Cannot get instructions for undefined job '{job_name}'.")
            return None

        job_instructions = self.job_definitions[job_name].get("instructions", "")

        for key, value in args.items():
            placeholder = f"{{{key}}}"
            job_instructions = job_instructions.replace(placeholder, str(value))

        prompt = f"###JOB_START: {job_name.upper()}###\n"
        prompt += f"{job_instructions}\n"
        prompt += f"###_END###"

        return prompt
