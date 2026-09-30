import cv2
import numpy as np
import time
import os
import random
import math
import argparse
import keyboard
import pyautogui
from mss import mss
import threading

# =============================================================================
# BASIC BOT CONFIGURATION
# =============================================================================

MARKER_CYAN_LOW    = (80, 100, 100)
MARKER_CYAN_HIGH   = (100, 255, 255)
MARKER_GREEN_LOW    = (45, 100, 100)
MARKER_GREEN_HIGH   = (75, 255, 255)
MARKER_MAGENTA_LOW = (140, 100, 100)
MARKER_MAGENTA_HIGH= (160, 255, 255)

sct_engine = mss()
is_running = True

CLIENT_OFFSET_X = 0
CLIENT_OFFSET_Y = 0

MINIMAP_REGION = {
    "left": 570,
    "top": 9,
    "width": 146,
    "height": 148
}

def capture_region(region):
    try:
        sct_img = sct_engine.grab(region)
        return np.array(sct_img)[:, :, :3]
    except Exception as e:
        print(f"[ERROR] capture_region failed: {e}")
        return None

def find_color_centers(image_bgr, lower_hsv, upper_hsv):
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    centers = []
    for c in contours:
        area = cv2.contourArea(c)
        if area > 10:
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centers.append((cx, cy))
    return centers

def human_mouse_move(x, y):
    pyautogui.moveTo(x, y, duration=random.uniform(0.1, 0.3), tween=pyautogui.easeInOutQuad)

def click_at(x, y, variation=3):
    rx = x + random.randint(-variation, variation)
    ry = y + random.randint(-variation, variation)
    human_mouse_move(rx, ry)
    time.sleep(random.uniform(0.02, 0.08))
    pyautogui.click()

def reset_aggro():
    print("\n[*] Timer reached! Starting Basic Aggro Reset Route...")
    
    # 1. Click Cyan
    print("    [*] Looking for Cyan marker on Minimap...")
    img = capture_region(MINIMAP_REGION)
    centers = find_color_centers(img, MARKER_CYAN_LOW, MARKER_CYAN_HIGH)
    if centers:
        cx, cy = centers[0]
        click_at(MINIMAP_REGION["left"] + cx, MINIMAP_REGION["top"] + cy, variation=2)
        print("    [*] Clicked Cyan. Waiting 10s to run...")
        time.sleep(10)
    else:
        print("    [!] Could not find Cyan marker! Aborting route.")
        return

    # 2. Click Blue
    print("    [*] Looking for Blue marker on Minimap...")
    img = capture_region(MINIMAP_REGION)
    centers = find_color_centers(img, MARKER_GREEN_LOW, MARKER_GREEN_HIGH)
    if centers:
        cx, cy = centers[0]
        click_at(MINIMAP_REGION["left"] + cx, MINIMAP_REGION["top"] + cy, variation=2)
        print("    [*] Clicked Blue. Waiting 12s to run...")
        time.sleep(12)
    else:
        print("    [!] Could not find Blue marker! Aborting route.")
        return

    # 3. Click Magenta (Home)
    print("    [*] Looking for Magenta marker on Minimap to return home...")
    img = capture_region(MINIMAP_REGION)
    centers = find_color_centers(img, MARKER_MAGENTA_LOW, MARKER_MAGENTA_HIGH)
    if centers:
        cx, cy = centers[0]
        click_at(MINIMAP_REGION["left"] + cx, MINIMAP_REGION["top"] + cy, variation=2)
        print("    [*] Clicked Magenta. Waiting 10s to return...")
        time.sleep(10)
    else:
        print("    [!] Could not find Magenta marker! You might be lost.")
        return
        
    print("[+] Basic Route Complete. Idling in combat...")

def main():
    global is_running, CLIENT_OFFSET_X, CLIENT_OFFSET_Y
    print("========================================")
    print("        BASIC SAND CRAB BOT v1.0        ")
    print("========================================")
    print("This bot blindly runs the Cyan -> Blue -> Magenta route every 10 minutes.")
    print("No crash detection, no login handling, no HP checking.")
    print("Ensure you are in Fixed - Classic layout.")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Calibrate window quickly
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, "RuneLite")
    if not hwnd:
        hwnd = user32.FindWindowW(None, "Old School RuneScape")
    if hwnd:
        child = user32.FindWindowExW(hwnd, 0, "SunAwtCanvas", None)
        if child: hwnd = child
        pt = wintypes.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))
        CLIENT_OFFSET_X = pt.x
        CLIENT_OFFSET_Y = pt.y
        MINIMAP_REGION["left"] += pt.x
        MINIMAP_REGION["top"] += pt.y
        print(f"[*] Window calibrated: Offset ({pt.x}, {pt.y})")
    
    while is_running:
        print("\n[*] Idling in combat for 10 minutes...")
        
        # Sleep for 10 minutes (600 seconds), checking for is_running every 5 seconds
        for _ in range(120):
            if not is_running: break
            time.sleep(5)
            
        if not is_running: break
        
        # Run route
        reset_aggro()
        
    print("\n[!] Basic bot safely stopped.")

if __name__ == '__main__':
    main()
