import unittest
import os
from engine.task_loader import TaskLoader
from engine.state_machine import StateMachineRunner
from engine.actions import ActionRegistry
from engine.conditions import ConditionEvaluator

class TestDeclarativeEngine(unittest.TestCase):
    def setUp(self):
        self.task_file = "tasks/example_sand_crabs.yaml"

    def test_task_loading(self):
        task_data = TaskLoader.load_task(self.task_file)
        self.assertIn("name", task_data)
        self.assertIn("states", task_data)
        self.assertGreater(len(task_data["states"]), 0)
        print(f"[TEST] Successfully loaded task: {task_data['name']}")

    def test_state_machine_transitions(self):
        task_data = TaskLoader.load_task(self.task_file)
        runner = StateMachineRunner(task_data)
        runner.is_running = True

        # Initial state should be 'check_aggro_timer'
        self.assertEqual(runner.current_state_id, "check_aggro_timer")
        
        # Step 1: Timer hasn't elapsed, should transition to 'check_combat'
        runner.step()
        self.assertEqual(runner.current_state_id, "check_combat")
        
        # Step 2: Next state is 'idle_delay' (override sleep for quick test)
        runner.actions.sleep_random = lambda dur: None
        runner.step()
        self.assertEqual(runner.current_state_id, "idle_delay")
        
        # Step 3: Returns to 'check_aggro_timer'
        runner.step()
        self.assertEqual(runner.current_state_id, "check_aggro_timer")
        print("[TEST] State machine transitions verified successfully!")

if __name__ == "__main__":
    unittest.main()
