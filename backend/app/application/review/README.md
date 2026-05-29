## application/review

Use cases cho human review workflow. Áp dụng với document có SensitivityLevel >= CONFIDENTIAL.

### Files

`get_pending.py` - lấy danh sách Review đang ở trạng thái PENDING, dùng cho reviewer dashboard.

`approve_review.py` - reviewer duyệt document: cập nhật Review sang APPROVED, chuyển Document sang READY, publish `ReviewApproved` event.

`reject_review.py` - reviewer từ chối: cập nhật Review sang REJECTED, document không được deploy vào search index.
