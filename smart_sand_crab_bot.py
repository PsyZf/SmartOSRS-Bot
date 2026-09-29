import argparse
import sys
import os
import threading
import time
import random
import math
import pyautogui
import keyboard
import cv2
import numpy as np
from mss import MSS

# Import our new Smart modules
from logger import logger
from vision import read_text_from_image, find_text_coordinates, detect_screen_action

# Setup command line arguments for flexible run-case usage
parser = argparse.ArgumentParser(description="OSRS Sand Crab Bot")
parser.add_argument("--debug", action="store_true", help="Enable detailed debug logs")
parser.add_argument("--no-pots", action="store_true", help="Disable combat potions")
parser.add_argument("--no-food", action="store_true", help="Disable auto-eating")
parser.add_argument("--no-relogin", action="store_true", help="Disable auto-reconnect features")
parser.add_argument("--hotkey-stop", default="q", help="Hotkey to stop bot")
parser.add_argument("--hotkey-pause", default="p", help="Hotkey to pause bot")
parser.add_argument("--hotkey-force", default="w", help="Hotkey to force home")
parser.add_argument("--max-time", type=float, help="Override random max runtime (in hours)")
parser.add_argument("--fast", action="store_true", help="Skip interactive startup menu")
parser.add_argument("--world-click", action="store_true", help="Use 3D world view for navigation instead of minimap")
args, unknown = parser.parse_known_args()

DEBUG_MODE = args.debug
WORLD_CLICK_NAV = args.world_click

# --- OSRS Sand Crab AFK Color Bot ---
# Built for Fixed - Classic Layout (765x503 canvas).
# WARNING: Automating OSRS gameplay is against Jagex Terms of Service and can result in account bans.
# Use at your own risk. This is provided for educational purposes.

# =============================================================================
# FIXED MODE UI REGION CONSTANTS
# Accurate for Fixed - Classic Layout. Coordinates are absolute screen positions
# assuming RuneLite window is at top-left of your primary monitor (0, 0).
# If your RuneLite window is NOT at (0,0), add your window offset to each value.
# =============================================================================

# --- Game Viewport ---
GAME_VIEWPORT = {"left": 4, "top": 4, "width": 512, "height": 334}

# --- Minimap ---
# Extended height by 30px downward to capture markers near the bottom edge.
MINIMAP_REGION = {"left": 565, "top": 9, "width": 156, "height": 182}
MINIMAP_CENTER = (643, 84)

# --- Orbs (left side of minimap panel) in Fixed Mode ---
HP_ORB     = (558, 54)   # Center of HP orb relative to canvas
PRAYER_ORB = (558, 94)   # Center of Prayer orb
RUN_ORB    = (558, 134)  # Center of Run energy orb
SPEC_ORB   = (558, 174)  # Center of Special attack orb

# --- Inventory Panel ---
# 4 columns x 7 rows = 28 slots.
INVENTORY_REGION = {"left": 554, "top": 205, "width": 179, "height": 261}
INVENTORY_SLOT_1 = (578, 228)  # Top-left slot center
INVENTORY_SLOT_W = 42          # Slot width
INVENTORY_SLOT_H = 36          # Slot height



# --- Chat Box ---
CHAT_REGION = {"left": 4, "top": 338, "width": 506, "height": 165}

# =============================================================================
# RUNTIME CONFIGURATION
# Edit these to tune the bot's behaviour.
# =============================================================================

# Aggro reset: fired after 10 minutes +/- a random offset each cycle.
# Gauss distribution gives a more natural, bell-curve spread rather than flat random.
def next_reset_time():
    """Returns next aggro reset interval in seconds using a gaussian distribution."""
    base   = 605          # ~10 min 5 sec base
    spread = 20           # std deviation in seconds
    return max(590, int(random.gauss(base, spread)))

RESET_TIME           = next_reset_time()
RUN_TIME_LIMIT_HOURS = random.uniform(5.0, 6.0)

# Randomize the hard shutdown failsafe between 25 and 26 minutes
FAILSAFE_SHUTDOWN_MINUTES = random.uniform(25.0, 26.0)

# Chance (out of 100) that a random break is taken each main loop cycle.
# Fluctuates slightly to remain unpredictable.
BREAK_CHANCE = random.randint(2, 4)

# ── Potion Configuration ──────────────────────────────────────────────────────
# Inventory slots are 0-indexed: 0-3 is top row, 4-7 is second row, etc.
# Set to empty lists [] if you don't want to use them.
COMBAT_POTION_SLOTS = []       # E.g. Super combat potions
COMBAT_POT_INTERVAL = random.gauss(580, 15) # Base time in seconds between sips (~9.5 mins)

# Health potions/food slots
HEALTH_FOOD_SLOTS   = []
# Threshold: if HP orb red pixels drop below this, bot eats/drinks
# A full HP orb has ~230-260 red pixels. Low HP is usually < 120 pixels.
LOW_HP_PIXEL_THRESHOLD = 130

# Apply CLI Overrides
if args.no_pots:
    COMBAT_POTION_SLOTS = []
if args.no_food:
    HEALTH_FOOD_SLOTS = []
if args.max_time:
    RUN_TIME_LIMIT_HOURS = args.max_time

# ── Minimap Clicking Tuning ───────────────────────────────────────────────────
# With titlebar auto-calibration active, no manual offset is required.
MINIMAP_CLICK_OFFSET_X = 0
MINIMAP_CLICK_OFFSET_Y = 0

# =============================================================================
# GLOBAL STATE
# =============================================================================
is_running       = True
loop_count       = 0
combat_pot_index = 0
food_index       = 0
last_pot_time    = time.time()  # Start timer now, don't drink immediately
last_combat_time = time.time()
last_antiban_time = 0

MARKER_WHITE_LOW  = (0, 0, 200)
MARKER_WHITE_HIGH = (180, 40, 255)

MARKER_MAGENTA_LOW  = (140, 215, 149)
MARKER_MAGENTA_HIGH = (160, 255, 255)

ACTIVE_HOME_LOW  = MARKER_MAGENTA_LOW
ACTIVE_HOME_HIGH = MARKER_MAGENTA_HIGH
ACTIVE_HOME_NAME = "Magenta (Home)"
last_crasher_time = 0

def stop_bot():
    global is_running
    is_running = False
    print("\n[!] Stop hotkey pressed. Stopping bot...")

is_paused = False
force_home_flag = False
old_sleep = time.sleep

class ForceHomeInterrupt(Exception):
    pass

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    if is_paused:
        print("\n[!] PAUSED - Press 'P' again to resume.")
    else:
        print("\n[!] UNPAUSED - Resuming bot...")

def trigger_force_home():
    global force_home_flag
    force_home_flag = True

def interruptable_sleep(duration):
    global force_home_flag, is_paused
    end_t = time.time() + duration
    while time.time() < end_t and is_running:
        while is_paused and is_running:
            old_sleep(0.1)
            end_t += 0.1
        if force_home_flag:
            raise ForceHomeInterrupt()
            
        sleep_chunk = min(0.1, max(0, end_t - time.time()))
        if sleep_chunk > 0:
            old_sleep(sleep_chunk)

