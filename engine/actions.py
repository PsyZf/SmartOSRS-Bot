import time
import random
import pyautogui
import cv2
import numpy as np
from mss import MSS

_global_sct = None

class ActionRegistry:
    """
    Registry of executable actions for declarative YAML tasks.
    """
    def __init__(self, sct=None):
        global _global_sct
        if sct is None:
            if _global_sct is None:
                _global_sct = MSS()
            sct = _global_sct
        self.sct = sct

    def sleep_random(self, duration: list | tuple | float):
        if isinstance(duration, (list, tuple)):
            min_d, max_d = duration[0], duration[1]
            dur = random.uniform(min_d, max_d)
        else:
            dur = float(duration)
        time.sleep(dur)

    def click_coord(self, target: list | tuple, variation: int = 5):
        tx, ty = target[0], target[1]
        vx = tx + random.randint(-variation, variation)
        vy = ty + random.randint(-variation, variation)
        dur = random.uniform(0.12, 0.28)
        pyautogui.moveTo(vx, vy, duration=dur, tween=pyautogui.easeOutQuad)
        pyautogui.click()

    def press_key(self, key: str, delay_after: float = 0.1):
        pyautogui.press(key)
        if delay_after > 0:
            time.sleep(delay_after)

    def log_message(self, message: str, level: str = "INFO"):
        print(f"[{level.upper()}] {message}")

    def execute(self, action_def: dict, context: dict) -> bool:
        if not action_def:
            return True
            
        action_type = action_def.get("type", "").lower()
        
        try:
            if action_type == "sleep":
                self.sleep_random(action_def.get("duration", 1.0))
            elif action_type == "click_coord":
                self.click_coord(action_def.get("target", [0, 0]), action_def.get("variation", 5))
            elif action_type == "press_key":
                self.press_key(action_def.get("key", "space"), action_def.get("delay_after", 0.1))
            elif action_type == "log":
                self.log_message(action_def.get("message", ""), action_def.get("level", "INFO"))
            elif action_type == "set_var":
                var_name = action_def.get("name")
                var_val = action_def.get("value")
                if var_name:
                    context["vars"][var_name] = var_val
            elif action_type == "sequence":
                for step in action_def.get("steps", []):
                    self.execute(step, context)
            else:
                print(f"[WARN] Unknown action type: '{action_type}'")
                return False
            return True
        except Exception as e:
            print(f"[ERROR] Failed executing action '{action_type}': {e}")
            return False
