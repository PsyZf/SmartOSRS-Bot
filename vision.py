import cv2
import numpy as np
import os

_reader = None
_reader_failed = False

def _get_ocr_reader():
    """
    Lazy-loads EasyOCR only when explicitly needed, avoiding blocking bot startup.
    """
    global _reader, _reader_failed
    if _reader_failed:
        return None
    if _reader is not None:
        return _reader
        
    try:
        import easyocr
        _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        return _reader
    except Exception:
        _reader_failed = True
        return None

def read_text_from_image(image_cv2):
    """
    Extracts text using EasyOCR if available, otherwise returns empty string.
    """
    if image_cv2 is None:
        return ""
        
    reader = _get_ocr_reader()
    if reader is None:
        return ""
        
    try:
        gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
        results = reader.readtext(gray, detail=0)
        return " ".join(results).strip()
    except Exception:
        return ""

def detect_screen_action(image_cv2):
    """
    High-accuracy detector for OSRS Login, Welcome, and Disconnect screens.
    Uses EasyOCR exact phrase detection with strict rejection of in-game gameplay screens.
    Returns (action_type, (x, y)) target coordinates relative to canvas.
    """
    if image_cv2 is None:
        return None, None

    # ── Method 1: EasyOCR Precision Phrase Detection ─────────────────────────
    reader = _get_ocr_reader()
    if reader is not None:
        try:
            results = reader.readtext(image_cv2, detail=1)
            extracted = []
            all_text_list = []
            
            for bbox, text, conf in results:
                t_low = text.lower().strip()
                cx = int((bbox[0][0] + bbox[2][0]) / 2)
                cy = int((bbox[0][1] + bbox[2][1]) / 2)
                extracted.append((cx, cy, conf, t_low, bbox))
                all_text_list.append(t_low)
                
            combined = " ".join(all_text_list)

            # 1. Welcome Screen ("Welcome to RuneScape" / "Click here to play" / "Play Now")
            is_welcome = (
                "welcome to runescape" in combined or
                "welcome to" in combined or
                "click here to play" in combined or
                "click to play" in combined or
                ("school" in combined and "world" in combined)
            )
            if is_welcome:
                for cx, cy, conf, text, bbox in extracted:
                    if 180 <= cx <= 585 and 150 <= cy <= 420:
                        if any(k in text for k in ["play", "click", "now", "here"]):
                            return "WELCOME_PLAY", (cx, cy)
                return "WELCOME_PLAY", (382, 235)

            # 2. Disconnect / Retry Screen
            is_disconnect = (
                "try again" in combined or
                "connection lost" in combined or
                "attempting to re-establish" in combined or
                "disconnected" in combined or
                "error connecting to server" in combined
            )
            if is_disconnect:
                for cx, cy, conf, text, bbox in extracted:
                    if 180 <= cx <= 585 and 150 <= cy <= 420:
                        if any(k in text for k in ["try", "again", "retry"]):
                            return "DISCONNECT_RETRY", (cx, cy)
                return "DISCONNECT_RETRY", (382, 275)

            # 3. Login Screen ("Existing User" / "Enter your username")
            is_login = (
                "existing user" in combined or
                "new user" in combined or
                "enter your username" in combined or
                "enter username" in combined or
                "invalid credentials" in combined or
                ("runescape" in combined and "password" in combined)
            )
            if is_login:
                for cx, cy, conf, text, bbox in extracted:
                    if 180 <= cx <= 585 and 150 <= cy <= 420:
                        if any(k in text for k in ["existing", "user", "login"]):
                            return "LOGIN_BUTTON", (cx, cy)
                return "LOGIN_BUTTON", (382, 250)

            # If none of the explicit screen phrases matched, this is an in-game screen or other UI
            return None, None

        except Exception:
            pass

    # ── Method 2: Pure CV Color & Contour Fallback (Restricted to Center Modals) ────
    hsv = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2HSV)
    
    # Red Welcome Screen Button ("CLICK HERE TO PLAY") - strictly in center box
    center_roi_red = hsv[250:400, 220:545]
    r1 = cv2.inRange(center_roi_red, (0, 90, 60), (10, 255, 255))
    r2 = cv2.inRange(center_roi_red, (170, 90, 60), (180, 255, 255))
    red_mask = cv2.bitwise_or(r1, r2)
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        if bw >= 140 and bh >= 25 and area > 2500 and (bw / float(max(1, bh))) > 2.2:
            return "WELCOME_PLAY", (220 + x + bw // 2, 250 + y + bh // 2)

    return None, None

def find_text_coordinates(image_cv2, target_text):
    """
    Finds the center (x, y) coordinate of a specific text string using OCR or pure CV.
    """
    action, coords = detect_screen_action(image_cv2)
    if coords is not None:
        return coords
        
    reader = _get_ocr_reader()
    if reader is not None and image_cv2 is not None:
        try:
            gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
            results = reader.readtext(gray, detail=1)
            for (bbox, text, prob) in results:
                if target_text.lower() in text.lower():
                    tl = bbox[0]
                    br = bbox[2]
                    cx = int((tl[0] + br[0]) / 2)
                    cy = int((tl[1] + br[1]) / 2)
                    return (cx, cy)
        except Exception:
            pass
            
    return None
