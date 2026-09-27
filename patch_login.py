import sys

def patch_login():
    filepath = 'C:/Users/psy/Documents/antigravity/amazing-einstein/osrs-smart-bot/smart_sand_crab_bot.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_code = """        # 1. Check for RED 'Click here to play' button (Welcome Screen)"""
    new_code = """        # 1. OCR check for 'Play' text (Jagex Login or Welcome Screen)
        play_coords = find_text_coordinates(img, "play")
        if play_coords:
            cx, cy = play_coords
            print("    [*] Detected 'Play' text via OCR. Clicking...")
            cv2.imwrite("debug_login_screen.png", img)
            click_at(canvas_region["left"] + cx, canvas_region["top"] + cy, variation=15)
            time.sleep(random.gauss(6.0, 1.0))
            continue
            
        # 2. Check for RED 'Click here to play' button (Welcome Screen fallback)"""
        
    content = content.replace(old_code, new_code)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

patch_login()
