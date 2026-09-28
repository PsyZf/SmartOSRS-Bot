import os
import yaml

class TaskLoader:
    """
    Parses and validates declarative YAML task files.
    """
    @staticmethod
    def load_task(file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Task file not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        if not isinstance(data, dict):
            raise ValueError("YAML root must be a dictionary object.")
            
        # Validate minimal schema
        if "name" not in data:
            data["name"] = os.path.splitext(os.path.basename(file_path))[0]
            
        if "states" not in data or not isinstance(data["states"], list) or len(data["states"]) == 0:
            raise ValueError("Task must contain a non-empty 'states' list.")
            
        for idx, state in enumerate(data["states"]):
            if "id" not in state:
                state["id"] = f"state_{idx}"
                
        return data

    @staticmethod
    def list_available_tasks(tasks_dir: str = "tasks") -> list[str]:
        if not os.path.exists(tasks_dir):
            return []
        return [
            os.path.join(tasks_dir, f)
            for f in os.listdir(tasks_dir)
            if f.endswith((".yaml", ".yml"))
        ]
