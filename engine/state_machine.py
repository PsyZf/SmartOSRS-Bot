import time
from .actions import ActionRegistry
from .conditions import ConditionEvaluator

class StateMachineRunner:
    """
    Generic execution runner for declarative YAML state machines.
    """
    def __init__(self, task_data: dict, action_registry: ActionRegistry = None, condition_evaluator: ConditionEvaluator = None):
        self.task_data = task_data
        self.actions = action_registry or ActionRegistry()
        self.conditions = condition_evaluator or ConditionEvaluator()
        
        self.states = {s["id"]: s for s in task_data["states"]}
        self.initial_state_id = task_data["states"][0]["id"]
        self.current_state_id = self.initial_state_id
        
        self.context = {
            "vars": {},
            "timers": {"start_time": time.time(), "default": time.time()},
            "loop_count": 0
        }
        
        self.is_running = False
        self.is_paused = False

    def step(self) -> bool:
        """
        Executes one step of the current state.
        Returns False if task is finished or state does not exist.
        """
        if not self.is_running or self.is_paused:
            return True
            
        state = self.states.get(self.current_state_id)
        if not state:
            print(f"[ENGINE] Reached terminal state or invalid state id: '{self.current_state_id}'")
            self.is_running = False
            return False

        self.context["loop_count"] += 1

        # 1. Evaluate Condition (if present)
        condition_met = True
        if "condition" in state:
            condition_met = self.conditions.evaluate(state["condition"], self.context)

        # 2. Execute Action based on condition branch or standard action
        action_def = None
        next_state_id = state.get("next_state")

        if "condition" in state:
            if condition_met:
                action_def = state.get("action_on_true") or state.get("action")
                next_state_id = state.get("on_true") or next_state_id
            else:
                action_def = state.get("action_on_false")
                next_state_id = state.get("on_false") or next_state_id
        else:
            action_def = state.get("action")

        if action_def:
            self.actions.execute(action_def, self.context)

        # 3. Transition to next state
        if next_state_id:
            self.current_state_id = next_state_id
            
        return True

    def run_loop(self, max_iterations: int = None, poll_interval: float = 0.5):
        self.is_running = True
        iterations = 0
        
        while self.is_running:
            if not self.step():
                break
            iterations += 1
            if max_iterations and iterations >= max_iterations:
                print(f"[ENGINE] Reached max iterations ({max_iterations}). Stopping.")
                break
            time.sleep(poll_interval)
            
        self.is_running = False
