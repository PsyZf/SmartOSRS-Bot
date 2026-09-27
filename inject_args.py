import re

def update_script(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Add arguments to argparse if it exists
    if 'argparse.ArgumentParser' in content:
        if '--no-relogin' not in content:
            arg_block = """parser.add_argument("--no-food", action="store_true", help="Disable auto-eating")
parser.add_argument("--no-relogin", action="store_true", help="Disable auto-reconnect features")
parser.add_argument("--hotkey-stop", default="q", help="Hotkey to stop bot")
parser.add_argument("--hotkey-pause", default="p", help="Hotkey to pause bot")
parser.add_argument("--hotkey-force", default="w", help="Hotkey to force home")"""
            content = content.replace('parser.add_argument("--no-food", action="store_true", help="Disable auto-eating")', arg_block)

        # 2. Update hotkeys
        content = content.replace('keyboard.add_hotkey("q", stop_bot)', 'keyboard.add_hotkey(args.hotkey_stop, stop_bot)')
        content = content.replace('keyboard.add_hotkey("p", toggle_pause)', 'keyboard.add_hotkey(args.hotkey_pause, toggle_pause)')
        content = content.replace('keyboard.add_hotkey("w", trigger_force_home)', 'keyboard.add_hotkey(args.hotkey_force, trigger_force_home)')
        
        # 3. Update relogin check
        content = content.replace('if time_out_of_combat > 15:\n                if handle_reconnect():', 'if time_out_of_combat > 15 and not args.no_relogin:\n                if handle_reconnect():')
        
    with open(filepath, 'w') as f:
        f.write(content)
    print(f'Updated {filepath}')

update_script('C:/Users/psy/Documents/antigravity/amazing-einstein/osrs-bot/sand_crab_bot.py')
