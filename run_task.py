import argparse
import sys
import os
import signal
from engine.task_loader import TaskLoader
from engine.state_machine import StateMachineRunner

def main():
    parser = argparse.ArgumentParser(description="Declarative Task Runner")
    parser.add_argument("task_file", type=str, help="Path to the .yaml task definition file")
    parser.add_argument("--interval", type=float, default=0.5, help="State machine polling interval in seconds")
    parser.add_argument("--max-iterations", type=int, default=None, help="Maximum state execution steps")
    args = parser.parse_args()

    if not os.path.exists(args.task_file):
        print(f"[ERROR] Task file does not exist: {args.task_file}")
        sys.exit(1)

    print(f"[*] Loading declarative task: {args.task_file}")
    try:
        task_data = TaskLoader.load_task(args.task_file)
    except Exception as e:
        print(f"[ERROR] Failed to parse task YAML: {e}")
        sys.exit(1)

    print(f"[+] Task loaded: '{task_data.get('name')}' (Version: {task_data.get('version', '1.0')})")
    print(f"[*] Total states defined: {len(task_data.get('states', []))}")
    print("[*] Starting state machine execution loop. Press Ctrl+C to stop.\n")

    runner = StateMachineRunner(task_data)

    def handle_sigint(sig, frame):
        print("\n[!] Shutdown signal received. Stopping state machine...")
        runner.is_running = False

    signal.signal(signal.SIGINT, handle_sigint)

    runner.run_loop(max_iterations=args.max_iterations, poll_interval=args.interval)
    print("[*] Execution complete.")

if __name__ == "__main__":
    main()
