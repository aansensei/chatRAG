## application/permission

Use cases for access control.

### Files

`validate_access.py` - checks whether a user has a specific right (read/edit/delete) on a document. Considers both the Permission entity and its expiry. Raises an exception if access is denied.
