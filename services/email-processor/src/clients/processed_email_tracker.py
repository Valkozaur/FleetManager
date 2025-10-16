import os
from threading import Lock

class ProcessedEmailTracker:
    """
    Tracks processed email IDs using a persistent file in data_dir.
    Thread-safe for single-process use.
    """
    def __init__(self, data_dir: str = './data', filename: str = 'processed_emails.txt'):
        self.data_dir = data_dir
        self.filepath = os.path.join(data_dir, filename)
        self._lock = Lock()
        os.makedirs(self.data_dir, exist_ok=True)
        self._ids = set()
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                for line in f:
                    self._ids.add(line.strip())

    def is_processed(self, email_id: str) -> bool:
        with self._lock:
            return email_id in self._ids

    def mark_processed(self, email_id: str):
        with self._lock:
            if email_id not in self._ids:
                with open(self.filepath, 'a') as f:
                    f.write(email_id + '\n')
                self._ids.add(email_id)
