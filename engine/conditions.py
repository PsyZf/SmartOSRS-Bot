import time
import cv2
import numpy as np
from mss import MSS

class ConditionEvaluator:
    """
    Evaluates conditional statements in declarative YAML tasks.
    """
    def __init__(self, sct=None):
        self.sct = sct or MSS()

    def capture_region(self, region: dict | list) -> np.ndarray:
        if isinstance(region, list):
            mon = {"left": region[0], "top": region[1], "width": region[2], "height": region[3]}
        else:
            mon = region
        img = np.array(self.sct.grab(mon))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def evaluate(self, condition_def: dict, context: dict) -> bool:
        if not condition_def:
            return True
            
        cond_type = condition_def.get("type", "").lower()
        
        try:
            if cond_type == "timer_elapsed":
                timer_name = condition_def.get("timer", "default")
                threshold = float(condition_def.get("seconds", 10.0))
                if timer_name not in context["timers"]:
                    context["timers"][timer_name] = time.time()
                    return False
                last_time = context["timers"][timer_name]
                elapsed = time.time() - last_time
                if elapsed >= threshold:
                    context["timers"][timer_name] = time.time()
                    return True
                return False

            elif cond_type == "var_equals":
                var_name = condition_def.get("name")
                expected = condition_def.get("value")
                return context["vars"].get(var_name) == expected

            elif cond_type == "color_present":
                region = condition_def.get("region", [0, 0, 100, 100])
                hsv_min = tuple(condition_def.get("hsv_min", [0, 0, 0]))
                hsv_max = tuple(condition_def.get("hsv_max", [180, 255, 255]))
                min_pixels = int(condition_def.get("min_pixels", 10))
                
                img = self.capture_region(region)
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, hsv_min, hsv_max)
                count = cv2.countNonZero(mask)
                return count >= min_pixels

            elif cond_type == "color_absent":
                region = condition_def.get("region", [0, 0, 100, 100])
                hsv_min = tuple(condition_def.get("hsv_min", [0, 0, 0]))
                hsv_max = tuple(condition_def.get("hsv_max", [180, 255, 255]))
                max_pixels = int(condition_def.get("max_pixels", 5))
                
                img = self.capture_region(region)
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, hsv_min, hsv_max)
                count = cv2.countNonZero(mask)
                return count <= max_pixels

            else:
                print(f"[WARN] Unknown condition type: '{cond_type}'")
                return True
        except Exception as e:
            print(f"[ERROR] Failed evaluating condition '{cond_type}': {e}")
            return False
