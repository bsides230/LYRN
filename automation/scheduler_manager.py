import os
import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from file_lock import SimpleFileLock

@dataclass
class Schedule:
    """Represents a single scheduled job."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_name: str = ""
    scheduled_datetime_iso: str = ""

    @property
    def scheduled_datetime(self) -> datetime:
        """Returns the scheduled time as a datetime object."""
        return datetime.fromisoformat(self.scheduled_datetime_iso)

class SchedulerManager:
    """Manages the loading, saving, and manipulation of scheduled jobs."""

    def __init__(self, schedules_path: str = "automation/schedules.json"):
        self.schedules_path = Path(schedules_path)
        self.schedules_lock_path = self.schedules_path.with_suffix(f"{self.schedules_path.suffix}.lock")
        self.schedules_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.schedules_path.exists():
            self._write_schedules_unsafe([])

    def _read_schedules_unsafe(self) -> List[Dict]:
        """Unsafely reads the schedules from the JSON file. Assumes lock is held."""
        try:
            if self.schedules_path.exists() and self.schedules_path.stat().st_size > 0:
                with open(self.schedules_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read schedules file, starting fresh. Error: {e}")
        return []

    def _write_schedules_unsafe(self, schedules_data: List[Dict]):
        """Unsafely writes the schedules to the JSON file. Assumes lock is held."""
        try:
            temp_path = self.schedules_path.with_suffix(f"{self.schedules_path.suffix}.tmp")
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(schedules_data, f, indent=2)
            shutil.move(temp_path, self.schedules_path)
        except (IOError, OSError) as e:
            print(f"Error writing schedules file: {e}")

    def add_schedule(self, job_name: str, scheduled_datetime: datetime) -> Optional[Schedule]:
        """Adds a new schedule to the file."""
        new_schedule = Schedule(
            job_name=job_name,
            scheduled_datetime_iso=scheduled_datetime.replace(microsecond=0).isoformat()
        )
        schedule_dict = {
            "id": new_schedule.id,
            "job_name": new_schedule.job_name,
            "scheduled_datetime_iso": new_schedule.scheduled_datetime_iso
        }

        try:
            with SimpleFileLock(self.schedules_lock_path):
                schedules = self._read_schedules_unsafe()
                schedules.append(schedule_dict)
                self._write_schedules_unsafe(schedules)
            print(f"Added schedule for '{job_name}' at {scheduled_datetime}")
            return new_schedule
        except TimeoutError as e:
            print(f"Error adding schedule: {e}")
            return None

    def get_all_schedules(self) -> List[Schedule]:
        """Retrieves all schedules from the file."""
        schedules_data = self._read_schedules_unsafe() # Lock not strictly needed for read-only
        return [Schedule(**data) for data in schedules_data]

    def delete_schedule(self, schedule_id: str) -> bool:
        """Deletes a schedule by its unique ID."""
        deleted = False
        try:
            with SimpleFileLock(self.schedules_lock_path):
                schedules = self._read_schedules_unsafe()
                schedules_to_keep = [s for s in schedules if s.get('id') != schedule_id]

                if len(schedules_to_keep) < len(schedules):
                    self._write_schedules_unsafe(schedules_to_keep)
                    deleted = True
                    print(f"Deleted schedule with ID: {schedule_id}")
                else:
                    print(f"Warning: Could not find schedule with ID: {schedule_id} to delete.")
        except TimeoutError as e:
            print(f"Error deleting schedule: {e}")

        return deleted

    def get_and_remove_due_schedules(self) -> List[Schedule]:
        """
        Gets all schedules that are due to run and removes them from the file.
        This is an atomic operation to prevent race conditions between watchers.
        """
        due_schedules = []
        schedules_to_keep = []
        now = datetime.now()

        try:
            with SimpleFileLock(self.schedules_lock_path):
                all_schedules = self._read_schedules_unsafe()
                if not all_schedules:
                    return []

                for s_dict in all_schedules:
                    schedule = Schedule(**s_dict)
                    if schedule.scheduled_datetime <= now:
                        due_schedules.append(schedule)
                    else:
                        schedules_to_keep.append(s_dict)

                if due_schedules:
                    self._write_schedules_unsafe(schedules_to_keep)

        except TimeoutError as e:
            print(f"Error getting due schedules: {e}")
            return []

        return due_schedules
