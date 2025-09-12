import sys
import time
from pathlib import Path
import os

# Add the parent directory to the Python path to allow for package-like imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from automation.scheduler_manager import SchedulerManager
    from automation_controller import AutomationController
    from file_lock import SimpleFileLock
except ImportError as e:
    print(f"Error: Could not import necessary modules. Make sure the script is run from the project's root directory or the parent directory is in the Python path.")
    print(f"Details: {e}")
    sys.exit(1)

def main():
    """
    The main loop for the scheduler watcher.
    Continuously checks for due schedules and adds them to the job queue.
    Ensures that only one instance of the watcher is running at a time.
    """
    watcher_lock_path = Path(SCRIPT_DIR) / "scheduler_watcher.lock"

    try:
        # Use a timeout of 0 to exit immediately if another instance is running
        with SimpleFileLock(watcher_lock_path, timeout=0):
            print("Scheduler watcher started...")
            scheduler_manager = SchedulerManager()
            automation_controller = AutomationController()

            while True:
                try:
                    due_schedules = scheduler_manager.get_and_remove_due_schedules()

                    if due_schedules:
                        print(f"Found {len(due_schedules)} due schedule(s).")
                        for schedule in due_schedules:
                            print(f"Queueing job: '{schedule.job_name}' scheduled for {schedule.scheduled_datetime_iso}")
                            automation_controller.add_job(name=schedule.job_name)

                    # Sleep for a short interval to be responsive but not waste CPU
                    time.sleep(0.5)  # 500 milliseconds

                except Exception as e:
                    print(f"An error occurred in the scheduler watcher loop: {e}")
                    # Wait a bit longer after an error to avoid rapid-fire error messages
                    time.sleep(5)

    except TimeoutError:
        print("Scheduler watcher is already running. Exiting.")
        sys.exit(0)  # Graceful exit if another instance is running.
    except Exception as e:
        print(f"An unexpected error occurred during watcher initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
