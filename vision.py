import cv2
import numpy as np
import os

reader = None
try:
    import easyocr
    reader = easyocr.Reader(['en'], gpu=False)
except Exception:
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
    Returns (action_type, (x, y)) with calibrated center coordinates for Fixed Classic layout (765x503).
    """
    if image_cv2 is None:
        return None, None
        
    hsv = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2HSV)
    
    # 1. Welcome Screen ("CLICK HERE TO PLAY" Red Button)
    r1 = cv2.inRange(hsv, (0, 70, 50), (12, 255, 255))
    r2 = cv2.inRange(hsv, (168, 70, 50), (180, 255, 255))
    red_mask = cv2.bitwise_or(r1, r2)
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        # Red welcome banner is large in the center area
        if (bw >= 100 and bh >= 20 and area > 1800) or area > 10000:
            if y < 420:
                # The "Click here to play" red button is centered at X=382, Y=330
                return "WELCOME_PLAY", (382, 330)

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
            # Click directly on the centered Try Again button
            return "DISCONNECT_RETRY", (382, 266)

    # 3. Gold / Yellow Login Buttons ("Existing User" / "Play Now" / "PLAYERNAME" Account Box)
    gold_mask = cv2.inRange(hsv, (12, 70, 70), (45, 255, 255))
    g_contours, _ = cv2.findContours(gold_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in g_contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        # Match gold button contours or massive account box banner
        if (bw >= 70 and bh >= 18 and area > 500) or area > 4000:
            if y < 420:
                # In classic fixed mode, the main character card / Play button is horizontally centered at X=382, Y=310
                return "LOGIN_BUTTON", (382, 310)

    return None, None

def find_text_coordinates(image_cv2, target_text):
    """
    Finds the center (x, y) coordinate of a specific text string using OCR or pure CV.
    """
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
            
    action, coords = detect_screen_action(image_cv2)
    if coords is not None:
        return coords
        
    return None