time.sleep = interruptable_sleep

keyboard.add_hotkey(args.hotkey_stop, stop_bot)
keyboard.add_hotkey(args.hotkey_pause, toggle_pause)
keyboard.add_hotkey(args.hotkey_force, trigger_force_home)

# =============================================================================
# AUTO-CALIBRATION
# =============================================================================

def calibrate_window():
    """
    Finds the exact (0,0) canvas origin of the game window.
    Uses native Windows APIs to find the inner Java Canvas (SunAwtCanvas) for RuneLite, 
    completely bypassing custom title bars, borders, and OS themes.
    """
    global GAME_VIEWPORT, MINIMAP_REGION, COMPASS
    global CLIENT_OFFSET_X, CLIENT_OFFSET_Y
    
    print("[Setup] Auto-calibrating window position...")

    if os.name == 'nt':
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            
            found_hwnds = []
            def enum_cb(hwnd, lparam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title_low = buff.value.lower()
                        if 'runelite' in title_low or 'old school runescape' in title_low or 'osrs' in title_low:
                            rect = wintypes.RECT()
                            user32.GetClientRect(hwnd, ctypes.byref(rect))
                            cw = rect.right - rect.left
                            if cw >= 700:
                                found_hwnds.append((hwnd, buff.value))
                return True
            
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            
            if found_hwnds:
                main_hwnd, win_title = found_hwnds[0]
                target_hwnd = main_hwnd
                
                # If using RuneLite, find the inner Java canvas to bypass custom chrome titlebars
                child = user32.FindWindowExW(main_hwnd, 0, "SunAwtCanvas", None)
                if child:
                    target_hwnd = child
                    
                pt = wintypes.POINT(0, 0)
                user32.ClientToScreen(target_hwnd, ctypes.byref(pt))
                
                CLIENT_OFFSET_X = pt.x
                CLIENT_OFFSET_Y = pt.y
                print(f"    [+] Calibrated to '{win_title}' -> Canvas Origin: X:{CLIENT_OFFSET_X}, Y:{CLIENT_OFFSET_Y}")
                
                GAME_VIEWPORT["left"]  = 4   + CLIENT_OFFSET_X
                GAME_VIEWPORT["top"]   = 4   + CLIENT_OFFSET_Y
                MINIMAP_REGION["left"] = 565 + CLIENT_OFFSET_X
                MINIMAP_REGION["top"]  = 9   + CLIENT_OFFSET_Y
                return
        except Exception as e:
            if DEBUG_MODE:
                print(f"    [DEBUG] Native calibration failed: {e}")

    # Fallback
    CLIENT_OFFSET_X = 0
    CLIENT_OFFSET_Y = 32
    print(f"    [!] Native calibration failed. Using standard layout (Titlebar Y=32)")
    GAME_VIEWPORT["left"]  = 4   + CLIENT_OFFSET_X
    GAME_VIEWPORT["top"]   = 4   + CLIENT_OFFSET_Y
    MINIMAP_REGION["left"] = 565 + CLIENT_OFFSET_X
    MINIMAP_REGION["top"]  = 9   + CLIENT_OFFSET_Y

CLIENT_OFFSET_X = 0
CLIENT_OFFSET_Y = 32

# =============================================================================
# RANDOMIZED TIMING HELPERS
# =============================================================================

def gaussian_sleep(mean_ms, std_ms, min_ms=50, max_ms=None):
    """
    Sleeps for a duration drawn from a gaussian (normal) distribution.
    Far more human-like than uniform random.
    mean_ms / std_ms / min_ms / max_ms are all in milliseconds.
    """
    duration = random.gauss(mean_ms, std_ms)
    duration = max(min_ms, duration)
    if max_ms:
        duration = min(max_ms, duration)
    time.sleep(duration / 1000.0)

def random_sleep(min_ms, max_ms):
    """Uniform random sleep between min and max milliseconds."""
    time.sleep(random.randint(min_ms, max_ms) / 1000.0)

def reaction_delay():
    """
    Simulates human reaction time before acting.
    Uses a skewed distribution — humans are rarely faster than ~150ms
    but occasionally slow (~600ms).
    """
    # Lognormal gives a realistic right-skewed reaction time distribution
    delay_ms = random.lognormvariate(math.log(250), 0.4)
    delay_ms = max(120, min(700, delay_ms))
    time.sleep(delay_ms / 1000.0)

# =============================================================================
# RANDOMIZED MOUSE MOVEMENT
# =============================================================================

def _bezier_point(t, p0, p1, p2, p3):
    """Cubic bezier interpolation for smooth curved mouse paths."""
    return (
        (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0],
        (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1],
    )

def human_mouse_move(target_x, target_y, speed_variance=True):
    """
    Moves the mouse along a cubic bezier curve — far more human-like than a
    straight-line move. Speed varies with distance and is randomized.
    """
    start_x, start_y = pyautogui.position()
    dist = math.hypot(target_x - start_x, target_y - start_y)

    # Control points placed randomly off the direct path for a curved arc
    cp1 = (start_x  + random.randint(-80, 80), start_y  + random.randint(-80, 80))
    cp2 = (target_x + random.randint(-80, 80), target_y + random.randint(-80, 80))

    # Speed: faster for short moves, slower for long ones, with added variance
    base_duration = dist / random.uniform(900, 1400)
    duration = base_duration + random.uniform(0.05, 0.25) if speed_variance else base_duration

    steps = max(10, int(dist / 5))
    for i in range(steps + 1):
        linear_t = i / steps
        # Apply Sine Ease-Out to make the mouse naturally decelerate
        t = math.sin(linear_t * math.pi / 2)
        
        bx, by = _bezier_point(t, (start_x, start_y), cp1, cp2, (target_x, target_y))
        # Add micro-jitter on each step
        jx = bx + random.uniform(-0.8, 0.8)
        jy = by + random.uniform(-0.8, 0.8)
        pyautogui.moveTo(int(jx), int(jy), _pause=False)
        time.sleep(duration / steps)

def click_at(x, y, variation=6, double=False):
    """
    Moves to (x, y) with gaussian scatter, reacts, then clicks.
    Optionally double-clicks.
    """
    # Gaussian position scatter — most clicks land near centre, few land on edges
    tx = int(x + random.gauss(0, variation / 2))
    ty = int(y + random.gauss(0, variation / 2))

    human_mouse_move(tx, ty)
    reaction_delay()

    if double:
        pyautogui.doubleClick()
    else:
        pyautogui.click()

    gaussian_sleep(80, 30, min_ms=40)

# =============================================================================
# INVENTORY & STATUS HELPERS
# =============================================================================

def get_inv_slot_coord(slot_index):
    """Returns absolute (x, y) coordinates for an inventory slot (0-27)."""
    # 0-indexed inventory layout (4 cols x 7 rows)
    col = slot_index % 4
    row = slot_index // 4
    
    # Base coords of Slot 0 in fixed mode
    start_x = 578 + CLIENT_OFFSET_X
    start_y = 228 + CLIENT_OFFSET_Y
    slot_w, slot_h = 42, 36
    
    return (start_x + col * slot_w, start_y + row * slot_h)

def check_combat_status():
    """
    Looks for the bright green or red health bar above the player's head.
    If found, the player is actively in combat.
    """
    # Check a 100x100 box around the center of the viewport (where the player stands)
    cx = GAME_VIEWPORT["left"] + GAME_VIEWPORT["width"] // 2
    cy = GAME_VIEWPORT["top"]  + GAME_VIEWPORT["height"] // 2
    
    region = {"left": cx - 50, "top": cy - 50, "width": 100, "height": 100}
    img = capture_region(region)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # OSRS hitsplat/HP bar greens and reds
    green_mask = cv2.inRange(hsv, (55, 200, 200), (65, 255, 255))
    red_mask   = cv2.inRange(hsv, (0, 200, 200), (5, 255, 255))
    
    green_px = cv2.countNonZero(green_mask)
    red_px   = cv2.countNonZero(red_mask)
    
    if DEBUG_MODE:
        print(f"    [DEBUG] Combat Check - Green px: {green_px}, Red px: {red_px}")
    
    # If there are >10 pixels of HP bar colours, we are in combat
    return green_px > 10 or red_px > 10

def open_inventory_tab():
    print("    [*] Clicking Inventory tab (Bag icon) to ensure it is open...")
    bag_x = 643 + CLIENT_OFFSET_X
    bag_y = 184 + CLIENT_OFFSET_Y
    click_at(bag_x, bag_y, variation=6)
    time.sleep(0.5)

def check_health_and_eat():
    """
    Checks the HP orb's fill level. If red pixels drop below threshold, eat/drink.
    Searches the inventory for any item marked with a GREEN Inventory Tag and clicks it.
    """
    if len(HEALTH_FOOD_SLOTS) == 0:
        return # Auto-eat disabled in menu
        
    # HP orb inner circle region in Fixed Mode (left: 546, top: 42 relative to canvas)
    orb_region = {
        "left": 546 + CLIENT_OFFSET_X, 
        "top": 42 + CLIENT_OFFSET_Y, 
        "width": 26, 
        "height": 26
    }
    img = capture_region(orb_region)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Red heart / fill color (broadened for anti-aliasing and transparent theme support)
    mask1 = cv2.inRange(hsv, (0, 100, 80), (10, 255, 255))
    mask2 = cv2.inRange(hsv, (170, 100, 80), (180, 255, 255))
    red_pixels = cv2.countNonZero(mask1) + cv2.countNonZero(mask2)
    
    if DEBUG_MODE:
        print(f"    [DEBUG] HP Orb Check - Red pixels: {red_pixels} (Threshold: {LOW_HP_PIXEL_THRESHOLD})")
    
    if red_pixels < LOW_HP_PIXEL_THRESHOLD:
        print(f"    [!] Low Health Detected ({red_pixels} red pixels). Searching for Green tagged food...")
        
        inv_region = {
            "left": 554 + CLIENT_OFFSET_X,
            "top": 205 + CLIENT_OFFSET_Y,
            "width": 179,
            "height": 261
        }
        
        def find_and_eat_food():
            inv_img = capture_region(inv_region)
            green_centers = find_color_centers(inv_img, (50, 100, 100), (70, 255, 255), min_area=5, max_area=1000)
            if green_centers:
                green_centers.sort(key=lambda c: (c[1], c[0]))
                target = green_centers[0]
                cx = target[0] + inv_region["left"]
                cy = target[1] + inv_region["top"]
                print("    [+] Found Green tagged food. Eating...")
                click_at(cx, cy, variation=8)
                time.sleep(random.gauss(1.2, 0.2))
                return True
            return False

        if not find_and_eat_food():
            print("    [-] No Green tagged food found! Inventory might be closed.")
            open_inventory_tab()
            if not find_and_eat_food():
                print("    [!] Still no Green tagged food found. Out of food!")

def check_combat_potions():
    """Drinks a combat potion if the interval has elapsed."""
    global combat_pot_index, last_pot_time, COMBAT_POT_INTERVAL
    
    if combat_pot_index >= len(COMBAT_POTION_SLOTS):
        return # Out of combat pots
        
    current_time = time.time()
    if current_time - last_pot_time > COMBAT_POT_INTERVAL:
        print("    [*] Sipping combat potion...")
        open_inventory_tab() # Ensure inventory is open before clicking raw slots
        
        slot = COMBAT_POTION_SLOTS[combat_pot_index]
        cx, cy = get_inv_slot_coord(slot)
        click_at(cx, cy, variation=8)
        
        last_pot_time = current_time
        # Determine next sip interval (some gaussian randomness)
        COMBAT_POT_INTERVAL = random.gauss(580, 15)
        
        combat_pot_index += 1
        time.sleep(random.gauss(1.2, 0.2))


# =============================================================================
# SCREEN CAPTURE & COLOR DETECTION
# =============================================================================

# Global singleton to prevent recreating the DXGI/GDI context thousands of times
sct_engine = MSS()

def capture_region(region):
    """Captures a specific screen region dict {left, top, width, height}."""
    screenshot = np.array(sct_engine.grab(region))
    return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

def capture_screen():
    """Captures the full primary monitor."""
    monitor = sct_engine.monitors[1]
    screenshot = np.array(sct_engine.grab(monitor))
    return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

def find_color_centers(image, lower_hsv, upper_hsv, min_area=2, max_area=None):
    """
    Finds all blobs of a target HSV color range in image.
    Supports min_area and max_area filtering.
    Returns list of (x, y) center coords of each blob, sorted largest first.
    """
    hsv      = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask     = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    blobs = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        effective_area = max(area, float(w * h))
        
        if effective_area >= min_area:
            if max_area is not None and effective_area > max_area:
                continue
            # Use bounding box center instead of moments.
            # This is mathematically perfect for axis-aligned OSRS tile markers,
            # even if the outline is partially obscured by dots/NPCs.
            cx = x + w // 2
            cy = y + h // 2
            blobs.append((effective_area, cx, cy))

    # Sort by area descending so largest blob (most prominent marker) is first
    blobs.sort(key=lambda b: b[0], reverse=True)
    return [(cx, cy) for _, cx, cy in blobs]

def get_minimap_center(img, default_x=78, default_y=75):
    """
    Dynamically finds the exact (x, y) coordinate of the player's white dot inside the minimap image.
    This makes the bot immune to window titlebar height differences.
    """
    white_mask = cv2.inRange(img, (240, 240, 240), (255, 255, 255))
    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for c in contours:
        area = cv2.contourArea(c)
        if 2 <= area <= 50:
            x, y, w, h = cv2.boundingRect(c)
            cx = x + w // 2
            cy = y + h // 2
            # Must be roughly in the middle of the minimap region
            if abs(cx - default_x) < 35 and abs(cy - default_y) < 35:
                return cx, cy
                
    return default_x, default_y

# =============================================================================
# RECOVERY & FAILSAFES
# =============================================================================

def is_in_game():
    """
    Checks if the player is actively logged in to the game world.
    Checks the HP orb for health/numbers, the Run orb, and ensures the title screen is absent.
    """
    orb_region = {
        "left": 546 + CLIENT_OFFSET_X, 
        "top": 42 + CLIENT_OFFSET_Y, 
        "width": 26, 
        "height": 26
    }
    img = capture_region(orb_region)
    if img is None:
        return False
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    r1 = cv2.inRange(hsv, (0, 60, 50), (12, 255, 255))
    r2 = cv2.inRange(hsv, (168, 60, 50), (180, 255, 255))
    hp_red = cv2.countNonZero(r1) + cv2.countNonZero(r2)
    # If the HP orb has >= 5 red pixels (heart icon or health), player is in game
    if hp_red >= 5:
        return True
        
    # Check Run orb as secondary indicator (Center is 558, 134 -> bounding box 546, 122)
    run_region = {
        "left": 546 + CLIENT_OFFSET_X,
        "top": 122 + CLIENT_OFFSET_Y,
        "width": 26,
        "height": 26
    }
    img_run = capture_region(run_region)
    if img_run is not None:
        hsv_run = cv2.cvtColor(img_run, cv2.COLOR_BGR2HSV)
        run_yellow = cv2.countNonZero(cv2.inRange(hsv_run, (15, 60, 60), (38, 255, 255)))
        if run_yellow >= 25:
            return True

    return False

def handle_reconnect():
    """
    Detects if we are disconnected (HP orb missing).
    Attempts a 120-second recovery by dynamically detecting Disconnect / Retry popups,
    the Red 'Click here to play' welcome button, and Gold 'Play Now' login buttons.
    """
    if is_in_game():
        return False

    canvas_region = {
        "left": int(CLIENT_OFFSET_X),
        "top": int(CLIENT_OFFSET_Y),
        "width": 765,
        "height": 503
    }
    
    # Capture canvas and verify an actual reconnect/welcome/login screen is visible
    img = capture_region(canvas_region)
    action, coords = detect_screen_action(img)
    if action is None:
        # No disconnect or title screen is active - do nothing to prevent false clicks
        return False

    print(f"\n    [!] Disconnect/Title state detected ({action}). Starting recovery loop...")
    logger.log_event("DISCONNECT_START")
    
    start_time = time.time()
    
    while time.time() - start_time < 120:
        if is_in_game():
            print("    [+] Successfully logged back in!")
            logger.log_event("DISCONNECT_RECOVERED")
            return True

        img = capture_region(canvas_region)
        action, coords = detect_screen_action(img)
        
        if action == "WELCOME_PLAY":
            cx, cy = coords
            print(f"    [*] Detected Welcome Screen ({cx}, {cy}). Clicking 'Click here to play'...")
            cv2.imwrite("debug_welcome_screen.png", img)
            click_at(canvas_region["left"] + cx, canvas_region["top"] + cy, variation=10)
            pyautogui.press('space')
            time.sleep(random.gauss(5.0, 0.5))
            continue
            
        elif action == "DISCONNECT_RETRY":
            cx, cy = coords
            print(f"    [*] Detected Disconnect/Retry Screen ({cx}, {cy}). Clicking 'Try again'...")
            cv2.imwrite("debug_fallback_screen.png", img)
            click_at(canvas_region["left"] + cx, canvas_region["top"] + cy, variation=8)
            pyautogui.press('enter')
            time.sleep(random.gauss(4.0, 0.5))
            continue
            
        elif action == "LOGIN_BUTTON":
            cx, cy = coords
            print(f"    [*] Detected Login Screen ({cx}, {cy}). Clicking Login/Play...")
            cv2.imwrite("debug_login_screen.png", img)
            click_at(canvas_region["left"] + cx, canvas_region["top"] + cy, variation=10)
            time.sleep(random.gauss(5.0, 0.5))
            continue
            
        # If no recognized screen action, wait peacefully instead of clicking random pixels
        time.sleep(2.0)

    print("    [-] Recovery loop timed out. Could not reconnect.")
    logger.log_event("DISCONNECT_TIMEOUT")
    return False

def recover_path():
    """
    Emergency recovery if lost or stuck.
    1. Checks if any primary route markers (Magenta, Cyan) are in view.
       If so, navigates back along the route to Home.
    2. If no route markers are in view, follows the closest Black breadcrumb, then
       immediately re-scans for route markers.
    3. If no markers at all are seen, attacks an on-screen Sand Crab to resume combat.
    Returns True if an action was taken.
    """
    print("    [!] Attempting smart path recovery (pressing ESC in case of obstructing interfaces)...")
    logger.log_event("RECOVER_PATH_START")
    pyautogui.press('esc')
    time.sleep(0.5)

    MARKER_MAGENTA_LOW  = (140, 215, 149)
    MARKER_MAGENTA_HIGH = (160, 255, 255)
    MARKER_CYAN_LOW     = (80, 100, 100)
    MARKER_CYAN_HIGH    = (100, 255, 255)
    MARKER_BLACK_LOW    = (0, 0, 0)
    MARKER_BLACK_HIGH   = (180, 255, 45)

    if WORLD_CLICK_NAV:
        offset_x = GAME_VIEWPORT["left"]
        offset_y = GAME_VIEWPORT["top"]
        mc_x     = GAME_VIEWPORT["width"]  // 2
        mc_y     = GAME_VIEWPORT["height"] // 2
        region   = GAME_VIEWPORT
        min_a    = 50
        max_a    = None
    else:
        offset_x = MINIMAP_REGION["left"]
        offset_y = MINIMAP_REGION["top"]
        mc_x     = 78
        mc_y     = 75
        region   = MINIMAP_REGION
        min_a    = 2
        max_a    = 350

    def dist_to_mc(p):
        return math.hypot(p[0] - mc_x, p[1] - mc_y)

    # Helper: Check and click any visible primary route block
    def check_primary_route():
        img = capture_region(region)
        nonlocal mc_x, mc_y
        if not WORLD_CLICK_NAV:
            mc_x, mc_y = get_minimap_center(img, mc_x, mc_y)
        
        # Priority 1: Magenta (Home)
        m_centers = find_color_centers(img, MARKER_MAGENTA_LOW, MARKER_MAGENTA_HIGH, min_area=min_a, max_area=max_a)
        if m_centers:
            closest_m = min(m_centers, key=dist_to_mc)
            print(f"    [+] Recovery: Sighted Magenta (Home) marker at {closest_m}. Walking home...")
            click_at(closest_m[0] + offset_x, closest_m[1] + offset_y, variation=4)
            time.sleep(random.gauss(8.5, 0.7))
            return True

        # Priority 2: Cyan (Mid waypoint)
        c_centers = find_color_centers(img, MARKER_CYAN_LOW, MARKER_CYAN_HIGH, min_area=min_a, max_area=max_a)
        if c_centers:
            closest_c = min(c_centers, key=dist_to_mc)
            print(f"    [+] Recovery: Sighted Cyan (Mid) marker at {closest_c}. Walking to Mid...")
            click_at(closest_c[0] + offset_x, closest_c[1] + offset_y, variation=4)
            time.sleep(random.gauss(8.5, 0.6))
            
            # After arriving at Mid, immediately look for Magenta (Home)
            img2 = capture_region(region)
            m2 = find_color_centers(img2, MARKER_MAGENTA_LOW, MARKER_MAGENTA_HIGH, min_area=min_a, max_area=max_a)
            if m2:
                target = min(m2, key=dist_to_mc)
                print(f"    [+] Recovery: Found Magenta (Home) from Mid! Walking to {target}...")
                click_at(target[0] + offset_x, target[1] + offset_y, variation=4)
                time.sleep(random.gauss(8.5, 0.7))
            return True

        return False

    # Step 1: Are any primary route markers already in view?
    if check_primary_route():
        return True

    # Step 2: If no primary route markers visible, use Black breadcrumbs
    attempts = 0
    while attempts < 10:
        img = capture_region(region)
        if not WORLD_CLICK_NAV:
            mc_x, mc_y = get_minimap_center(img, mc_x, mc_y)
            
        black_centers = find_color_centers(img, MARKER_BLACK_LOW, MARKER_BLACK_HIGH, min_area=min_a, max_area=max_a)
        if not black_centers:
            break
            
        closest = min(black_centers, key=dist_to_mc)
        print(f"    [+] Following Black breadcrumb at {closest}...")
        click_at(closest[0] + offset_x, closest[1] + offset_y, variation=4)
        walk_wait = random.gauss(8.5, 0.7)
        time.sleep(max(7.0, min(10.0, walk_wait)))

        # After stepping on breadcrumb, immediately check if route markers came into view!
        if check_primary_route():
            return True
            
        attempts += 1

    # Step 3: No markers on minimap at all — look for Sand Crab NPC highlight to attack
    print("    [-] No markers on minimap. Looking for Sand Crabs on screen...")
    vp_img = capture_region(GAME_VIEWPORT)
    crab_centers = find_color_centers(vp_img, (80, 100, 100), (100, 255, 255), min_area=20)
    if crab_centers:
        cx, cy = crab_centers[0]
        print("    [+] Found Sand Crab on screen. Attacking...")
        click_at(cx + GAME_VIEWPORT["left"], cy + GAME_VIEWPORT["top"], variation=8)
        time.sleep(random.gauss(4.0, 0.5))
        return True

    return False


# =============================================================================
# AGGRO RESET
# =============================================================================

def reset_aggro():
    """
    Aggression reset using minimap ground markers.
    Route:
      Home (Magenta) -> Mid (Cyan, if visible) -> Far (Blue) -> Mid (Cyan, if visible) -> Home (Magenta)
    """
    MARKER_MAGENTA_LOW  = (140, 215, 149)
    MARKER_MAGENTA_HIGH = (160, 255, 255)
    
    MARKER_CYAN_LOW     = (80, 100, 100)
    MARKER_CYAN_HIGH    = (100, 255, 255)

    MARKER_BLUE_LOW     = (110, 100, 100)
    MARKER_BLUE_HIGH    = (130, 255, 255)

    print("\n[*] Initiating Sand Crab aggression reset route...")

    if WORLD_CLICK_NAV:
        offset_x = GAME_VIEWPORT["left"]
        offset_y = GAME_VIEWPORT["top"]
        mc_x     = GAME_VIEWPORT["width"]  // 2
        mc_y     = GAME_VIEWPORT["height"] // 2
        region   = GAME_VIEWPORT
        min_a    = 50
        max_a    = None
    else:
        offset_x = MINIMAP_REGION["left"]
        offset_y = MINIMAP_REGION["top"]
        mc_x     = 78
        mc_y     = 75
        region   = MINIMAP_REGION
        min_a    = 2
        max_a    = 350
        
    center_screen_x = offset_x + mc_x
    center_screen_y = offset_y + mc_y

    def get_markers(low_hsv, high_hsv):
        """Fresh capture -> absolute screen coords for each marker blob."""
        img     = capture_region(region)
        nonlocal center_screen_x, center_screen_y
        if not WORLD_CLICK_NAV:
            mx, my = get_minimap_center(img, mc_x, mc_y)
            center_screen_x = offset_x + mx
            center_screen_y = offset_y + my
            
        centers = find_color_centers(img, low_hsv, high_hsv, min_area=min_a, max_area=max_a)
        return [(cx + offset_x, cy + offset_y) for cx, cy in centers]

    def dist_from_center(p):
        return math.hypot(p[0] - center_screen_x, p[1] - center_screen_y)

    def walk_to_target(target_coord, name, wait_time=8.5):
        print(f"    -> {name} marker clicked at {target_coord}...")
        click_at(*target_coord, variation=4)
        walk_wait = random.gauss(wait_time, 1.0)
        walk_wait = max(7.0, min(12.0, walk_wait))
        if DEBUG_MODE:
            print(f"    [DEBUG] Walk_to ({name}) wait: {walk_wait:.2f}s")
        time.sleep(walk_wait)

    def poll_marker(color_low, color_high, name, max_wait=20.0):
        """Polls for a marker and returns its closest coordinate to minimap center."""
        print(f"    -> Scanning for {name} marker...")
        waited = 0.0
        POLL_INTERVAL = 1.2
        while waited < max_wait:
            fresh = get_markers(color_low, color_high)
            if fresh:
                return min(fresh, key=dist_from_center)
            time.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL
        print(f"    [!] {name} marker not found.")
        return None

    # Step 1: Walk to Cyan (Mid) if visible
    cyan_markers = get_markers(MARKER_CYAN_LOW, MARKER_CYAN_HIGH)
    if cyan_markers:
        print("    [+] Cyan (Mid) marker detected. Initiating 3-point route...")
        cyan_target = min(cyan_markers, key=dist_from_center)
        walk_to_target(cyan_target, "Cyan (Mid)")
    else:
        print("    [-] No Cyan (Mid) marker detected. Initiating 2-point route...")

    # Step 2: Walk to Blue (Far)
    far_coord = poll_marker(MARKER_BLUE_LOW, MARKER_BLUE_HIGH, "Blue (Far)")
    if far_coord:
        walk_to_target(far_coord, "Blue (Far)")
        time.sleep(random.gauss(2.0, 0.5))  # Brief pause at Far point to ensure aggro boundary reset
    else:
        print("    [!] Critical Error: Blue (Far) marker not found. Cannot reset aggro properly.")
        recover_path()
        return

    # Step 3: Walk back to Cyan (Mid) if we used it
    if cyan_markers:
        mid_coord = poll_marker(MARKER_CYAN_LOW, MARKER_CYAN_HIGH, "Cyan (Mid)")
        if mid_coord:
            walk_to_target(mid_coord, "Cyan (Mid)")
        else:
            recover_path()
            return

    # Step 4: Walk back to Home
    home_coord = poll_marker(ACTIVE_HOME_LOW, ACTIVE_HOME_HIGH, ACTIVE_HOME_NAME)
    if home_coord:
        walk_to_target(home_coord, ACTIVE_HOME_NAME)
    else:
        print("    [!] Home marker not found!")
        recover_path()
        return

    print("[*] Aggro reset complete. Verifying home tile alignment...")
    time.sleep(2.0)
    check_home_alignment()
    time.sleep(3.0)
    print("    [*] Secondary alignment check to ensure player has settled...")
    check_home_alignment()


# =============================================================================
# ANTI-BAN ACTIONS
# These fire probabilistically each loop cycle to mimic human behaviour.
# =============================================================================

def anti_ban_actions():
    """
    A weighted pool of anti-ban micro-behaviours.
    Only fires occasionally and picks a single action to prevent robotic bursting.
    """
    global loop_count, last_antiban_time
    
    current_time = time.time()
    
    # Must wait at least 45-120 seconds between ANY antiban action
    if current_time - last_antiban_time < random.randint(45, 120):
        return

    # 15% chance to trigger an antiban action this cycle (if off cooldown)
    if random.random() > 0.15:
        return
        
    last_antiban_time = current_time
    
    # Pick exactly ONE action to perform
    action_type = random.choices(["drift", "chat", "hp", "camera"], weights=[30, 25, 30, 15], k=1)[0]

    if action_type == "drift":
        # Drift somewhere inside the game viewport
        drift_x = random.randint(GAME_VIEWPORT["left"] + 10, GAME_VIEWPORT["left"] + GAME_VIEWPORT["width"] - 10)
        drift_y = random.randint(GAME_VIEWPORT["top"]  + 10, GAME_VIEWPORT["top"]  + GAME_VIEWPORT["height"] - 10)
        print(f"[*] Antiban: Idle mouse drift to ({drift_x}, {drift_y})")
        human_mouse_move(drift_x, drift_y)

    elif action_type == "chat":
        pause = random.gauss(3.5, 1.2)
        pause = max(1.5, min(7.0, pause))
        print(f"[*] Antiban: Reading chat pause ({pause:.1f}s)")
        time.sleep(pause)

    elif action_type == "hp":
        print("[*] Antiban: Checking HP orb and verifying coordinates...")
        # Exact center of the HP Orb
        hx = 559 + CLIENT_OFFSET_X
        hy = 55 + CLIENT_OFFSET_Y
        human_mouse_move(hx, hy)
        gaussian_sleep(200, 50, min_ms=100, max_ms=400)
        
        # Verify that the pixel we are hovering over is actually the red HP orb
        check_region = {"left": hx - 5, "top": hy - 5, "width": 10, "height": 10}
        img = capture_region(check_region)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        r1 = cv2.inRange(hsv, (0, 100, 80), (10, 255, 255))
        r2 = cv2.inRange(hsv, (170, 100, 80), (180, 255, 255))
        if cv2.countNonZero(r1) + cv2.countNonZero(r2) < 5:
            print("    [!] CRITICAL: HP Orb is not red! Client window has moved!")
            print("    [!] Attempting emergency window re-calibration...")
            calibrate_window()
        else:
            print("    [+] Coordinate drift check passed (HP Orb verified).")
            
        gaussian_sleep(400, 150, min_ms=200, max_ms=900)

    elif action_type == "camera":
        print("[*] Antiban: Minor camera nudge")
        cx = random.randint(150, 350) + CLIENT_OFFSET_X
        cy = random.randint(100, 250) + CLIENT_OFFSET_Y
        pyautogui.moveTo(cx, cy, _pause=False)
        gaussian_sleep(120, 40)
        pyautogui.mouseDown(button='right')
        pyautogui.moveRel(random.randint(-8, 8), random.randint(-4, 4), duration=random.uniform(0.15, 0.3))
        pyautogui.mouseUp(button='right')

def take_break():
    """
    Simulates the player stepping away for a short while.
    Does nothing but wait. Mouse stays still.
    """
    break_duration = random.gauss(45, 15)
    break_duration = max(20, min(90, break_duration))
    print(f"\n[*] Taking a short break ({break_duration:.0f}s) — simulating AFK...")
    time.sleep(break_duration)
    print("[*] Break over. Resuming.\n")

# =============================================================================
# CAMERA & CLIENT SETUP
# Runs once at startup to put the client in the exact same known state
# every time the bot starts, regardless of where the camera was left.
# =============================================================================

# Fixed Mode compass position — the small N/compass icon attached to the minimap.
# In Fixed Classic Layout (765x503) this is always at (571, 11).
COMPASS = (571, 11)

# Centre of the game viewport — used as hover target for scroll zooming.
VIEWPORT_CENTER = (
    GAME_VIEWPORT["left"] + GAME_VIEWPORT["width"]  // 2,
    GAME_VIEWPORT["top"]  + GAME_VIEWPORT["height"] // 2,
)

def setup_camera():
    """
    Puts the camera into a known, consistent state:
      1. Click compass  -> snaps camera to True North instantly
      2. Scroll down x20 -> zooms fully out  (OSRS max zoom = ~20 scroll clicks)
      3. Hold Up Arrow x2 -> pitches camera to top-down view
         (requires RuneLite Camera plugin with 'Expand pitch limit' ON)

    All actions have small human-like delays between them.
    """
    print("[Setup] Configuring camera...")

    # ── 1. True North: click the compass icon ────────────────────────────────
    print("[Setup] -> Clicking compass for True North...")
    cx = 571 + CLIENT_OFFSET_X
    cy = 11  + CLIENT_OFFSET_Y
    human_mouse_move(cx, cy)
    gaussian_sleep(200, 60)
    pyautogui.click()
    gaussian_sleep(400, 100)   # brief pause after click

    # ── 2. Zoom fully out: hover game viewport, scroll down many times ───────
    print("[Setup] -> Zooming out fully...")
    human_mouse_move(*VIEWPORT_CENTER)
    gaussian_sleep(200, 60)
    # 20 scroll-down clicks is enough to hit the zoom floor from any position.
    # We break it into two bursts of 10 with a tiny pause to seem more natural.
    for _ in range(10):
        pyautogui.scroll(-3)   # negative = scroll down = zoom out in OSRS
        time.sleep(random.uniform(0.04, 0.09))
    gaussian_sleep(300, 80)
    for _ in range(10):
        pyautogui.scroll(-3)
        time.sleep(random.uniform(0.04, 0.09))
    gaussian_sleep(400, 100)

    # ── 3. Pitch to top-down: hold Up Arrow ──────────────────────────────────
    # RuneLite Camera plugin must have 'Expand pitch limit' enabled.
    # Standard OSRS pitch limit is ~383; expanded allows full top-down (~512).
    # Holding Up Arrow while the game window is focused pitches the camera up.
    # We hold for ~2.5s which is enough to reach the ceiling from any angle.
    print("[Setup] -> Pitching camera top-down (hold Up Arrow)...")
    gaussian_sleep(150, 50)

    # Hold Up Arrow — split into two presses so it reads less robotic
    hold_time = random.uniform(2.2, 2.8)
    pyautogui.keyDown('up')
    time.sleep(hold_time)
    pyautogui.keyUp('up')
    gaussian_sleep(200, 60)
    # Second short tap to make sure we're pinned to the ceiling
    pyautogui.keyDown('up')
    time.sleep(random.uniform(0.4, 0.7))
    pyautogui.keyUp('up')
    gaussian_sleep(300, 80)

    print("[Setup] Camera setup complete. North / Zoomed out / Top-down.\n")

# =============================================================================
# INTERACTIVE STARTUP MENU
# =============================================================================

def interactive_startup_menu():
    """
    Displays an interactive settings menu when the bot starts.
    Allows toggling Food, Potions, Debug logs, or setting a custom runtime.
    """
    global HEALTH_FOOD_SLOTS, COMBAT_POTION_SLOTS, DEBUG_MODE, RUN_TIME_LIMIT_HOURS, WORLD_CLICK_NAV

    if args.fast:
        return

    while True:
        food_status = "ENABLED (Slots 4-7)" if len(HEALTH_FOOD_SLOTS) > 0 else "DISABLED"
        pot_status  = "ENABLED (Slots 0-3)" if len(COMBAT_POTION_SLOTS) > 0 else "DISABLED"
        dbg_status  = "ON" if DEBUG_MODE else "OFF"
        
        print("\n" + "=" * 48)
        print("         OSRS SAND CRAB BOT -- CONFIG MENU      ")
        print("=" * 48)
        print(f"  [1] Food / Auto-Eat:     [{food_status}]")
        print(f"  [2] Combat Potions:      [{pot_status}]")
        print(f"  [3] Debug Logs:          [{dbg_status}]")
        print(f"  [4] Max Runtime:         [{RUN_TIME_LIMIT_HOURS:.1f} hours]")
        print(f"  [5] 3D World Click Nav:  [{'ON' if WORLD_CLICK_NAV else 'OFF'}]")
        print("-" * 48)
        print("  * Enter a number (1-5) to toggle or change a setting.")
        print("  * Press [ENTER] to confirm and launch the bot.")
        print("=" * 48)

        try:
            choice = input("Select option (or press Enter to start): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "":
            break
        elif choice == "1":
            if len(HEALTH_FOOD_SLOTS) > 0:
                HEALTH_FOOD_SLOTS = []
                print("  -> Auto-eat DISABLED.")
            else:
                HEALTH_FOOD_SLOTS = [4, 5, 6, 7]
                print("  -> Auto-eat ENABLED.")
        elif choice == "2":
            if len(COMBAT_POTION_SLOTS) > 0:
                COMBAT_POTION_SLOTS = []
                print("  -> Combat Potions DISABLED.")
            else:
                COMBAT_POTION_SLOTS = [0, 1, 2, 3]
                print("  -> Combat Potions ENABLED.")
        elif choice == "3":
            DEBUG_MODE = not DEBUG_MODE
            print(f"  -> Debug Mode set to {'ON' if DEBUG_MODE else 'OFF'}.")
        elif choice == "4":
            val = input("  Enter max runtime in hours (e.g. 3.5 or 6): ").strip()
            try:
                RUN_TIME_LIMIT_HOURS = float(val)
                print(f"  -> Runtime set to {RUN_TIME_LIMIT_HOURS:.1f} hours.")
            except ValueError:
                print("  [!] Invalid number entered.")
        elif choice == "5":
            WORLD_CLICK_NAV = not WORLD_CLICK_NAV
            print(f"  -> 3D World Click Nav set to {'ON' if WORLD_CLICK_NAV else 'OFF'}.")

def is_crasher_present():
    """
    Scans the 3D game world for a Red tile (Player indicator), avoiding health bars.
    If a large Red square/polygon is found, another player is standing on our tile or nearby.
    """
    img = capture_region(GAME_VIEWPORT)
    if img is None:
        return False
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Red wraps around HSV 0 and 180
    mask1 = cv2.inRange(hsv, (0, 150, 150), (10, 255, 255))
    mask2 = cv2.inRange(hsv, (170, 150, 150), (180, 255, 255))
    red_mask = cv2.bitwise_or(mask1, mask2)
    
    # Mask out fixed UI elements (Minimap, Chatbox) to avoid hitsplats or map dots
    red_mask[0:170, 550:] = 0
    red_mask[340:, 0:520] = 0
    
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        area = cv2.contourArea(c)
        if area > 180: # Tile markers are large polygons, health bars are small rectangles
            x, y, w, h = cv2.boundingRect(c)
            ratio = w / float(h)
            if 0.5 < ratio < 4.0: # Exclude extreme long thin lines (just in case)
                return True
    return False

def check_home_alignment():
    """
    Periodic self-correction: Checks if the player is perfectly centered on the Active Home tile.
    Because the player is always at the dead-center of the minimap (or 3D view), 
    the active ground marker should be mathematically centered on the screen.
    If it's more than a few pixels off, we walk to correct it.
    """
    global ACTIVE_HOME_LOW, ACTIVE_HOME_HIGH, ACTIVE_HOME_NAME

    if WORLD_CLICK_NAV:
        offset_x = GAME_VIEWPORT["left"]
        offset_y = GAME_VIEWPORT["top"]
        mc_x     = GAME_VIEWPORT["width"]  // 2
        mc_y     = GAME_VIEWPORT["height"] // 2
        region   = GAME_VIEWPORT
        min_a    = 50
        max_a    = None
        tolerance = 15  # Pixels tolerance for 3D world view (tiles are larger)
    else:
        offset_x = MINIMAP_REGION["left"]
        offset_y = MINIMAP_REGION["top"]
        mc_x     = 78  # Exact center of minimap circle relative to region (643 - 565)
        mc_y     = 75  # Exact center of minimap circle relative to region (84 - 9)
        region   = MINIMAP_REGION
        min_a    = 2
        max_a    = 350
        tolerance = 2.5 # Pixels tolerance for Minimap (tiles are tiny, 2.5px is ~1/2 tile)

    img = capture_region(region)
    if not WORLD_CLICK_NAV:
        mc_x, mc_y = get_minimap_center(img, mc_x, mc_y)

    m_centers = find_color_centers(img, ACTIVE_HOME_LOW, ACTIVE_HOME_HIGH, min_area=min_a, max_area=max_a)

    if m_centers:
        def dist_to_mc(p):
            return math.hypot(p[0] - mc_x, p[1] - mc_y)

        closest_m = min(m_centers, key=dist_to_mc)
        dist = dist_to_mc(closest_m)

        # If the closest magenta marker is further than the tolerance, we are off the tile!
        if dist > tolerance:
            print(f"    [*] Alignment Check: Off-center by {dist:.1f}px (Limit {tolerance}). Correcting...")
            click_at(closest_m[0] + offset_x, closest_m[1] + offset_y, variation=2)
            time.sleep(random.gauss(2.5, 0.5))
            return True
        else:
            print(f"    [*] Alignment Check: Perfectly centered. (Offset: {dist:.1f}px)")
    else:
        print("    [!] Alignment Check: No Magenta marker found near player!")
    return False


# =============================================================================
# MAIN LOOP
# =============================================================================

def main():
    global loop_count, RESET_TIME, is_running, last_combat_time
    idle_history = []  # Tracks timestamps of recent idles

    # Interactive options menu
    interactive_startup_menu()

    print("\n=========================================")
    print("   OSRS Sand Crab Bot -- Fixed Mode      ")
    print("=========================================")
    print(f"Max Runtime Limit: {RUN_TIME_LIMIT_HOURS:.1f} hours")
    print(f"Food enabled:      {'YES' if len(HEALTH_FOOD_SLOTS) > 0 else 'NO'}")
    print(f"Potions enabled:   {'YES' if len(COMBAT_POTION_SLOTS) > 0 else 'NO'}")
    print(f"Debug Mode:        {'ON' if DEBUG_MODE else 'OFF'}")
    print(f"World-Click Nav:   {'ON' if WORLD_CLICK_NAV else 'OFF'} (Experimental)")
    print("-----------------------------------------")
    print("Hotkeys:")
    print("  Q  -> Stop the bot immediately")
    print("  P  -> Pause / Unpause the bot")
    print("  W  -> Force path recovery to Home tile")
    print("  PyAutoGUI Failsafe: move mouse to any screen CORNER to abort")
    print()
    print("Starting in 5 seconds... switch to your RuneLite window now.")

    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Auto-calibrate window position
    calibrate_window()

    def _stream_preview_loop():
        """Continuously streams latest game frames to latest_frame.jpg for the GUI."""
        while is_running:
            try:
                stream_box = {
                    "left": int(CLIENT_OFFSET_X),
                    "top": int(CLIENT_OFFSET_Y),
                    "width": 765,
                    "height": 503
                }
                frame = capture_region(stream_box)
                if frame is not None:
                    preview = cv2.resize(frame, (580, 381))
                    cv2.imwrite("latest_frame_tmp.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if os.path.exists("latest_frame_tmp.jpg"):
                        os.replace("latest_frame_tmp.jpg", "latest_frame.jpg")
            except Exception:
                pass
            time.sleep(1.0)

    # Launch live streaming daemon thread
    threading.Thread(target=_stream_preview_loop, daemon=True).start()

    # Run camera setup before the main loop begins
    setup_camera()

    print("[+] Bot started!\n")

    start_time           = time.time()
    last_aggro_reset     = time.time()
    last_alignment_check = time.time()

    while is_running:
        try:
            loop_count   += 1
            current_time  = time.time()
            elapsed       = current_time - start_time
            since_reset   = current_time - last_aggro_reset

            # ── Hard runtime ceiling ──────────────────────────────────────────────
            if elapsed > RUN_TIME_LIMIT_HOURS * 3600:
                print("[!] Runtime limit reached. Shutting down.")
                break

            # ── Health & Potions ──────────────────────────────────────────────────
            check_health_and_eat()
            check_combat_potions()

            # ── Combat Status Monitoring & Failsafes ──────────────────────────────
            # Check if we have a health bar above our head
            if check_combat_status():
                time_out_of_combat = 0
                last_combat_time = current_time
            else:
                time_out_of_combat = current_time - last_combat_time
            
                # Failsafe 1: Complete shutdown if stuck for 25-26 mins
                if time_out_of_combat > FAILSAFE_SHUTDOWN_MINUTES * 60:
                    print(f"\n[!!!] FAILSAFE: Out of combat for {time_out_of_combat/60:.1f} mins!")
                    print("[!!!] Shutting down to prevent standing idle permanently.")
                    is_running = False
                    break
                
                # Try to handle disconnect/6-hour log if we are completely idle and interface is lost
                if time_out_of_combat > 20 and not is_in_game():
                    if handle_reconnect():
                        # If we reconnected, reset the combat timer to give it time to load in
                        last_combat_time = time.time()
                        continue

                # Out of combat periodic status notification
                if 25 <= time_out_of_combat < 60 and loop_count % 8 == 0:
                    print(f"    [*] Out of combat for {time_out_of_combat:.0f}s (Aggro reset in {max(0, int(RESET_TIME - since_reset))}s or at 60s idle)...")

                # Fallback: If out of combat for 60 seconds, trigger full aggro reset route
                if time_out_of_combat >= 60:
                    print(f"\n    [WARNING] Out of combat for {time_out_of_combat:.0f}s (60s limit reached)! Triggering full Aggro Reset route...")
                    reset_aggro()
                    last_aggro_reset = time.time()
                    last_combat_time = time.time()
                    RESET_TIME = next_reset_time()
                    print(f"[*] Next aggro reset in {RESET_TIME}s ({RESET_TIME/60:.1f} min)")

            # ── Aggro reset check ─────────────────────────────────────────────────
            if since_reset > RESET_TIME:
                if time_out_of_combat > 3:
                    print(f"\n[*] Aggro timer expired ({RESET_TIME/60:.1f} min). Out of combat, resetting now...")
                    reset_aggro()
                    last_aggro_reset = time.time()
                    last_combat_time = time.time() # Reset combat timer so we don't spam warning
                    RESET_TIME = next_reset_time()
                    print(f"[*] Next aggro reset in {RESET_TIME}s ({RESET_TIME/60:.1f} min)")
                elif time_out_of_combat == 0 and loop_count % 10 == 0:
                    print(f"    [*] Aggro timer expired, but waiting for current combat to finish before resetting...")

            # ── Crasher Protection (Red Tile Detection) ───────────────────────────
            global ACTIVE_HOME_COLOR, ACTIVE_HOME_NAME, last_crasher_time
            if loop_count % 3 == 0:
                if is_crasher_present():
                    last_crasher_time = current_time
                    if ACTIVE_HOME_NAME == "Magenta (Home)":
                        print("\n[!] CRASHER DETECTED (Red Tile)! Retreating to White (Backup) tile...")
                        ACTIVE_HOME_COLOR = (MARKER_WHITE_LOW, MARKER_WHITE_HIGH)
                        ACTIVE_HOME_NAME = "White (Backup)"
                        check_home_alignment() # Walk to new backup home
                else:
                    if ACTIVE_HOME_NAME == "White (Backup)" and (current_time - last_crasher_time > 90):
                        print("\n[+] Spot clear for 90s! Returning to primary Magenta (Home) tile...")
                        ACTIVE_HOME_COLOR = (MARKER_MAGENTA_LOW, MARKER_MAGENTA_HIGH)
                        ACTIVE_HOME_NAME = "Magenta (Home)"
                        check_home_alignment() # Walk back to primary home

            # ── Periodic alignment check ──────────────────────────────────────────
            # Check every 2-4 minutes (instead of every 60 seconds) to look more human
            if current_time - last_alignment_check > random.randint(120, 240):
                if since_reset > 15 and since_reset < RESET_TIME - 15:
                    check_home_alignment()
                last_alignment_check = current_time

            # ── Occasional break ──────────────────────────────────────────────────
            # Only take a break if we are comfortably in combat and not about to reset aggro
            if random.randint(1, 100) <= BREAK_CHANCE:
                if since_reset < RESET_TIME - 45 and time_out_of_combat < 15:
                    take_break()

            # ── Anti-ban micro-actions ────────────────────────────────────────────
            anti_ban_actions()

            # ── Main loop idle — gaussian sleep so intervals are never identical ──
            idle = random.gauss(2.0, 0.6)
            idle = max(0.8, min(4.5, idle))
            time.sleep(idle)

        except ForceHomeInterrupt:
            global force_home_flag
            force_home_flag = False
            print('\n[!] Manual Override: W hotkey pressed. Forcing path recovery to Home...')
            recover_path()
            last_combat_time = time.time()
            continue
    print("\n[+] Bot stopped successfully.")

if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0   # We handle all timing manually for full control
    main()
