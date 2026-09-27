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
