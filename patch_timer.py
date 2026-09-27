import sys

def patch():
    filepath = 'C:/Users/psy/Documents/antigravity/amazing-einstein/osrs-smart-bot/gui_app.py'
    with open(filepath, 'r') as f:
        content = f.read()

    # Add import time
    if 'import time' not in content:
        content = content.replace('import sys', 'import sys\nimport time')

    # Add timer variables to __init__
    content = content.replace('self.bot_process = None', 'self.bot_process = None\n        self.bot_start_time = None\n        self.timer_running = False')

    # Initialize timer in start_bot
    content = content.replace('self.log(f"[*] Initializing {script_file}...")', 'self.log(f"[*] Initializing {script_file}...")\n        self.bot_start_time = time.time()\n        self.timer_running = True\n        self.update_timer()')

    # Create update_timer function right after start_bot
    update_timer_code = '''
    def update_timer(self):
        if self.timer_running and self.bot_start_time:
            elapsed = int(time.time() - self.bot_start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.timer_label.configure(text=f"Active Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.after(1000, self.update_timer)
'''
    if 'def update_timer' not in content:
        content = content.replace('    def read_output(self):', update_timer_code + '\n    def read_output(self):')

    # Stop timer in bot_finished
    content = content.replace('self.bot_process = None', 'self.bot_process = None\n        self.timer_running = False\n        self.timer_label.configure(text="Active Runtime: 00:00:00")')

    with open(filepath, 'w') as f:
        f.write(content)
    print('Timer patched')

patch()
