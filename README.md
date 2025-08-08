# Quote PDF Parser (OCR to JSON)

Extracts **line items** (description, quantity, unit price, cost) from a one-page PDF of a quote using EasyOCR + PyMuPDF, then writes a structured JSON summary.

---

## (Briefly) What this script does:
- Renders the 1st page of your PDF to a png
- Runs OCR to find table headers like “Description”, “Qty”, “Unit Price”, “Amount/Total”
- Scans down each column to collect line items
- Normalizes numbers and totals them
- Saves to `Output/<filename>.json`

---

## Usage

1. Run the main script (main.py)
2. Upload the pdf of the quote to Upload folder
3. Type in the name of the pdf file (including the .pdf file extension) into the terminal prompt
4. Wait for easyocr to process the file
5. Find the corresponding output .json file in Output folder

---

## Requirements

- Python 3.9+ (recommended)
- Packages:
  - `opencv-python` (cv2)
  - `easyocr` (requires PyTorch)
  - `matplotlib`
  - `pymupdf`
- No external OCR engines needed (EasyOCR is bundled)

---

### Install in a fresh virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install --upgrade pip
pip install opencv-python easyocr matplotlib pymupdf torch torchvision --index-url https://download.pytorch.org/whl/cpu
