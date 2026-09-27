import sys

def patch_gui():
    filepath = 'C:/Users/psy/Documents/antigravity/amazing-einstein/osrs-smart-bot/gui_app.py'
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Change text on start/stop buttons
    content = content.replace('text="▶ START BOT"', 'text="START BOT"')
    content = content.replace('text="■ STOP BOT"', 'text="STOP BOT"')

    # 2. Adjust pady to pack controls tighter (replace (15, 10) with (5, 5))
    content = content.replace('pady=(20, 10)', 'pady=(5, 5)')
    content = content.replace('pady=(15, 0)', 'pady=(5, 0)')
    content = content.replace('pady=(15, 10)', 'pady=(5, 5)')
    content = content.replace('pady=(0, 20)', 'pady=(0, 5)')
    content = content.replace('pady=(5, 15)', 'pady=(5, 5)')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

patch_gui()
