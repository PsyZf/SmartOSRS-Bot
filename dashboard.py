import tkinter as tk
from tkinter import ttk
import json
import os

class TelemetryDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("OSRS Smart Bot Dashboard")
        self.root.geometry("800x400")
        
        # UI Setup
        self.tree = ttk.Treeview(root, columns=("Time", "Event", "Details"), show="headings")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Event", text="Event")
        self.tree.heading("Details", text="Details")
        
        self.tree.column("Time", width=150)
        self.tree.column("Event", width=150)
        self.tree.column("Details", width=450)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Start the polling loop
        self.last_size = 0
        self.log_file = None
        self.find_latest_log()
        self.update_logs()

    def find_latest_log(self):
        log_dir = "data"
        if not os.path.exists(log_dir):
            return
            
        logs = [f for f in os.listdir(log_dir) if f.startswith("telemetry_")]
        if logs:
            logs.sort()
            self.log_file = os.path.join(log_dir, logs[-1])

    def update_logs(self):
        if self.log_file and os.path.exists(self.log_file):
            current_size = os.path.getsize(self.log_file)
            if current_size > self.last_size:
                with open(self.log_file, "r") as f:
                    f.seek(self.last_size)
                    new_lines = f.readlines()
                    self.last_size = f.tell()
                    
                for line in new_lines:
                    try:
                        data = json.loads(line)
                        time_str = data.pop("timestamp").split("T")[1][:8]
                        event = data.pop("event")
                        details = str(data)
                        self.tree.insert("", "end", values=(time_str, event, details))
                        self.tree.yview_moveto(1) # Scroll to bottom
                    except json.JSONDecodeError:
                        pass
                        
        self.root.after(1000, self.update_logs)

if __name__ == "__main__":
    root = tk.Tk()
    app = TelemetryDashboard(root)
    root.mainloop()
