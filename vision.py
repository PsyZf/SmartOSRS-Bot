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
    Uses EasyOCR text-coordinate detection with pure CV color/shape fallback.
    Returns (action_type, (x, y)) target coordinates relative to canvas.
    """
    if image_cv2 is None:
        return None, None

    # ── Method 1: EasyOCR Precision Text Targeting ───────────────────────────
    reader = _get_ocr_reader()
    if reader is not None:
        try:
            results = reader.readtext(image_cv2, detail=1)
            play_candidates = []
            retry_candidates = []
            login_candidates = []

            for bbox, text, conf in results:
                t_low = text.lower().strip()
                words = t_low.split()
                cx = int((bbox[0][0] + bbox[2][0]) / 2)
                cy = int((bbox[0][1] + bbox[2][1]) / 2)

                # Focus on the game canvas area
                if 120 <= cx <= 645 and 100 <= cy <= 450:
                    # Match "Play", "Play Now", "Click here to play" (exact words)
                    if "play" in words or "now" in words or "click" in words:
                        play_candidates.append((cx, cy, conf, text))
                    # Match "Try again", "Retry", "Disconnected"
                    elif "try" in words or "again" in words or "retry" in words or "disconnected" in words:
                        retry_candidates.append((cx, cy, conf, text))
                    # Match "Existing User", "Login"
                    elif "existing" in words or "login" in words or "user" in words:
                        login_candidates.append((cx, cy, conf, text))

            # Prioritize Play buttons if found
            if play_candidates:
                best = max(play_candidates, key=lambda x: x[2])
                return "WELCOME_PLAY", (best[0], best[1])

            # Then Disconnect / Retry buttons
            if retry_candidates:
                best = max(retry_candidates, key=lambda x: x[2])
                return "DISCONNECT_RETRY", (best[0], best[1])

            # Then Login buttons
            if login_candidates:
                best = max(login_candidates, key=lambda x: x[2])
                return "LOGIN_BUTTON", (best[0], best[1])
        except Exception:
            pass

    # ── Method 2: Pure CV Color & Contour Fallback ───────────────────────────
    hsv = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2HSV)
    
    # Red Welcome Screen Button ("CLICK HERE TO PLAY")
    r1 = cv2.inRange(hsv, (0, 70, 50), (12, 255, 255))
    r2 = cv2.inRange(hsv, (168, 70, 50), (180, 255, 255))
    red_mask = cv2.bitwise_or(r1, r2)
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        if (bw >= 100 and bh >= 20 and area > 1800) or area > 10000:
            if y < 420:
                return "WELCOME_PLAY", (x + bw // 2, y + bh // 2)

    # Gold Login Button ("Existing User" / "Play Now" / Character Box)
    gold_mask = cv2.inRange(hsv, (12, 70, 70), (45, 255, 255))
    g_contours, _ = cv2.findContours(gold_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in g_contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        if (bw >= 70 and bh >= 18 and area > 500) or area > 4000:
            if y < 420:
                return "LOGIN_BUTTON", (382, 235)

    # Disconnect / Retry Dialog Box (White text clusters)
    center_roi = image_cv2[150:350, 200:565]
    white_text = cv2.inRange(center_roi, (180, 180, 180), (255, 255, 255))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 3))
    grouped = cv2.dilate(white_text, kernel, iterations=1)
    t_contours, _ = cv2.findContours(grouped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for tc in t_contours:
        tx, ty, tw, th = cv2.boundingRect(tc)
        if 40 <= tw <= 190 and 8 <= th <= 25 and 85 <= ty <= 145:
            return "DISCONNECT_RETRY", (200 + tx + tw // 2, 150 + ty + th // 2)

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
