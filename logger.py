import json
import time
import os
from datetime import datetime

class TelemetryLogger:
    def __init__(self, log_dir="data"):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Keep a rotating log file based on date
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(log_dir, f"telemetry_{date_str}.jsonl")
        
    def log_event(self, event_type, details=None):
        """
        Logs a structured JSON event.
        :param event_type: A high-level category (e.g. 'AGGRO_RESET', 'DISCONNECT', 'ANTI_BAN')
        :param details: A dictionary of additional metrics or data
        """
        if details is None:
            details = {}
            
        payload = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **details
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(payload) + "\n")
            
        return payload

# Global instance for easy importing
logger = TelemetryLogger()
