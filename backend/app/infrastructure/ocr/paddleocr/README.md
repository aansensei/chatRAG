## infrastructure/ocr/paddleocr

PaddleOCR implementation.

### Files

`ocr.py` - receives an image path (or bytes), runs PaddleOCR, returns the extracted text. Called by `workers/ocr_worker.py` on each scanned page.
