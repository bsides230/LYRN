import os
import time
import tempfile
import hashlib
import psutil

class SimpleFileLock:
    """
    A simple, portable file locking mechanism that is resistant to stale locks.
    This lock is a context manager, ensuring that the lock is always released
    on a clean exit. It handles stale locks by storing the process ID (PID)
    of the lock owner and checking if the process is still alive.
    """
    def __init__(self, lock_file_path, timeout=5):
        lock_file_hash = hashlib.md5(str(lock_file_path).encode()).hexdigest()
        self.lock_file_path = os.path.join(tempfile.gettempdir(), f"{lock_file_hash}.lock")
        self.timeout = timeout
        self._lock_file_handle = None

    def _is_pid_running(self, pid):
        """Check if a process with the given PID is currently running."""
        return psutil.pid_exists(pid)

    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                # Attempt to create the lock file exclusively.
                self._lock_file_handle = open(self.lock_file_path, 'x')
                # Write the current PID to the lock file.
                self._lock_file_handle.write(str(os.getpid()))
                self._lock_file_handle.flush()
                return self
            except FileExistsError:
                # If the lock file already exists, it might be a stale lock.
                if time.time() - start_time > self.timeout:
                    raise TimeoutError(f"Could not acquire lock on {self.lock_file_path} within {self.timeout}s.")

                try:
                    with open(self.lock_file_path, 'r') as f:
                        pid_str = f.read().strip()
                        if not pid_str: # Handle empty lock file
                            # If the lock file is empty, it's safe to assume it's stale.
                             os.remove(self.lock_file_path)
                             continue

                        owner_pid = int(pid_str)

                    if not self._is_pid_running(owner_pid):
                        # The process that owned the lock is no longer running.
                        # Break the lock and try to acquire it again.
                        os.remove(self.lock_file_path)
                        continue
                except (IOError, ValueError):
                    # Could not read or parse the PID. The lock file might be corrupt.
                    # It's safer to wait and retry.
                    pass

                time.sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._lock_file_handle:
            self._lock_file_handle.close()
            try:
                # To avoid a race condition, only remove the lock file if this
                # process is still the owner.
                with open(self.lock_file_path, 'r') as f:
                    owner_pid = int(f.read().strip())
                if owner_pid == os.getpid():
                    os.remove(self.lock_file_path)
            except (IOError, ValueError, FileNotFoundError):
                # The lock file might have been removed by another process
                # breaking the lock, which is acceptable.
                pass
