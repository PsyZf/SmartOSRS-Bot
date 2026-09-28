import cv2
import numpy as np
import os

reader = None
try:
    import easyocr
    reader = easyocr.Reader(['en'], gpu=False)
except Exception:
    # PyTorch/EasyOCR fallback handled automatically by pure CV
    pass

def read_text_from_image(image_cv2):
    """
    Extracts text using EasyOCR if available, otherwise returns empty.
    """
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
    Pure OpenCV high-speed detector for OSRS Login, Welcome, and Disconnect screens.
    Returns (action_type, (x, y)) where (x, y) is the optimal click target relative to canvas.
    """
    if image_cv2 is None:
        return None, None
        
    hsv = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2HSV)
    
    # 1. Welcome Screen ("CLICK HERE TO PLAY" Red Button)
    r1 = cv2.inRange(hsv, (0, 70, 50), (12, 255, 255))
    r2 = cv2.inRange(hsv, (168, 70, 50), (180, 255, 255))
    red_mask = cv2.bitwise_or(r1, r2)
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_red_box = None
    min_dist_to_center = float('inf')
    
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        # Red button is large and located in center screen (X: 180-580, Y: 180-420)
        if bw >= 100 and bh >= 20 and area > 1800:
            cx = x + bw // 2
            cy = y + bh // 2
            dist = (cx - 382)**2 + (cy - 300)**2
            if dist < min_dist_to_center:
                min_dist_to_center = dist
                best_red_box = (cx, cy)
                
    if best_red_box is not None:
        return "WELCOME_PLAY", best_red_box

    # 2. Disconnect / Try Again Popup (Dialog with white text at Y: 220-280)
    center_roi = image_cv2[150:350, 200:565]
    white_text = cv2.inRange(center_roi, (180, 180, 180), (255, 255, 255))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 3))
    grouped = cv2.dilate(white_text, kernel, iterations=1)
    t_contours, _ = cv2.findContours(grouped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for tc in t_contours:
        tx, ty, tw, th = cv2.boundingRect(tc)
        # "Try again" text at dialog bottom
        if 40 <= tw <= 190 and 8 <= th <= 25 and 85 <= ty <= 145:
            abs_cx = 200 + tx + tw // 2
            abs_cy = 150 + ty + th // 2
            return "DISCONNECT_RETRY", (abs_cx, abs_cy)

    # 3. Gold / Yellow Login Buttons ("Existing User" / "Play Now")
    gold_mask = cv2.inRange(hsv, (12, 70, 70), (45, 255, 255))
    g_contours, _ = cv2.findContours(gold_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in g_contours:
        x, y, bw, bh = cv2.boundingRect(c)
        if bw >= 90 and bh >= 18 and cv2.contourArea(c) > 1000:
            if 150 <= y <= 380: # Center login area
                return "LOGIN_BUTTON", (x + bw // 2, y + bh // 2)

    return None, None

def find_text_coordinates(image_cv2, target_text):
    """
    Finds the center (x, y) coordinate of a specific text string using OCR or pure CV.
    """
    # 1. Try EasyOCR if available
    if reader is not None:
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
            
    # 2. Pure CV Fallback for common buttons
    action, coords = detect_screen_action(image_cv2)
    if coords is not None:
        return coords
        
    return None
