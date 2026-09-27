import sys

def patch_bot():
    filepath = 'C:/Users/psy/Documents/antigravity/amazing-einstein/osrs-smart-bot/smart_sand_crab_bot.py'
    with open(filepath, 'r') as f:
        content = f.read()

    injection = """
            # ── Stream Latest Screenshot to GUI ───────────────────────────────────
            try:
                if loop_count % 2 == 0:  # Update every ~2 loops
                    with mss() as sct:
                        mon = {"top": int(offset_y), "left": int(offset_x), "width": int(win_width), "height": int(win_height)}
                        img = np.array(sct.grab(mon))
                        # Resize to fit nicely in GUI and save disk I/O
                        img = cv2.resize(img, (400, 300))
                        cv2.imwrite("latest_frame.jpg", img)
            except Exception as e:
                pass

            # ── Main loop idle — gaussian sleep so intervals are never identical ──
"""
    if "latest_frame.jpg" not in content:
        content = content.replace('            # ── Main loop idle — gaussian sleep so intervals are never identical ──', injection)
        with open(filepath, 'w') as f:
            f.write(content)
        print("Patched smart bot successfully.")
    else:
        print("Already patched smart bot.")

patch_bot()
