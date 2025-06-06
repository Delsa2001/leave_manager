import json
from datetime import datetime


class DataHandler:
    def __init__(self, filepath):
        self.filepath = filepath
        self._read_data()

    def _read_data(self):
        """Read JSON data from file and ensure required keys exist."""
        with open(self.filepath, "r") as file:
            self.data = json.load(file)

        # Ensure required keys exist
        self.data.setdefault("holidays", [])
        self._write_data()

    def _write_data(self):
        """Write JSON data back to file."""
        with open(self.filepath, "w") as file:
            json.dump(self.data, file, indent=4)

    def save(self):
        """Public method to save current state of data."""
        self._write_data()

    def record_log(self, note):
        """Append a log entry to system.log with a timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {note}\n"
        with open("system.log", "a") as logfile:
            logfile.write(log_entry)

    def log_action(self, note):
        """Alias for record_log, for consistency with other modules."""
        self.record_log(note)
