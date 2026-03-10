import pytesseract
from PIL import Image
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure Tesseract path if set in .env
tesseract_cmd = os.getenv("TESSERACT_CMD")
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

def extract_text_from_image(image_path: str | Path) -> str:
    """
    Extracts text from the given image path using Tesseract OCR.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return ""

if __name__ == "__main__":
    # Assuming test_capture.png was created by screencapture.py
    test_path = "test_capture.png"
    if Path(test_path).exists():
        text = extract_text_from_image(test_path)
        print(f"Extracted Text:\n{text[:200]}...")
    else:
        print(f"File {test_path} not found. Run screencapture.py first.")
