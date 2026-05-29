## application/permission

Use cases kiểm soát quyền truy cập.

### Files

`validate_access.py` - kiểm tra user có quyền thao tác cụ thể (read/edit/delete) trên một document không. Xem xét cả Permission entity lẫn expiry. Raise exception nếu không có quyền.
