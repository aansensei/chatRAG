## infrastructure/ocr/paddleocr

PaddleOCR implementation.

### Files

`ocr.py` - nhận image path (hoặc bytes), chạy PaddleOCR, trả về text đã extract. Được gọi bởi `workers/ocr_worker.py` trên từng trang scan.
