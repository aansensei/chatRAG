## presentation/middleware

FastAPI middleware chạy trước mỗi request.

### Files

`auth.py` - validate JWT token từ Authorization header, decode và populate `request.state.user`. Trả 401 nếu token không hợp lệ hoặc hết hạn.

`permission.py` - sau khi auth, kiểm tra user có quyền trên resource cụ thể không (document-level). Gọi validate_access use case.

`rate_limit.py` - giới hạn số request per IP hoặc per user trong khoảng thời gian nhất định, chống abuse.
