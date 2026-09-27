import cv2
import os

reader = None
try:
    import easyocr
    # Initialize the EasyOCR reader (it will download models on first run if missing)
    # Using English ('en'). Use gpu=False to ensure it works on all laptops.
    reader = easyocr.Reader(['en'], gpu=False)
except Exception as e:
    print(f"[!] OCR Disabled: PyTorch failed to load on this system. Bot will fallback to visual matching.")

def read_text_from_image(image_cv2):
    """
    Takes an OpenCV BGR image and extracts text using EasyOCR.
    """
    if reader is None:
        return ""
        
    try:
        # EasyOCR handles raw images quite well, but grayscale can speed it up
        gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
        
        # Extract text (detail=0 returns just a list of text strings)
        results = reader.readtext(gray, detail=0)
        
        # Join into a single string
        text = " ".join(results)
        return text.strip()
    except Exception:
        return ""

def find_text_coordinates(image_cv2, target_text):
    """
    Finds the center (x, y) coordinate of a specific text string using OCR.
    """
    if reader is None:
        return None
        
    try:
        gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
        # detail=1 returns bounding boxes along with text
        results = reader.readtext(gray, detail=1)
        
        for (bbox, text, prob) in results:
            if target_text.lower() in text.lower():
                # bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                # tl = top-left, br = bottom-right
                tl = bbox[0]
                br = bbox[2]
                cx = int((tl[0] + br[0]) / 2)
                cy = int((tl[1] + br[1]) / 2)
                return (cx, cy)
    except Exception:
        pass
    return None
